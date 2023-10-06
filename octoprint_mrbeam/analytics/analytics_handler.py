# coding=utf-8

import collections
import fileinput
import json
import logging
import os.path
import sys
import time
import uuid
from threading import Thread, Timer, Lock

import re
from octoprint.events import Events as OctoPrintEvents

from octoprint_mrbeam.analytics.analytics_keys import AnalyticsKeys
from octoprint_mrbeam.analytics.cpu import Cpu
from octoprint_mrbeam.analytics.value_collector import ValueCollector
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.util import dict_merge
from octoprint_mrbeam.util.log import json_serialisor
from octoprint_mrbeam.util.uptime import get_uptime
from octoprint_mrbeam.analytics.timer_handler import TimerHandler
from octoprint_mrbeam.analytics.uploader import AnalyticsFileUploader

# singleton
_instance = None


def analyticsHandler(plugin):
    global _instance
    if _instance is None:
        _instance = AnalyticsHandler(plugin)
    return _instance


class AnalyticsHandler(object):
    QUEUE_MAXSIZE = 1000
    UNKNOWN_VALUE = "unknown"
    ANALYTICS_LOG_VERSION = (
        29  # bumped for SW-1157 add laser head max temperature and summer month offset
    )

    def __init__(self, plugin):
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._settings = plugin._settings
        self._analytics_lock = Lock()

        self._snr = plugin.getSerialNum()
        self._plugin_version = plugin.get_plugin_version()

        self._timer_handler = TimerHandler(plugin, self, self._analytics_lock)
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.analyticshandler")

        # Mr Beam specific data
        self._analytics_enabled = self._settings.get(["analyticsEnabled"])
        self._support_mode = plugin.support_mode
        self._no_choice_made = True if self._analytics_enabled is None else False

        self.analytics_folder = os.path.join(
            self._settings.getBaseFolder("base"),
            self._settings.get(["analytics", "folder"]),
        )
        if not os.path.isdir(self.analytics_folder):
            os.makedirs(self.analytics_folder)
        self.analytics_file = os.path.join(
            self.analytics_folder, self._settings.get(["analytics", "filename"])
        )

        # Session-specific data
        self._session_id = "{uuid}@{serial}".format(
            serial=self._snr, uuid=uuid.uuid4().hex
        )

        # Job-specific data
        self._current_job_id = None
        self._current_job_time_estimation_v1 = -1
        self.current_job_time_estimation_v2 = -1
        self._current_job_final_status = None
        self._current_job_compressor_data = None
        self._current_dust_collector = None
        self._current_intensity_collector = None
        self._current_lasertemp_collector = None
        self._current_cpu_data = None

        self.event_waiting_for_terminal_dump = None

        self._dust_manager = None
        self._compressor_handler = None
        self._laserhead_handler = None

        self._logger.info(
            "Analytics analyticsEnabled: %s, sid: %s",
            self.is_analytics_enabled(),
            self._session_id,
        )

        # Subscribe to startup and mrb_plugin_initialize --> The rest go on _on_mrbeam_plugin_initialized
        self._event_bus.subscribe(OctoPrintEvents.STARTUP, self._event_startup)
        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

        # Initialize queue for analytics data and queue-to-file writer
        self._analytics_queue = collections.deque(maxlen=self.QUEUE_MAXSIZE)

        # Activate analytics
        if self.is_analytics_enabled():
            self._activate_analytics()

    def _on_mrbeam_plugin_initialized(self, event, payload):
        _ = event
        _ = payload
        self._laserhead_handler = self._plugin.laserhead_handler
        self._dust_manager = self._plugin.dust_manager
        self._temperature_manager = self._plugin.temperature_manager
        self._compressor_handler = self._plugin.compressor_handler

        self._subscribe()

        # Upload any previous analytics, unless the user didn't make a choice yet
        if not self._no_choice_made:
            AnalyticsFileUploader.upload_now(self._plugin, self._analytics_lock)

        # Start timers for async analytics
        self._timer_handler.start_timers()

    def _activate_analytics(self):
        # Restart queue if the analytics were disabled before
        if not self._no_choice_made:
            self._analytics_queue = collections.deque(maxlen=self.QUEUE_MAXSIZE)
        else:
            self._no_choice_made = False

        # Start writer thread
        analytics_writer = Thread(target=self._write_queue_to_analytics_file)
        analytics_writer.daemon = True
        analytics_writer.start()

    def is_analytics_enabled(self):
        return self._analytics_enabled and not self._support_mode

    # -------- EXTERNALLY CALLED METHODS -------------------------------------------------------------------------------
    def upload(self, delay=5.0):
        # We have to wait until the last line is written before we upload
        Timer(
            interval=delay,
            function=AnalyticsFileUploader.upload_now,
            args=[self._plugin, self._analytics_lock],
        ).start()

    # INIT
    def analytics_user_permission_change(
        self, analytics_enabled, header_extension=None
    ):
        try:
            self._logger.info(
                "analytics user permission change: analyticsEnabled=%s",
                analytics_enabled,
            )

            if analytics_enabled:
                self._analytics_enabled = True
                self._settings.set_boolean(["analyticsEnabled"], True)
                self._activate_analytics()
                self._add_device_event(
                    AnalyticsKeys.Device.Event.ANALYTICS_ENABLED,
                    payload=dict(enabled=True),
                    header_extension=header_extension,
                )
            else:
                # can not log this since the user just disagreed
                # self._add_device_event(ak.Device.Event.ANALYTICS_ENABLED, payload=dict(enabled=False))
                self._analytics_enabled = False
                self._timer_handler.cancel_timers()
                self._settings.set_boolean(["analyticsEnabled"], False)
        except Exception as e:
            self._logger.exception(
                "Exception during analytics_user_permission_change: {}".format(e)
            )

    def add_ui_render_call_event(
        self, host, remote_ip, referrer, language, user_agent, header_extension=None
    ):
        try:
            call = {
                AnalyticsKeys.Connectivity.Call.HOST: host,
                AnalyticsKeys.Connectivity.Call.REMOTE_IP: remote_ip,
                AnalyticsKeys.Connectivity.Call.REFERRER: referrer,
                AnalyticsKeys.Connectivity.Call.LANGUAGE: language,
                AnalyticsKeys.Connectivity.Call.USER_AGENT: user_agent,
            }

            self._add_connectivity_event(
                AnalyticsKeys.Connectivity.Event.UI_RENDER_CALL,
                payload=call,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_ui_render_call_event: {}".format(e)
            )

    def add_client_opened_event(self, remote_ip, header_extension=None):
        try:
            data = {
                AnalyticsKeys.Connectivity.Call.REMOTE_IP: remote_ip,
            }

            self._add_connectivity_event(
                AnalyticsKeys.Connectivity.Event.CLIENT_OPENED,
                payload=data,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_client_opened_event: {}".format(e)
            )

    def add_frontend_event(self, event, payload=None, header_extension=None):
        try:
            self._add_frontend_event(
                event, payload=payload, header_extension=header_extension
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_frontend_event: {}".format(e), analytics=True
            )

    # TIMER_HANDLER
    def add_mrbeam_usage(self, usage_data, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.MRBEAM_USAGE,
                payload=usage_data,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception("Exception during add_mrbeam_usage: {}".format(e))

    def add_http_self_check(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.HTTP_SELF_CHECK,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception("Exception during add_http_self_check: {}".format(e))

    def add_internet_connection(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.INTERNET_CONNECTION,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_internet_connection: {}".format(e)
            )

    def add_ip_addresses(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.IPS,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception("Exception during add_ip_addresses: {}".format(e))

    def add_disk_space(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.DISK_SPACE,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception("Exception during add_disk_space: {}".format(e))

    def add_software_versions(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.SOFTWARE_VERSIONS,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_software_versions: {}".format(e)
            )

    def add_num_files(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.NUM_FILES,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception("Exception during add_num_files: {}".format(e))

    def add_analytics_file_crop(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Log.Event.ANALYTICS_FILE_CROP,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_analytics_file_crop: {}".format(e)
            )

    # MRB_LOGGER
    def add_logger_event(
        self, event_details, wait_for_terminal_dump, header_extension=None
    ):
        try:
            filename = event_details["caller"].filename.replace(
                __package_path__ + "/", ""
            )

            if event_details["level"] in logging._levelNames:
                event_details["level"] = logging._levelNames[event_details["level"]]

            if event_details["exception_str"]:
                event_details["level"] = AnalyticsKeys.Log.Level.EXCEPTION

            caller = event_details.pop("caller", None)
            if caller:
                event_details.update(
                    {
                        AnalyticsKeys.Log.Caller.HASH: hash(
                            "{}{}{}".format(
                                filename, caller.lineno, self._plugin_version
                            )
                        ),
                        AnalyticsKeys.Log.Caller.FILE: filename,
                        AnalyticsKeys.Log.Caller.LINE: caller.lineno,
                        AnalyticsKeys.Log.Caller.FUNCTION: caller.function,
                        # code_context: caller.code_context[0].strip()
                    }
                )

            if (
                wait_for_terminal_dump
            ):  # If it is e.g. GRBL error, we will have to wait some time for the whole dump
                self.event_waiting_for_terminal_dump = dict(event_details)
            else:
                self._add_log_event(
                    AnalyticsKeys.Log.Event.EVENT_LOG,
                    payload=event_details,
                    analytics=False,
                    header_extension=header_extension,
                )
        except Exception as e:
            self._logger.exception("Exception during add_logger_event: {}".format(e))

    def log_terminal_dump(
        self, dump, header_extension=None
    ):  # Will be used with e.g. GRBL errors
        try:
            if self.event_waiting_for_terminal_dump is not None:
                payload = dict(self.event_waiting_for_terminal_dump)
                payload[AnalyticsKeys.Log.TERMINAL_DUMP] = dump
                self._add_log_event(
                    AnalyticsKeys.Log.Event.EVENT_LOG,
                    payload=payload,
                    analytics=False,
                    header_extension=header_extension,
                )
                self.event_waiting_for_terminal_dump = None
            else:
                self._logger.warn(
                    "log_terminal_dump() called but no foregoing event tracked. self.event_waiting_for_terminal_dump is "
                    "None. ignoring this dump."
                )
        except Exception as e:
            self._logger.exception("Exception during log_terminal_dump: {}".format(e))

    # LASERHEAD_HANDLER
    def add_laserhead_info(self, header_extension=None):
        try:
            laser_head = self._laserhead_handler.get_current_used_lh_data()
            power_calibration = self._laserhead_handler.get_current_used_lh_power()
            settings = self._laserhead_handler.get_correction_settings()
            laserhead_info = {
                AnalyticsKeys.Device.LaserHead.POWER_65: power_calibration.get(
                    "power_65", None
                ),
                AnalyticsKeys.Device.LaserHead.POWER_75: power_calibration.get(
                    "power_75", None
                ),
                AnalyticsKeys.Device.LaserHead.POWER_85: power_calibration.get(
                    "power_85", None
                ),
                AnalyticsKeys.Device.LaserHead.TARGET_POWER: power_calibration.get(
                    "target_power", None
                ),
                AnalyticsKeys.Device.LaserHead.CORRECTION_FACTOR: laser_head["info"][
                    "correction_factor"
                ],
                AnalyticsKeys.Device.LaserHead.CORRECTION_ENABLED: settings[
                    "correction_enabled"
                ],
                AnalyticsKeys.Device.LaserHead.CORRECTION_OVERRIDE: settings[
                    "correction_factor_override"
                ],
            }
            self._add_device_event(
                AnalyticsKeys.Device.Event.LASERHEAD_INFO,
                payload=laserhead_info,
                header_extension=header_extension,
            )

        except Exception as e:
            self._logger.exception("Exception during add_laserhead_info: {}".format(e))

    def add_laserhead_changed(
        self,
        last_used_serial,
        last_used_model_id,
        new_serial,
        new_model_id,
        header_extension=None,
    ):
        try:
            laser_head = self._laserhead_handler.get_current_used_lh_data()
            power_calibration = self._laserhead_handler.get_current_used_lh_power()
            settings = self._laserhead_handler.get_correction_settings()
            laserhead_info = {
                AnalyticsKeys.Device.LaserHead.LAST_USED_SERIAL: last_used_serial,
                AnalyticsKeys.Device.LaserHead.LAST_USED_HEAD_MODEL_ID: last_used_model_id,
                AnalyticsKeys.Device.LaserHead.SERIAL: new_serial,
                AnalyticsKeys.Device.LaserHead.HEAD_MODEL_ID: new_model_id,
                AnalyticsKeys.Device.LaserHead.POWER_65: power_calibration.get(
                    "power_65", None
                ),
                AnalyticsKeys.Device.LaserHead.POWER_75: power_calibration.get(
                    "power_75", None
                ),
                AnalyticsKeys.Device.LaserHead.POWER_85: power_calibration.get(
                    "power_85", None
                ),
                AnalyticsKeys.Device.LaserHead.TARGET_POWER: power_calibration.get(
                    "target_power", None
                ),
                AnalyticsKeys.Device.LaserHead.CORRECTION_FACTOR: laser_head["info"][
                    "correction_factor"
                ],
                AnalyticsKeys.Device.LaserHead.CORRECTION_ENABLED: settings[
                    "correction_enabled"
                ],
                AnalyticsKeys.Device.LaserHead.CORRECTION_OVERRIDE: settings[
                    "correction_factor_override"
                ],
            }
            self._add_device_event(
                AnalyticsKeys.Device.Event.LASERHEAD_CHANGED,
                payload=laserhead_info,
                header_extension=header_extension,
            )

        except Exception as e:
            self._logger.exception(
                "Exception during add_laserhead_change: {}".format(e)
            )

    # LID_HANDLER
    def add_camera_session_details(self, session_details, header_extension=None):
        try:
            self._add_log_event(
                AnalyticsKeys.Log.Event.CAMERA,
                payload=session_details,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_camera_session: {}".format(e), analytics=True
            )

    def add_camera_image(self, payload, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.CAMERA_IMAGE,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_camera_image: {}".format(e), analytics=True
            )

    # ACC_WATCH_DOG
    def add_cpu_log(self, temp, throttle_alerts, header_extension=None):
        try:
            cpu_data = {
                AnalyticsKeys.Log.Cpu.TEMP: temp,
                AnalyticsKeys.Log.Cpu.THROTTLE_ALERTS: throttle_alerts,
            }
            self._add_log_event(
                AnalyticsKeys.Log.Event.CPU,
                payload=cpu_data,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_cpu_log: {}".format(e), analytics=True
            )

    # CONVERTER
    def add_material_details(self, material_details, header_extension=None):
        try:
            self._add_job_event(
                AnalyticsKeys.Job.Event.Slicing.MATERIAL,
                payload=material_details,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_material_details: {}".format(e)
            )

    def add_engraving_parameters(self, eng_params, header_extension=None):
        try:
            self._add_job_event(
                AnalyticsKeys.Job.Event.Slicing.CONV_ENGRAVE,
                payload=eng_params,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_engraving_parameters: {}".format(e)
            )

    def add_cutting_parameters(self, cut_details, header_extension=None):
        try:
            self._add_job_event(
                AnalyticsKeys.Job.Event.Slicing.CONV_CUT,
                payload=cut_details,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_cutting_parameters: {}".format(e)
            )

    def add_design_file_details(self, design_file, header_extension=None):
        try:
            self._add_job_event(
                AnalyticsKeys.Job.Event.Slicing.DESIGN_FILE,
                payload=design_file,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_design_file_details: {}".format(e)
            )

    # USAGE
    def add_job_ntp_sync_details(self, sync_details, header_extension=None):
        try:
            self._add_job_event(
                AnalyticsKeys.Job.Event.NTP_SYNC,
                payload=sync_details,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_job_ntp_sync_details: {}".format(e)
            )

    # COMM_ACC2
    def add_grbl_flash_event(
        self, from_version, to_version, successful, err=None, header_extension=None
    ):
        try:
            flashing = {
                AnalyticsKeys.Device.Grbl.FROM_VERSION: from_version,
                AnalyticsKeys.Device.Grbl.TO_VERSION: to_version,
                AnalyticsKeys.Device.SUCCESS: successful,
                AnalyticsKeys.Device.ERROR: err,
            }

            self._add_device_event(
                AnalyticsKeys.Device.Event.FLASH_GRBL,
                payload=flashing,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_grbl_flash_event: {}".format(e)
            )

    # SOFTWARE_UPDATE_INFORMATION
    def add_software_channel_switch_event(
        self, old_channel, new_channel, header_extension=None
    ):
        try:
            channels = {
                AnalyticsKeys.Device.SoftwareChannel.OLD: old_channel,
                AnalyticsKeys.Device.SoftwareChannel.NEW: new_channel,
            }

            self._add_device_event(
                AnalyticsKeys.Device.Event.SW_CHANNEL_SWITCH,
                payload=channels,
                header_extension=header_extension,
            )

        except Exception as e:
            self._logger.exception(
                "Exception during add_software_channel_switch_event: {}".format(e)
            )

    # LED_EVENTS
    def add_connections_state(self, connections, header_extension=None):
        try:
            self._add_connectivity_event(
                AnalyticsKeys.Connectivity.Event.CONNECTIONS_STATE,
                payload=connections,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_connections_state: {}".format(e)
            )

    # DUST_MANAGER
    def add_fan_rpm_test(self, data, header_extension=None):
        try:
            # The fan_rpm_test might finish after the job is done, in that case it isn't interesting for us
            if self._current_job_id:
                self._add_job_event(
                    AnalyticsKeys.Job.Event.Print.FAN_RPM_TEST,
                    payload=data,
                    header_extension=header_extension,
                )
        except Exception as e:
            self._logger.exception("Exception during add_fan_rpm_test: {}".format(e))

    # OS_HEALTH_CARE
    def add_os_health_log(self, data, header_extension=None):
        try:
            self._add_log_event(
                AnalyticsKeys.Log.Event.OS_HEALTH,
                payload=data,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_os_health_log: {}".format(e), analytics=True
            )

    # COMPRESSOR_HANDLER
    def add_compressor_data(self, data, header_extension=None):
        try:
            self._add_device_event(
                AnalyticsKeys.Device.Event.COMPRESSOR,
                payload=data,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_compressor_static_data: {}".format(e)
            )

    # High Temp Warning
    def add_high_temp_warning_state_transition(
        self, event, state_before, state_after, feature_disabled, header_extension=None
    ):
        """
        Add a high temp warning state transition event to the analytics queue
        Args:
            event: event that triggered the transition
            state_before: state before the transition
            state_after: state after the transition
            feature_disabled: if the feature is disabled
            header_extension:  additional header information

        Returns:
            None
        """
        try:
            if header_extension is None:
                header_extension = dict()

            header_extension.update(
                {
                    AnalyticsKeys.Header.FEATURE_ID: "SW-991",
                }
            )
            payload = {
                AnalyticsKeys.HighTemperatureWarning.State.STATE_BEFORE: state_before,
                AnalyticsKeys.HighTemperatureWarning.State.STATE_AFTER: state_after,
                AnalyticsKeys.HighTemperatureWarning.State.EVENT: event,
                AnalyticsKeys.HighTemperatureWarning.State.FEATURE_DISABLED: feature_disabled,
            }
            self._add_device_event(
                AnalyticsKeys.HighTemperatureWarning.Event.STATE_TRANSITION,
                payload=payload,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during add_high_temp_warning_state_transition: {}".format(e)
            )

    # -------- OCTOPRINT AND MR BEAM EVENTS ----------------------------------------------------------------------------
    def _subscribe(self):
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_STARTED, self._event_print_started
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_PAUSED, self._event_print_paused
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_RESUMED, self._event_print_resumed
        )
        self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_print_done)
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_FAILED, self._event_print_failed
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_CANCELLED, self._event_print_cancelled
        )
        self._event_bus.subscribe(
            OctoPrintEvents.SLICING_STARTED, self._event_slicing_started
        )
        self._event_bus.subscribe(
            OctoPrintEvents.SLICING_DONE, self._event_slicing_done
        )
        self._event_bus.subscribe(
            OctoPrintEvents.SLICING_CANCELLED, self._event_slicing_cancelled
        )
        self._event_bus.subscribe(
            OctoPrintEvents.SLICING_FAILED, self._event_slicing_failed
        )
        self._event_bus.subscribe(
            MrBeamEvents.READY_TO_LASER_CANCELED, self._event_laser_job_finished
        )
        self._event_bus.subscribe(
            MrBeamEvents.PRINT_PROGRESS, self._event_print_progress
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_PAUSE, self._event_laser_cooling_pause
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_RESUME, self._event_laser_cooling_resume
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_JOB_DONE, self._event_laser_job_finished
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_JOB_CANCELLED, self._event_laser_job_finished
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_JOB_FAILED, self._event_laser_job_finished
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_JOB_ABORTED, self._event_laser_job_finished
        )
        self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._event_shutdown)
        self._event_bus.subscribe(
            MrBeamEvents.ANALYTICS_DATA, self._add_other_plugin_data
        )
        self._event_bus.subscribe(
            MrBeamEvents.JOB_TIME_ESTIMATED, self._event_job_time_estimated
        )
        self._event_bus.subscribe(
            MrBeamEvents.PRINT_ABORTED, self._on_event_print_aborted
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_TO_SLOW,
            self._on_event_laser_cooling_to_slow,
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_RE_TRIGGER_FAN,
            self._on_event_laser_cooling_re_trigger_fan,
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_HIGH_TEMPERATURE,
            self._on_event_laser_high_temperature,
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_SHOW,
            self._on_event_high_temperature_shown,
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW,
            self._on_event_high_temperature_shown,
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED,
            self._on_event_high_temperature_dismissed,
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED,
            self._on_event_high_temperature_dismissed,
        )

    def _event_startup(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        # Here the MrBeamPlugin is not fully initialized yet, so we have to access this data direct from the plugin
        payload = {
            AnalyticsKeys.Device.Usage.USERS: len(self._plugin._user_manager._users),
        }
        self._add_device_event(
            AnalyticsKeys.Device.Event.STARTUP,
            payload=payload,
            header_extension=header_extension,
        )

    def _event_shutdown(self, event, payload, header_extension=None):
        response_payload = {
            AnalyticsKeys.Device.Cpu.THROTTLE_ALERTS: Cpu(
                state="shutdown", repeat=False
            ).get_cpu_throttle_warnings(),
        }
        self._add_device_event(
            AnalyticsKeys.Device.Event.SHUTDOWN,
            payload=response_payload,
            header_extension=header_extension,
        )

    def _event_slicing_started(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        self._init_new_job()
        self._add_job_event(
            AnalyticsKeys.Job.Event.Slicing.STARTED, header_extension=header_extension
        )
        self._current_cpu_data = Cpu(state="slicing", repeat=False)

    def _event_slicing_done(self, event, payload, header_extension=None):
        _ = event
        if self._current_cpu_data:
            self._current_cpu_data.record_cpu_data()
            self._add_cpu_data(dur=payload.get("time", 0.0))
        self._current_job_final_status = "Sliced"

        payload = {
            AnalyticsKeys.Job.Duration.CURRENT: int(round(payload.get("time", 0.0))),
        }
        self._add_job_event(
            AnalyticsKeys.Job.Event.Slicing.DONE,
            payload=payload,
            header_extension=header_extension,
        )

    def _event_slicing_failed(self, event, payload, header_extension=None):
        _ = event
        _ = header_extension
        self._add_job_event(
            AnalyticsKeys.Job.Event.Slicing.FAILED,
            payload={AnalyticsKeys.Job.ERROR: payload["reason"]},
            header_extension=header_extension,
        )

    def _event_slicing_cancelled(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        self._add_job_event(
            AnalyticsKeys.Job.Event.Slicing.CANCELLED, header_extension=header_extension
        )

    def _add_cpu_data(self, dur=None, header_extension=None):
        if self._current_cpu_data:
            payload = self._current_cpu_data.get_cpu_data()
            payload["dur"] = dur
            self._add_job_event(
                AnalyticsKeys.Job.Event.CPU,
                payload=payload,
                header_extension=header_extension,
            )

    def _event_print_started(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        # If there's no job_id, it may be a gcode file (no slicing), so we have to start the job here
        if not self._current_job_id:
            self._init_new_job()
        self._current_cpu_data = Cpu(state="laser", repeat=True)
        self._init_collectors()
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.STARTED, header_extension=header_extension
        )

    def _event_print_progress(self, event, payload, header_extension=None):
        _ = event
        laser_temp = None
        laser_intensity = None
        dust_value = None

        if self._current_lasertemp_collector:
            laser_temp = self._current_lasertemp_collector.get_latest_value()
        if self._current_intensity_collector:
            laser_intensity = self._current_intensity_collector.get_latest_value()
        if self._current_dust_collector:
            dust_value = self._current_dust_collector.get_latest_value()

        data = {
            AnalyticsKeys.Job.Progress.PERCENT: payload["progress"],
            AnalyticsKeys.Job.Progress.LASER_TEMPERATURE: laser_temp,
            AnalyticsKeys.Job.Progress.LASER_INTENSITY: laser_intensity,
            AnalyticsKeys.Job.Progress.DUST_VALUE: dust_value,
            AnalyticsKeys.Job.Duration.CURRENT: round(payload["time"], 1),
            AnalyticsKeys.Job.Fan.RPM: self._dust_manager.get_fan_rpm(),
            AnalyticsKeys.Job.Fan.STATE: self._dust_manager.get_fan_state(),
        }

        # We only add the compressor data if there is a compressor
        if self._compressor_handler.has_compressor():
            data.update(
                {
                    AnalyticsKeys.Job.Progress.COMPRESSOR: self._compressor_handler.get_compressor_data()
                }
            )

        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.PROGRESS,
            data,
            header_extension=header_extension,
        )

        if self._current_cpu_data:
            self._current_cpu_data.update_progress(payload["progress"])

    def _event_print_paused(self, event, payload, header_extension=None):
        """
        Cooling: payload holds some information if it was a cooling_pause or not. Lid/Button: Currently there is no
        way to know other than checking the current state: _mrbeam_plugin_implementation.iobeam
        .is_interlock_closed()
        """
        _ = event
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.PAUSED,
            payload={
                AnalyticsKeys.Job.Duration.CURRENT: int(round(payload.get("time", 0.0)))
            },
            header_extension=header_extension,
        )

    def _event_print_resumed(self, event, payload, header_extension=None):
        _ = event
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.RESUMED,
            payload={
                AnalyticsKeys.Job.Duration.CURRENT: int(round(payload.get("time", 0.0)))
            },
            header_extension=header_extension,
        )

    def _event_laser_cooling_pause(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        data = {
            AnalyticsKeys.Job.LaserHead.TEMP: None,
            AnalyticsKeys.Job.LaserHead.COOLING_TEMPERATURE: self._laserhead_handler.current_laserhead_max_temperature,
            AnalyticsKeys.Job.LaserHead.SUMMER_MONTH_TEMPERATURE_OFFSET: self._laserhead_handler.get_summermonth_temperature_offset(),
        }
        if self._current_lasertemp_collector:
            data[
                AnalyticsKeys.Job.LaserHead.TEMP
            ] = self._current_lasertemp_collector.get_latest_value()
        self._add_job_event(
            AnalyticsKeys.Job.Event.Cooling.START,
            payload=data,
            header_extension=header_extension,
        )

    def _event_laser_cooling_resume(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        data = {AnalyticsKeys.Job.LaserHead.TEMP: None}
        if self._current_lasertemp_collector:
            data[
                AnalyticsKeys.Job.LaserHead.TEMP
            ] = self._current_lasertemp_collector.get_latest_value()
        self._add_job_event(
            AnalyticsKeys.Job.Event.Cooling.DONE,
            payload=data,
            header_extension=header_extension,
        )

    def _on_event_laser_cooling_to_slow(self, event, payload, header_extension=None):
        """On Event Laser Cooling to slow add Analytics entry.

        Args:
            event: event that triggered the call
            payload: payload of the event
            header_extension: extension of the header

        Returns:
            None
        """
        _ = event
        _ = payload

        if header_extension is None:
            header_extension = {}

        header_extension.update(
            {
                AnalyticsKeys.Header.FEATURE_ID: "SW-991",
            }
        )

        data = {
            AnalyticsKeys.Job.LaserHead.TEMP: None,
            AnalyticsKeys.Job.Event.Cooling.DIFFERENCE: payload.get(
                "cooling_difference"
            ),
            AnalyticsKeys.Job.Event.Cooling.TIME: payload.get("cooling_time"),
        }
        if self._current_lasertemp_collector:
            data[
                AnalyticsKeys.Job.LaserHead.TEMP
            ] = self._current_lasertemp_collector.get_latest_value()
        self._add_job_event(
            AnalyticsKeys.Job.Event.Cooling.TO_SLOW,
            payload=data,
            header_extension=header_extension,
        )

    def _event_print_done(self, event, payload, header_extension=None):
        _ = event
        duration = {
            AnalyticsKeys.Job.Duration.CURRENT: int(round(payload.get("time", 0.0))),
            AnalyticsKeys.Job.Duration.ESTIMATION: int(
                round(self._current_job_time_estimation_v1)
            ),
            AnalyticsKeys.Job.Duration.ESTIMATION_V2: int(
                round(self.current_job_time_estimation_v2)
            ),
        }
        self._current_job_final_status = "Done"
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.DONE,
            payload=duration,
            header_extension=header_extension,
        )
        self._add_collector_details()
        self._add_cpu_data(
            dur=payload.get("time", 0.0), header_extension=header_extension
        )

    def _event_print_failed(self, event, payload, header_extension=None):
        details = {
            AnalyticsKeys.Job.Duration.CURRENT: int(round(payload.get("time", 0.0))),
            AnalyticsKeys.Job.ERROR: payload.get("error_msg", self.UNKNOWN_VALUE),
        }
        self._current_job_final_status = "Failed"
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.FAILED,
            payload=details,
            header_extension=header_extension,
        )
        self._add_collector_details()
        self._add_cpu_data(dur=payload.get("time", 0.0))

    def _event_print_cancelled(self, event, payload, header_extension=None):
        _ = event
        self._current_job_final_status = "Cancelled"
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.CANCELLED,
            payload={
                AnalyticsKeys.Job.Duration.CURRENT: int(round(payload.get("time", 0.0)))
            },
            header_extension=header_extension,
        )
        self._add_collector_details()
        self._add_cpu_data(dur=payload.get("time", 0.0))

    def _on_event_print_aborted(self, event, payload, header_extension=None):
        """Callback for aborted print event . Will add an event to analytics.

        Args:
            event: event that triggered the action
            payload: payload of the event
            header_extension: extension for the header

        Returns:
            None
        """
        _ = event
        trigger = payload.get("trigger", None)

        self._current_job_final_status = "Aborted"
        self._add_job_event(
            AnalyticsKeys.Job.Event.Print.ABORTED,
            payload={
                AnalyticsKeys.Job.TRIGGER: trigger,
            },
            header_extension=header_extension,
        )
        self._add_collector_details()
        self._add_cpu_data(dur=payload.get("time"))

    def _event_laser_job_finished(self, event, payload, header_extension=None):
        _ = event
        _ = payload
        self._add_job_event(
            AnalyticsKeys.Job.Event.LASERJOB_FINISHED,
            payload={AnalyticsKeys.Job.STATUS: self._current_job_final_status},
            header_extension=header_extension,
        )
        self._cleanup_job()

        self.upload()  # delay of 5.0 s

    def _event_job_time_estimated(self, event, payload, header_extension=None):
        _ = event
        self._current_job_time_estimation_v1 = payload["job_time_estimation_raw"]

        if self._current_job_id:
            payload = {
                AnalyticsKeys.Job.Duration.ESTIMATION: int(
                    round(self._current_job_time_estimation_v1)
                ),
                AnalyticsKeys.Job.Duration.ESTIMATION_V2: int(
                    round(self.current_job_time_estimation_v2)
                ),
                AnalyticsKeys.Job.Duration.CALC_DURATION_TOTAL: payload[
                    "calc_duration_total"
                ],
                AnalyticsKeys.Job.Duration.CALC_DURATION_WOKE: payload[
                    "calc_duration_woke"
                ],
                AnalyticsKeys.Job.Duration.CALC_LINES: payload["calc_lines"],
            }
            self._add_job_event(
                AnalyticsKeys.Job.Event.JOB_TIME_ESTIMATED,
                payload=payload,
                header_extension=header_extension,
            )

    def _add_other_plugin_data(self, event, event_payload, header_extension=None):
        try:
            if (
                "component" in event_payload
                and "type" in event_payload
                and "component_version" in event_payload
            ):
                component = event_payload.get("component")
                event_type = event_payload.get("type")
                if event_type == AnalyticsKeys.Log.Event.EVENT_LOG:
                    data = event_payload.get("data", dict())
                    data[AnalyticsKeys.Log.Component.NAME] = component
                    data[AnalyticsKeys.Log.Component.VERSION] = event_payload.get(
                        "component_version"
                    )
                    self._add_log_event(
                        AnalyticsKeys.Log.Event.EVENT_LOG,
                        payload=data,
                        header_extension=header_extension,
                    )
                else:
                    self._logger.warn(
                        "Unknown type: '%s' from component %s. payload: %s",
                        event_type,
                        component,
                        event_payload,
                    )
            elif "plugin" in event_payload and "eventname" in event_payload:
                plugin = event_payload.get("plugin")
                if plugin:
                    event_name = event_payload.get("eventname")
                    data = event_payload.get("data", None)
                    data.update(
                        {"plugin_version": event_payload.get("plugin_version", None)}
                    )
                    self._add_event_to_queue(
                        plugin,
                        event_name,
                        payload=data,
                        header_extension=header_extension,
                    )
                else:
                    self._logger.warn(
                        "Invalid plugin: '%s'. payload: %s", plugin, event_payload
                    )
            else:
                self._logger.warn("Invalid payload data in event %s", event)
        except Exception as e:
            self._logger.exception(
                "Exception during _add_other_plugin_data: {}".format(e)
            )

    def _on_event_laser_high_temperature(self, event, payload, header_extension=None):
        """Callback for laser high temperature event.

        Args:
            event: event that triggered this action
            payload: payload of the event
            header_extension: extension to the header

        Returns:
            None
        """
        _ = event
        try:
            if header_extension is None:
                header_extension = dict()

            header_extension.update(
                {
                    AnalyticsKeys.Header.FEATURE_ID: "SW-991",
                }
            )
            if payload:
                self._add_device_event(
                    AnalyticsKeys.Device.Event.LASER_HIGH_TEMPERATURE,
                    payload=dict(
                        temperature=payload.get("tmp", 0),
                        threshold=self._temperature_manager.high_tmp_warn_threshold,
                    ),
                    header_extension=header_extension,
                )
        except Exception as e:
            self._logger.exception(
                "Exception during _on_event_laser_high_temperature: {}".format(e)
            )

    def _on_event_high_temperature_shown(self, event, payload, header_extension=None):
        """Callback for high temperature warning or critical shown event.
        Will add an event to analytics.

        Args:
            event: event that triggered this action
            payload: payload of the event
            header_extension: extension to the header

        Returns:
            None
        """
        _ = payload

        if header_extension is None:
            header_extension = dict()

        header_extension.update(
            {
                AnalyticsKeys.Header.FEATURE_ID: "SW-991",
            }
        )

        if event == MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW:
            analytics_event_key = AnalyticsKeys.Device.HighTemp.WARNING_SHOWN
        elif event == MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_SHOW:
            analytics_event_key = AnalyticsKeys.Device.HighTemp.CRITICAL_SHOWN
        else:
            self._logger.error(
                "Unknown event %s for _on_event_high_temperature_shown", event
            )
            return
        try:
            self._add_device_event(
                analytics_event_key,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during _on_event_high_temperature_shown: {}".format(e)
            )

    def _on_event_high_temperature_dismissed(
        self, event, payload, header_extension=None
    ):
        """Callback for high temperature warning/critical dismissed event. Will add an event to analytics.
        Will add an event to analytics.

        Args:
            event: event that triggered this action
            payload: payload of the event
            header_extension: extension to the header

        Returns:
            None
        """
        _ = payload

        if header_extension is None:
            header_extension = dict()

        header_extension.update(
            {
                AnalyticsKeys.Header.FEATURE_ID: "SW-991",
            }
        )

        if event == MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED:
            analytics_event_key = AnalyticsKeys.Device.HighTemp.WARNING_DISMISSED
        elif event == MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED:
            analytics_event_key = AnalyticsKeys.Device.HighTemp.CRITICAL_DISMISSED
        else:
            self._logger.error(
                "Unknown event %s for _on_event_high_temperature_dismissed", event
            )
            return
        try:
            self._add_device_event(
                analytics_event_key,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during _on_event_high_temperature_dismissed: {}".format(e)
            )

    def _on_event_laser_cooling_re_trigger_fan(
        self, event, payload, header_extension=None
    ):
        """Callback for laser cooling re-trigger fan event to add analytics entry.

        Args:
            event: event that triggered this action
            payload: payload of the event
            header_extension: header extension

        Returns:
            None
        """

        _ = payload
        _ = event

        if header_extension is None:
            header_extension = dict()

        header_extension.update(
            {
                AnalyticsKeys.Header.FEATURE_ID: "SW-991",
            }
        )

        try:
            self._add_device_event(
                AnalyticsKeys.Job.Event.Cooling.COOLING_FAN_RETRIGGER,
                header_extension=header_extension,
            )
        except Exception as e:
            self._logger.exception(
                "Exception during _on_event_laser_cooling_re_trigger_fan: {}".format(e)
            )

    # -------- ANALYTICS LOGS QUEUE ------------------------------------------------------------------------------------
    def _add_device_event(self, event, payload=None, header_extension=None):
        self._add_event_to_queue(
            AnalyticsKeys.EventType.DEVICE,
            event,
            payload=payload,
            header_extension=header_extension,
        )

    def _add_log_event(
        self, event, payload=None, analytics=False, header_extension=None
    ):
        self._add_event_to_queue(
            AnalyticsKeys.EventType.LOG,
            event,
            payload=payload,
            analytics=analytics,
            header_extension=header_extension,
        )

    def _add_frontend_event(self, event, payload=None, header_extension=None):
        self._add_event_to_queue(
            AnalyticsKeys.EventType.FRONTEND,
            event,
            payload=payload,
            analytics=True,
            header_extension=header_extension,
        )

    def _add_job_event(self, event, payload=None, header_extension=None):
        self._add_event_to_queue(
            AnalyticsKeys.EventType.JOB,
            event,
            payload=payload,
            header_extension=header_extension,
        )

    def _add_connectivity_event(self, event, payload, header_extension=None):
        self._add_event_to_queue(
            AnalyticsKeys.EventType.CONNECTIVITY,
            event,
            payload=payload,
            header_extension=header_extension,
        )

    def _add_event_to_queue(
        self,
        event_type,
        event_name,
        payload=None,
        header_extension=None,
        analytics=True,
    ):
        try:
            data = dict()
            if isinstance(payload, dict):
                data = payload

            if not isinstance(header_extension, dict):
                header_extension = dict()

            event = {
                AnalyticsKeys.Header.SNR: self._snr,
                AnalyticsKeys.Header.TYPE: event_type,
                AnalyticsKeys.Header.ENV: self._plugin.get_env(),
                AnalyticsKeys.Header.VERSION: self.ANALYTICS_LOG_VERSION,
                AnalyticsKeys.Header.EVENT: event_name,
                AnalyticsKeys.Header.TIMESTAMP: time.time(),
                AnalyticsKeys.Header.NTP_SYNCED: self._plugin.is_time_ntp_synced(),
                AnalyticsKeys.Header.SESSION_ID: self._session_id,
                AnalyticsKeys.Header.VERSION_MRBEAM_PLUGIN: self._plugin_version,
                AnalyticsKeys.Header.SOFTWARE_TIER: self._settings.get(
                    ["dev", "software_tier"]
                ),
                AnalyticsKeys.Header.DATA: data,
                AnalyticsKeys.Header.UPTIME: get_uptime(),
                AnalyticsKeys.Header.MODEL: self._plugin.get_model_id(),
                AnalyticsKeys.Header.LH_MODEL_ID: self._laserhead_handler.get_current_used_lh_model_id()
                if self._laserhead_handler is not None
                else self.UNKNOWN_VALUE,
                AnalyticsKeys.Header.LH_SERIAL: self._plugin.get_current_laser_head_serial()
                if self._laserhead_handler is not None
                else self.UNKNOWN_VALUE,
                AnalyticsKeys.Header.FEATURE_ID: header_extension.get(
                    AnalyticsKeys.Header.FEATURE_ID, None
                ),
            }

            if event_type == AnalyticsKeys.EventType.JOB:
                event[AnalyticsKeys.Job.ID] = self._current_job_id

            self._add_to_queue(event)

        except Exception as e:
            self._logger.exception(
                "Exception during _add_event_to_queue: {}".format(e),
                analytics=analytics,
            )

    def _add_to_queue(self, element):
        try:
            self._analytics_queue.append(element)
        except Exception as e:
            self._logger.info("Exception during _add_to_queue: {}".format(e))

    # -------- COLLECTOR METHODS (COMM_ACC2) ---------------------------------------------------------------------------
    def collect_dust_value(self, dust_value):
        if self._current_dust_collector is not None:
            try:
                self._current_dust_collector.addValue(dust_value)
            except Exception as e:
                self._logger.exception(
                    "Exception during collect_dust_value: {}".format(e)
                )

    def collect_laser_temp_value(self, laser_temp):
        if self._current_lasertemp_collector is not None:
            try:
                self._current_lasertemp_collector.addValue(laser_temp)
            except Exception as e:
                self._logger.exception(
                    "Exception during collect_laser_temp_value: {}".format(e)
                )

    def collect_laser_intensity_value(self, laser_intensity):
        if self._current_intensity_collector is not None:
            try:
                self._current_intensity_collector.addValue(laser_intensity)
            except Exception as e:
                self._logger.exception(
                    "Exception during collect_laser_intensity_value: {}".format(e)
                )

    def _init_collectors(self):
        self._current_dust_collector = ValueCollector("DustColl")
        self._current_intensity_collector = ValueCollector("IntensityColl")
        self._current_lasertemp_collector = ValueCollector("TempColl")

    def _add_collector_details(self):
        if self._current_dust_collector:
            dust_summary = self._current_dust_collector.getSummary()
            self._add_job_event(
                AnalyticsKeys.Job.Event.Summary.DUST, payload=dust_summary
            )
        if self._current_intensity_collector:
            intensity_summary = self._current_intensity_collector.getSummary()
            self._add_job_event(
                AnalyticsKeys.Job.Event.Summary.INTENSITY, payload=intensity_summary
            )
        if self._current_lasertemp_collector:
            lasertemp_summary = self._current_lasertemp_collector.getSummary()
            lasertemp_summary[
                AnalyticsKeys.Job.Event.Summary.Laserhead.COOLING_TEMPERATURE
            ] = self._laserhead_handler.current_laserhead_max_temperature
            lasertemp_summary[
                AnalyticsKeys.Job.Event.Summary.Laserhead.SUMMER_MONTH_TEMPERATURE_OFFSET
            ] = self._laserhead_handler.get_summermonth_temperature_offset()
            self._add_job_event(
                AnalyticsKeys.Job.Event.Summary.LASERTEMP, payload=lasertemp_summary
            )

    # -------- HELPER METHODS --------------------------------------------------------------------------------------
    def _cleanup_job(self):
        self._current_job_id = None
        self._current_dust_collector = None
        self._current_intensity_collector = None
        self._current_lasertemp_collector = None
        self._current_cpu_data = None
        self._current_job_time_estimation_v1 = -1
        self.current_job_time_estimation_v2 = -1
        self._current_job_final_status = None
        self._current_job_compressor_data = None

    def _init_new_job(self):
        self._cleanup_job()
        self._current_job_id = "j_{}_{}".format(self._snr, time.time())
        self._add_job_event(AnalyticsKeys.Job.Event.LASERJOB_STARTED, payload=payload)

    # -------- WRITER THREAD (queue --> analytics file) ----------------------------------------------------------------
    def _write_queue_to_analytics_file(self):
        try:
            while self.is_analytics_enabled():
                if not os.path.isfile(self.analytics_file):
                    self._init_json_file()

                with self._analytics_lock:
                    while self._analytics_queue:
                        with open(self.analytics_file, "a") as f_handle:
                            data = self._analytics_queue.popleft()
                            data_string = None
                            try:
                                data_string = (
                                    json.dumps(
                                        data, sort_keys=False, default=json_serialisor
                                    )
                                    + "\n"
                                )
                            except Exception:
                                self._logger.info(
                                    "Exception during json dump in _write_queue_to_analytics_file"
                                )

                            if data_string:
                                f_handle.write(data_string)
                time.sleep(0.1)

        except Exception as e:
            self._logger.exception(
                "Exception during _write_queue_to_analytics_file: {}".format(e),
                analytics=False,
            )

    def _init_json_file(self):
        open(self.analytics_file, "w+").close()

    # -------- INITIAL ANALYTICS PROCEDURE -----------------------------------------------------------------------------
    def initial_analytics_procedure(self, consent):
        if consent == "agree":
            self.analytics_user_permission_change(True)
            self.process_analytics_files()

        elif consent == "disagree":
            self.analytics_user_permission_change(False)
            self.delete_analytics_files()

    def delete_analytics_files(self):
        self._logger.info("Deleting analytics files...")
        folder = self.analytics_folder
        for analytics_file in os.listdir(folder):
            file_path = os.path.join(folder, analytics_file)
            try:
                if os.path.isfile(file_path) and "analytics" in analytics_file:
                    os.unlink(file_path)
                    self._logger.info("File deleted: {file}".format(file=file_path))
            except Exception as e:
                self._logger.exception(
                    "Exception when deleting file {file}: {error}".format(
                        file=file_path, error=e
                    )
                )

    def process_analytics_files(self):
        self._logger.info("Processing analytics files...")
        folder = self.analytics_folder
        idx = None
        for analytics_file in os.listdir(folder):
            file_path = os.path.join(folder, analytics_file)
            try:
                if os.path.isfile(file_path) and "analytics" in analytics_file:
                    # open + remove file_names + save
                    for idx, line in enumerate(fileinput.input(file_path, inplace=1)):
                        line = re.sub(r"\"filename\": \"[^\"]+\"", "", line)
                        sys.stdout.write(line)
                    self._logger.info("File processed: {file}".format(file=file_path))
            except Exception as e:
                self._logger.exception(
                    "Exception when processing line {line} of file {file}: {e}".format(
                        line=idx, file=file_path, e=e
                    )
                )
