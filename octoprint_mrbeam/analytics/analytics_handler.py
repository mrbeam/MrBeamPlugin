import time
import json
import os.path
import logging
import sys
import fileinput
import re
import uuid

from value_collector import ValueCollector
from cpu import Cpu
from threading import Thread
from Queue import Queue

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.laserhead_handler import laserheadHandler
from analytics_keys import AnalyticsKeys as ak
from timer_handler import TimerHandler
from uploader import FileUploader

# singleton
_instance = None


def analyticsHandler(plugin):
	global _instance
	if _instance is None:
		_instance = AnalyticsHandler(plugin)
	return _instance


def existing_analyticsHandler():
	"""
	Returns AnalyticsHandler instance only if it's already initialized. None otherwise
	:return: None or AnalyticsHandler instance
	"""
	global _instance
	return _instance


class AnalyticsHandler(object):
	QUEUE_MAXSIZE = 100
	SELF_CHECK_USER_AGENT = 'MrBeamPlugin self check'

	def __init__(self, plugin):
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings
		self._laserhead_handler = laserheadHandler(plugin)  # TODO IRATXE: This is still not initialized in the plugin
		self._snr = plugin.getSerialNum()
		self._plugin_version = plugin._plugin_version

		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.analyticshandler")

		self._analytics_enabled = self._settings.get(['analyticsEnabled'])
		if self._analytics_enabled is None:
			self._no_choice_made = True
		else:
			self._no_choice_made = False

		self._session_id = "{uuid}@{serial}".format(serial=self._snr, uuid=uuid.uuid4().hex)

		self._current_job_id = None
		self._is_job_paused = False
		self._is_cooling_paused = False
		self._is_job_done = False

		self._current_dust_collector = None
		self._current_cam_session_id = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None
		self._current_cpu_data = None
		self._current_job_time_estimation = None

		self._analytics_log_version = 8  # bumped in 0.3.2.1 TODO IRATXE: move iwo

		self.event_waiting_for_terminal_dump = None

		self._logger.info("Analytics analyticsEnabled: %s, sid: %s", self._analytics_enabled, self._session_id)

		self.analytics_folder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['analytics', 'folder']))
		if not os.path.isdir(self.analytics_folder):
			os.makedirs(self.analytics_folder)

		# It uploads any previous analytics, unless the user didn't make a choice yet
		if not self._no_choice_made:
			FileUploader.upload_now(self._plugin)

		self._jsonfile = os.path.join(self.analytics_folder, self._settings.get(['analytics', 'filename']))

		self._shutdown_signaled = False  # TODO IRATXE: keep or not

		self._analytics_queue = Queue(maxsize=self.QUEUE_MAXSIZE)
		self._analytics_writer = Thread(target=self._write_queue_to_analytics_file)
		self._timer_handler = TimerHandler()
		if self._analytics_enabled:
			self._activate_analytics()

	def shutdown(self, *args):  # TODO IRATXE: keep or not?
		self._logger.debug("shutdown() args: %s", args)
		global _instance
		_instance = None
		self._shutdown_signaled = True

	def _activate_analytics(self):
		# Restart queue if the analytics were disabled before
		if not self._no_choice_made:
			self._analytics_queue = Queue(self.QUEUE_MAXSIZE)
		else:
			self._no_choice_made = False

		# Start writer thread
		self._analytics_writer.daemon = True  # TODO IRATXE: keep or not?
		self._analytics_writer.start()

		# Start timers for async analytics
		self._timer_handler.start_timers()

		# Subscribe to OctoPrint and Mr Beam events
		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._event_print_started)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self._event_print_paused)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self._event_print_resumed)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_print_done)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._event_print_failed)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._event_print_cancelled)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_STARTED, self._event_slicing_started)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self._event_slicing_done)
		self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self._event_print_progress)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_PAUSE, self._event_laser_cooling_pause)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_RESUME, self._event_laser_cooling_resume)
		self._event_bus.subscribe(MrBeamEvents.LASER_JOB_DONE, self._event_laser_job_done)
		self._event_bus.subscribe(MrBeamEvents.LASER_JOB_CANCELLED, self._event_laser_job_done)
		self._event_bus.subscribe(MrBeamEvents.LASER_JOB_FAILED, self._event_laser_job_done)
		self._event_bus.subscribe(OctoPrintEvents.STARTUP, self._event_startup)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._event_shutdown)
		self._event_bus.subscribe(MrBeamEvents.ANALYTICS_DATA, self._add_other_plugin_data)
		self._event_bus.subscribe(MrBeamEvents.JOB_TIME_ESTIMATED, self._event_job_time_estimated)

	def _cleanup_job(self):
		self._current_job_id = None
		self._current_dust_collector = None
		self._current_intensity_collector = None
		self._current_lasertemp_collector = None
		self._current_cpu_data = None
		self._current_job_time_estimation = None

	def _init_new_job(self):
		self._cleanup_job()
		self._current_job_id = 'j_{}_{}'.format(self._snr, time.time())
		self._add_job_event(ak.LASERJOB_STARTED)

	def _add_cpu_data(self, dur=None):
		payload = self._current_cpu_data.get_cpu_data()
		payload['dur'] = dur
		self._add_job_event(ak.CPU_DATA, payload=payload)

	# -------- OCTOPRINT AND MR BEAM EVENTS ----------------------------------------------------------------------------
	def _event_startup(self, event, payload):
		payload = {
			ak.LASERHEAD_SERIAL: self._laserhead_handler.get_current_used_lh_data()['serial'],
			ak.ENV: self._plugin.get_env(),
			ak.USERS: len(self._plugin._user_manager._users)
		}
		self._add_device_event(ak.STARTUP, payload=payload)

	def _event_shutdown(self, event, payload):
		self._add_device_event(ak.SHUTDOWN)

	def _event_slicing_started(self, event, payload):
		self._init_new_job()
		self._add_job_event(ak.SLICING_STARTED)
		self._current_cpu_data = Cpu(state='slicing', repeat=False)

	def _event_slicing_done(self, event, payload):
		if self._current_cpu_data:
			self._current_cpu_data.record_cpu_data()
			self._add_cpu_data(dur=payload['time'])
		self._add_job_event(ak.SLICING_DONE)

	def _event_print_started(self, event, payload):
		# If there's no job_id, it may be a gcode file (no slicing), so we have to start the job here
		if not self._current_job_id:
			self._init_new_job()
		self._current_cpu_data = Cpu(state='laser', repeat=True)
		self._init_collectors()
		self._is_job_paused = False
		self._is_cooling_paused = False
		self._is_job_done = False
		self._add_job_event(ak.PRINT_STARTED)

	def _event_print_progress(self, event, payload):
		data = {
			ak.PROGRESS_PERCENT: payload['progress'],
			ak.PROGRESS_LASER_TEMPERATURE: self._current_lasertemp_collector.get_latest_value(),
			ak.PROGRESS_LASER_INTENSITY: self._current_intensity_collector.get_latest_value(),
			ak.PROGRESS_DUST_VALUE: self._current_dust_collector.get_latest_value(),
			ak.JOB_DURATION: round(payload['time'], 1),
			ak.FAN_RPM: self._plugin._dustManager.get_fan_rpm(),
			ak.FAN_STATE: self._plugin._dustManager.get_fan_state(),
		}
		self._add_job_event(ak.PRINT_PROGRESS, data)

		if self._current_cpu_data:
			self._current_cpu_data.update_progress(payload['progress'])

	def _event_print_paused(self, event, payload):
		"""
		Cooling: payload holds some information if it was a cooling_pause or not. Lid/Button: Currently there is no
		way to know other than checking the current state: _mrbeam_plugin_implementation._ioBeam
		.is_interlock_closed()
		"""
		if not self._is_job_paused:  # prevent multiple printPaused events per Job
			self._add_job_event(ak.PRINT_PAUSED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._is_job_paused = True

	def _event_print_resumed(self, event, payload):
		if self._is_job_paused:  # prevent multiple printResume events per Job
			self._add_job_event(ak.PRINT_RESUMED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._is_job_paused = False

	def _event_laser_cooling_pause(self, event, payload):
		if not self._is_cooling_paused:
			data = {
				ak.LASERTEMP: None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._add_job_event(ak.COOLING_START, payload=data)
			self._is_cooling_paused = True

	def _event_laser_cooling_resume(self, event, payload):
		if self._is_cooling_paused:
			data = {
				ak.LASERTEMP: None
			}
			if self._current_lasertemp_collector:
				data[ak.LASERTEMP] = self._current_lasertemp_collector.get_latest_value()
			self._add_job_event(ak.COOLING_DONE, payload=data)
			self._is_cooling_paused = False

	def _event_print_done(self, event, payload):
		if not self._is_job_done:
			self._is_job_done = True  # prevent two jobDone events per Job
			payload = {
				ak.JOB_DURATION: int(round(payload['time'])),
				ak.JOB_TIME_ESTIMATION: int(round(self._current_job_time_estimation))
			}

			self._add_job_event(ak.PRINT_DONE, payload=payload)
			self._add_collector_details()
			self._add_cpu_data(dur=payload['time'])

	def _event_print_failed(self, event, payload):
		if not self._current_job_id:
			self._add_job_event(ak.PRINT_FAILED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._add_collector_details()
			self._add_cpu_data(dur=payload['time'])

	def _event_print_cancelled(self, event, payload):
		if not self._current_job_id:
			self._add_job_event(ak.PRINT_CANCELLED, payload={ak.JOB_DURATION: int(round(payload['time']))})
			self._add_collector_details()
			self._add_cpu_data(dur=payload['time'])

	# We will also call this from the Mr Beam events "cancelled" and "failed"
	def _event_laser_job_done(self, event, payload):
		if not self._current_job_id:
			self._add_job_event(ak.LASERJOB_DONE)
			self._cleanup_job()
		FileUploader.upload_now(self._plugin, delay=5.0)

	def _event_job_time_estimated(self, event, payload):
		self._current_job_time_estimation = payload['jobTimeEstimation']

	def _add_other_plugin_data(self, event, event_payload):
		try:
			if 'component' in event_payload and 'type' in event_payload and 'component_version' in event_payload:
				component = event_payload.get('component')
				event_type = event_payload.get('type')
				if event_type == ak.EVENT_LOG:
					data = event_payload.get('data', dict())
					data['component'] = component
					data['component_version'] = event_payload.get('component_version')
					self._add_log_event(ak.EVENT_LOG, payload=data)
				else:
					self._logger.warn("Unknown type: '%s' from component %s. payload: %s", event_type, component, event_payload)
			elif 'plugin' in event_payload and 'event_name' in event_payload:
				plugin = event_payload.get('plugin')
				if plugin:
					event_name = event_payload.get('eventname')
					data = event_payload.get('data', None)
					self._add_event_to_queue(plugin, event_name, payload=data)
				else:
					self._logger.warn("Invalid plugin: '%s'. payload: %s", plugin, event_payload)
			else:
				self._logger.warn("Invalid payload data in event %s", event)
		except Exception as e:
			self._logger.exception('Exception during _add_other_plugin_data: {}'.format(e))

	# -------- EXTERNALLY CALLED METHODS -------------------------------------------------------------------------------
	# INIT
	def analytics_user_permission_change(self, analytics_enabled):
		self._logger.info("analytics user permission change: analyticsEnabled=%s", analytics_enabled)

		if analytics_enabled:
			self._analytics_enabled = True
			self._settings.set_boolean(["analyticsEnabled"], True)
			self._activate_analytics()
			self._add_device_event(ak.ANALYTICS_ENABLED, payload=dict(enabled=True))
		else:
			# can not log this since the user just disagreed
			# self._add_device_event(ak.ANALYTICS_ENABLED, payload=dict(enabled=False))
			self._analytics_enabled = False
			self._timer_handler.cancel_timers()
			self._settings.set_boolean(["analyticsEnabled"], False)

	def add_ui_render_call_event(self, host, remote_ip, referrer, language):
		try:
			call = dict(
				host=host,
				remote_ip=remote_ip,
				referrer=referrer,
				language=language
			)
			self._add_connectivity_event(ak.EVENT_UI_RENDER_CALL, payload=call)
		except Exception as e:
			self._logger.exception('Exception during add_ui_render_call_event: {}'.format(e))

	def add_client_opened_event(self, remote_ip):
		try:
			data = dict(
				remote_ip=remote_ip
			)
			self._add_connectivity_event(ak.EVENT_CLIENT_OPENED, payload=data)
		except Exception as e:
			self._logger.exception('Exception during add_client_opened_event: {}'.format(e))

	def add_frontend_event(self, event, payload=None):
		try:
			self._add_frontend_event(event, payload=payload)
		except Exception as e:
			self._logger.exception('Error during add_frontend_event: {}'.format(e), analytics=True)

	# TIMER_HANDLER
	def add_mrbeam_usage(self, usage_data):
		self._add_device_event(ak.MRBEAM_USAGE, payload=usage_data)

	def add_http_self_check(self, payload):
		self._add_device_event(ak.HTTP_SELF_CHECK, payload=payload)

	def add_internet_connection(self, payload):
		self._add_device_event(ak.INTERNET_CONNECTION, payload=payload)

	def add_ip_addresses(self, payload):
		self._add_device_event(ak.IPS, payload=payload)

	def add_disk_space(self, payload):
		self._add_device_event(ak.MRBEAM_USAGE, payload=payload)

	# MRB_LOGGER
	def add_logger_event(self, event_details, wait_for_terminal_dump):
		self._logger.info('################## CUIDADO, log_event!')
		filename = event_details['caller'].filename.replace(__package_path__ + '/', '')

		if event_details['level'] in logging._levelNames:
			event_details['level'] = logging._levelNames[event_details['level']]

		if event_details['exception_str']:
			event_details['level'] = ak.EXCEPTION

		caller = event_details.pop('caller', None)
		if caller:
			event_details.update({
				'hash': hash('{}{}{}'.format(filename, caller.lineno, self._plugin_version)),
				'file': filename,
				'line': caller.lineno,
				'function': caller.function,
				# code_context: caller.code_context[0].strip()
			})

		if wait_for_terminal_dump:  # If it is a e.g. GRBL error, we will have to wait some time for the whole dump
			self.event_waiting_for_terminal_dump = dict(event_details)
		else:
			self._add_log_event(ak.EVENT_LOG, payload=event_details, analytics=False)

	def log_terminal_dump(self, dump):  # Will be used with e.g. GRBL errors
		if self.event_waiting_for_terminal_dump is not None:
			payload = dict(self.event_waiting_for_terminal_dump)
			payload['terminal_dump'] = dump
			self._add_log_event(ak.EVENT_LOG, payload=payload, analytics=False)
			self.event_waiting_for_terminal_dump = None
		else:
			self._logger.warn(
				"log_terminal_dump() called but no foregoing event tracked. self.event_waiting_for_terminal_dump is "
				"None. ignoring this dump.")

	# LASERHEAD_HANDLER
	def add_laserhead_info(self):
		try:
			lh = self._laserhead_handler.get_current_used_lh_data()
			settings = self._laserhead_handler.get_correction_settings()
			laserhead_info = {
				ak.LASERHEAD_SERIAL: lh['serial'],
				ak.POWER_65: lh['info']['p_65'],
				ak.POWER_75: lh['info']['p_75'],
				ak.POWER_85: lh['info']['p_85'],
				ak.CORRECTION_FACTOR: lh['info']['correction_factor'],
				ak.CORRECTION_ENABLED: settings['correction_enabled'],
				ak.CORRECTION_OVERRIDE: settings['correction_factor_override'],
			}
			self._add_device_event(ak.LASERHEAD_INFO, payload=laserhead_info)

		except:
			self._logger.exception('Exception when saving info about the laserhead')

	# LID_HANDLER
	def add_camera_session(self, errors):
		try:
			self._logger.info(errors)
			success = True
			if errors:
				success = False
			data = {
				'success': success,
				'err': errors,
			}
			self._add_log_event(ak.CAMERA, payload=data)

		except Exception as e:
			self._logger.exception('Error during log_camera_error: {}'.format(e), analytics=True)

	# IOBEAM_HANDLER
	def add_iobeam_message_log(self, iobeam_version, message):
		data = dict(
			version=iobeam_version,
			message=message
		)
		self._add_log_event(ak.IOBEAM, payload=data)

	# ACC_WATCH_DOG
	def add_cpu_log(self, temp, throttle_alerts):
		try:
			data = {'temp': temp,
					'throttle_alerts': throttle_alerts}
			self._add_log_event(ak.LOG_CPU, payload=data)
		except Exception as e:
			self._logger.exception('Error during add_cpu_log: {}'.format(e), analytics=True)

	# CONVERTER
	def add_material_details(self, material_details):
		try:
			self._add_job_event(ak.LASER_JOB, payload=material_details)  # TODO IRATXE: this name does not make sense
		except Exception as e:
			self._logger.exception('Error during add_material_details: {}'.format(e))

	def add_engraving_parameters(self, eng_params):
		try:
			self._add_job_event(ak.CONV_ENGRAVE, payload=eng_params)
		except Exception as e:
			self._logger.exception('Error during add_engraving_parameters: {}'.format(e))

	def add_cutting_parameters(self, cut_details):
		try:
			self._add_job_event(ak.CONV_CUT, payload=cut_details)
		except Exception as e:
			self._logger.exception('Error during add_cutting_parameters: {}'.format(e))

	def add_design_file_details(self, design_file):
		try:
			self._add_job_event(ak.DESIGN_FILE, payload=design_file)
		except Exception as e:
			self._logger.exception('Error during add_design_file_details: {}'.format(e))

	# COMM_ACC2
	def add_grbl_flash_event(self, from_version, to_version, successful, err=None):
		payload = dict(
			from_version=from_version,
			to_version=to_version,
			succesful=successful,
			err=err)
		self._add_device_event(ak.FLASH_GRBL, payload=payload)

	# SOFTWARE_UPDATE_INFORMATION
	def add_software_channel_switch_event(self, old_channel, new_channel):
		try:
			channels = {
				ak.OLD_CHANNEL: old_channel,
				ak.NEW_CHANNEL: new_channel,
			}

			self._add_event_to_queue(ak.TYPE_DEVICE_EVENT, ak.SW_CHANNEL_SWITCH, payload=channels)

		except Exception as e:
			self._logger.exception('Error during add_software_channel_switch_event: {}'.format(e))

	# LED_EVENTS
	def add_connections_state(self, connections):
		try:
			self._add_event_to_queue(ak.TYPE_CONNECTIVITY_EVENT, ak.CONNECTIONS_STATE, payload=connections)
		except Exception as e:
			self._logger.exception('Exception during add_connections_state: {}'.format(e))

	# DUST_MANAGER
	def add_fan_rpm_test(self, data):
		try:
			if self._current_job_id:
				self._add_job_event(ak.FAN_RPM_TEST, payload=data)
		except Exception as e:
			self._logger.exception('Error during add_fan_rpm_test: {}'.format(e))

	def add_final_dust_details(self, dust_start, dust_start_ts, dust_end, dust_end_ts):
		"""
		Sends dust values after print_done (the final dust profile). This is to check how fast dust is getting less
		in the machine and to check for filter full later.
		:param dust_start: dust_value at state print_done
		:param dust_start_ts: timestamp of dust_value at state print done
		:param dust_end: dust_value at job_done
		:param dust_end_ts: timestamp at dust_value at job_done
		:return:
		"""
		dust_duration = round(dust_end_ts - dust_start_ts, 4)
		dust_difference = round(dust_end - dust_start, 5)
		dust_per_time = dust_difference / dust_duration
		self._logger.debug("dust extraction time {} from {} to {} (difference: {},gradient: {})".format(dust_duration, dust_start, dust_end, dust_difference, dust_per_time))

		data = {
			ak.DUST_START: dust_start,
			ak.DUST_END: dust_end,
			ak.DUST_START_TS: dust_start_ts,
			ak.DUST_END_TS: dust_end_ts,
			ak.DUST_DURATION: dust_duration,
			ak.DUST_DIFF: dust_difference,
			ak.DUST_PER_TIME: dust_per_time
		}
		self._add_job_event(ak.FINAL_DUST, payload=data)

	# OS_HEALTH_CARE
	def add_os_health_log(self, data):
		try:
			self._add_log_event(ak.OS_HEALTH, payload=data)
		except Exception as e:
			self._logger.exception('Error during add_frontend_event: {}'.format(e), analytics=True)

	# -------- ANALYTICS LOGS QUEUE ------------------------------------------------------------------------------------
	def _add_device_event(self, event, payload=None):
		self._add_event_to_queue(ak.TYPE_DEVICE_EVENT, event, payload=payload)

	def _add_log_event(self, event, payload=None, analytics=False):
		self._add_event_to_queue(ak.TYPE_LOG_EVENT, event, payload=payload, analytics=analytics)

	def _add_frontend_event(self, event, payload=None):
		self._add_event_to_queue(ak.TYPE_FRONTEND, event, payload=payload, analytics=True)

	def _add_job_event(self, event, payload=None):
		self._add_event_to_queue(ak.TYPE_JOB_EVENT, event, payload=payload)

	def _add_connectivity_event(self, event, payload):
		self._add_event_to_queue(ak.TYPE_CONNECTIVITY_EVENT, event, payload=payload)

	def _add_event_to_queue(self, event_type, event_name, payload=None, analytics=False):
		try:
			data = dict()
			if isinstance(payload, dict):
				data = payload

			event = {
				ak.SERIALNUMBER: self._snr,
				ak.TYPE: event_type,
				ak.VERSION: self._analytics_log_version,
				ak.EVENT: event_name,
				ak.TIMESTAMP: time.time(),
				ak.NTP_SYNCED: self._plugin.is_time_ntp_synced(),
				ak.SESSION_ID: self._session_id,
				ak.VERSION_MRBEAM_PLUGIN: self._plugin_version,
				ak.SOFTWARE_TIER: self._settings.get(["dev", "software_tier"]),
				ak.DATA: data,
			}

			if event_type == ak.TYPE_JOB_EVENT:
				event[ak.JOB_ID] = self._current_job_id

			self._add_to_queue(event)

		except Exception as e:
			self._logger.error('Error during _add_event_to_queue: {}'.format(e), analytics=analytics)

	def _add_to_queue(self, element):
		try:
			self._analytics_queue.put(element)
			self._logger.info('################## QUEUE: {}'.format(self._analytics_queue.qsize()))
		except Queue.Full:
			self._logger.info('Analytics queue max size reached ({}). Reinitializing...'.format(self.QUEUE_MAXSIZE))
			self._analytics_queue = Queue(maxsize=self.QUEUE_MAXSIZE)

	# -------- COLLECTOR METHODS (COMM_ACC2) ---------------------------------------------------------------------------
	def collect_dust_value(self, dust_value):
		if self._current_dust_collector is not None:
			try:
				self._current_dust_collector.addValue(dust_value)
			except Exception as e:
				self._logger.exception('Error during collect_dust_value: {}'.format(e))

	def collect_laser_temp_value(self, laser_temp):
		if self._current_lasertemp_collector is not None:
			try:
				self._current_lasertemp_collector.addValue(laser_temp)
			except Exception as e:
				self._logger.exception('Error during collect_laser_temp_value: {}'.format(e))

	def collect_laser_intensity_value(self, laser_intensity):
		if self._current_intensity_collector is not None:
			try:
				self._current_intensity_collector.addValue(laser_intensity)
			except Exception as e:
				self._logger.exception('Error during save_laser_intensity_value: {}'.format(e))

	def _init_collectors(self):
		self._current_dust_collector = ValueCollector('DustColl')
		self._current_intensity_collector = ValueCollector('IntensityColl')
		self._current_lasertemp_collector = ValueCollector('TempColl')

	def _add_collector_details(self):
		lh_info = {
			ak.LASERHEAD_VERSION: None,
			ak.LASERHEAD_SERIAL: self._laserhead_handler.get_current_used_lh_data()['serial'],
		}

		self._add_job_event(ak.DUST_SUM, payload=self._current_dust_collector.getSummary())
		self._add_job_event(ak.INTENSITY_SUM, payload=self._current_intensity_collector.getSummary().update(lh_info))
		self._add_job_event(ak.LASERTEMP_SUM, payload=self._current_lasertemp_collector.getSummary().update(lh_info))

	# -------- WRITER THREAD (queue --> analytics file) ----------------------------------------------------------------
	def _write_queue_to_analytics_file(self):
		# while not self._shutdown_signaled: TODO IRATXE: keep or not
		while self._analytics_enabled:
			try:
				if not os.path.isfile(self._jsonfile):
					self._init_json_file()

				with open(self._jsonfile, 'a') as f:
					while not self._analytics_queue.empty():
						data = self._analytics_queue.get()
						data_string = json.dumps(data, sort_keys=False) + '\n'
						f.write(data_string)
						if 'e' in data:
							self._logger.info('################## WRITE -- {}'.format(data['e']))
						else:
							self._logger.info('################## WRITE -- {}'.format(data))

				time.sleep(0.1)

			except Exception as e:
				self._logger.exception('Error while writing data: {}'.format(e), analytics=False)

		self._logger.info('######################### SHUTDOOOOOOOWN')

	def _init_json_file(self):
		open(self._jsonfile, 'w+').close()
		self._add_device_event(ak.INIT, payload={})

	# -------- INITIAL ANALYTICS PROCEDURE -----------------------------------------------------------------------------
	def initial_analytics_procedure(self, consent):
		if consent == 'agree':
			self.analytics_user_permission_change(True)
			self.process_analytics_files()
			FileUploader.upload_now(self._plugin)

		elif consent == 'disagree':
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
					self._logger.info('File deleted: {file}'.format(file=file_path))
			except Exception as e:
				self._logger.exception('Error when deleting file {file}: {error}'.format(file=file_path, error=e))

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
					self._logger.info('File processed: {file}'.format(file=file_path))
			except Exception as e:
				self._logger.exception(
					'Error when processing line {line} of file {file}: {e}'.format(line=idx, file=file_path, e=e))
