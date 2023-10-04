import os
import threading
import time
import unicodedata

import yaml
from octoprint.util import dict_merge

from octoprint_mrbeam import AirFilter
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamValueEvents, IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None


def usageHandler(plugin):
    global _instance
    if _instance is None:
        _instance = UsageHandler(plugin)
    return _instance


class UsageHandler(object):
    MIN_DUST_FACTOR = 0.5
    MAX_DUST_VALUE = 0.5
    MIN_DUST_VALUE = 0.2
    DEFAULT_PREFILTER_LIFESPAN = 40
    HEAVY_DUTY_PREFILTER_LIFESPAN = 80
    MIGRATION_WAIT = 3  # in seconds

    JOB_TIME_KEY = "job_time"
    AIRFILTER_KEY = "airfilter"
    PREFILTER_KEY = "prefilter"
    CARBON_FILTER_KEY = "carbon_filter"
    COMPLETE_KEY = "complete"
    LASER_HEAD_KEY = "laser_head"
    TOTAL_KEY = "total"
    GANTRY_KEY = "gantry"
    COMPRESSOR_KEY = "compressor"
    SUCCESSFUL_JOBS_KEY = "succ_jobs"
    UNKNOWN_SERIAL_KEY = "no_serial"

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.usage")
        self._plugin = plugin
        self._airfilter = None
        self._event_bus = plugin._event_bus
        self._settings = plugin._settings
        self._plugin_version = plugin.get_plugin_version()
        self._device_serial = plugin.getSerialNum()
        self._file_lock = threading.Lock()

        self.start_time_total = -1
        self.start_time_laser_head = -1
        self.start_time_prefilter = -1
        self.start_time_carbon_filter = -1
        self.start_time_gantry = -1
        self.start_time_compressor = -1
        self.start_ntp_synced = None

        self._last_dust_value = None

        analyticsfolder = os.path.join(
            self._settings.getBaseFolder("base"),
            self._settings.get(["analytics", "folder"]),
        )
        if not os.path.isdir(analyticsfolder):
            os.makedirs(analyticsfolder)
        self._storage_file = os.path.join(
            analyticsfolder, self._settings.get(["analytics", "usage_filename"])
        )
        self._backup_file = os.path.join(
            analyticsfolder, self._settings.get(["analytics", "usage_backup_filename"])
        )

        self._usage_data = {}
        self._load_usage_data()

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    @property
    def _usage_data_airfilter(self):
        return self._usage_data.get(self.AIRFILTER_KEY, {})

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._analytics_handler = self._plugin.analytics_handler
        self._laserhead_handler = self._plugin.laserhead_handler
        self._dust_manager = self._plugin.dust_manager
        self._airfilter = self._plugin.airfilter

        # Read laser head. If it's None, use 'no_serial'
        self._lh = self._laserhead_handler.get_current_used_lh_data()
        if self._lh["serial"]:
            self._laser_head_serial = self._lh["serial"]
        else:
            self._laser_head_serial = self.UNKNOWN_SERIAL_KEY
        self._calculate_dust_mapping()
        self._init_missing_usage_data()
        self._log_usage()

        self._subscribe()

    def _calculate_dust_mapping(self):
        max_dust_factor = self._laserhead_handler.current_laserhead_max_dust_factor
        self._dust_mapping_m = (max_dust_factor - self.MIN_DUST_FACTOR) / (
            self.MAX_DUST_VALUE - self.MIN_DUST_VALUE
        )
        self._dust_mapping_b = (
            self.MIN_DUST_FACTOR - self._dust_mapping_m * self.MIN_DUST_VALUE
        )
        self._logger.debug(
            "new dust mapping -> {} - {} - {}".format(
                max_dust_factor, self._dust_mapping_m, self._dust_mapping_b
            )
        )

    def _log_usage(self):
        self._logger.info(
            "Usage: total_usage: {}, pre-filter: {}, main filter: {}, current laser head: {}, mechanics: {}, compressor: {} - {}".format(
                self.get_duration_humanreadable(
                    self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY]
                ),
                self.get_duration_humanreadable(self.get_prefilter_usage()),
                self.get_duration_humanreadable(self.get_carbon_filter_usage()),
                self.get_duration_humanreadable(
                    self._usage_data[self.LASER_HEAD_KEY][self._laser_head_serial][
                        self.JOB_TIME_KEY
                    ]
                ),
                self.get_duration_humanreadable(
                    self._usage_data[self.COMPRESSOR_KEY][self.JOB_TIME_KEY]
                ),
                self.get_duration_humanreadable(
                    self._usage_data[self.GANTRY_KEY][self.JOB_TIME_KEY]
                ),
                self._usage_data,
            )
        )

    def _subscribe(self):
        self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._event_start)
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_PAUSED, self._event_write
        )  # cooling breaks also send a regular pause event
        self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_stop)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._event_stop)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._event_stop)
        self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self._event_write)
        self._event_bus.subscribe(
            MrBeamEvents.LASER_HEAD_READ, self._event_laser_head_read
        )
        self._plugin.iobeam.subscribe(
            IoBeamValueEvents.LASERHEAD_CHANGED, self._event_laserhead_changed
        )
        self._event_bus.subscribe(IoBeamEvents.FAN_CONNECTED, self._event_fan_connected)

    def _event_laser_head_read(self, event, payload):
        # Update laser head info if necessary --> Only update if there is a serial number different than the previous
        if payload["serial"] and self._lh["serial"] != payload["serial"]:
            self._lh = self._laserhead_handler.get_current_used_lh_data()
            self._laser_head_serial = self._lh["serial"]
            self._init_missing_usage_data()

    def _event_start(self, event, payload):
        self._load_usage_data()
        self.start_time_total = self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY]
        self.start_time_prefilter = self.get_prefilter_usage()
        self.start_time_carbon_filter = self.get_carbon_filter_usage()
        self.start_time_laser_head = self._usage_data[self.LASER_HEAD_KEY][
            self._laser_head_serial
        ][self.JOB_TIME_KEY]
        self.start_time_gantry = self._usage_data[self.GANTRY_KEY][self.JOB_TIME_KEY]
        self.start_time_compressor = self._usage_data[self.COMPRESSOR_KEY][
            self.JOB_TIME_KEY
        ]
        self.start_ntp_synced = self._plugin._time_ntp_synced

        self._last_dust_value = None

    def _event_write(self, event, payload):
        if self.start_time_total >= 0:
            self._update_last_dust_value()
            self._set_time(payload["time"])

    def _event_stop(self, event, payload):
        if event == OctoPrintEvents.PRINT_DONE:
            self._usage_data[self.SUCCESSFUL_JOBS_KEY]["count"] = (
                self._usage_data[self.SUCCESSFUL_JOBS_KEY]["count"] + 1
            )

        if self.start_time_total >= 0:
            self._update_last_dust_value()
            self._set_time(payload["time"])

            self.start_time_total = -1
            self.start_time_laser_head = -1
            self.start_time_prefilter = -1
            self.start_time_carbon_filter = -1
            self.start_time_gantry = -1
            self.start_time_compressor = -1
            self.start_ntp_synced = None

            self.write_usage_analytics(action="job_finished")

    def _event_laserhead_changed(self, event):
        """will be triggered if the laser head changed, refreshes the laserhead
        max dust factor that will be used for the new laser head.

        Returns:
        """
        self._logger.debug("Laserhead changed recalculate dust mapping")
        self._calculate_dust_mapping()

    def _event_fan_connected(self, event, payload):
        self._logger.debug("Fan connected, trigger migration of airfilter usage data.")
        self._migrate_airfilterfilter_data_if_necessary()

    def _set_time(self, job_duration):
        if job_duration is not None and job_duration > 0.0:

            # If it wasn't ntp synced at the beginning of the job, but it is now, we subtract the time shift
            if self.start_ntp_synced != self._plugin._time_ntp_synced:
                job_duration = self._calculate_ntp_fix_compensation(job_duration)

            dust_factor = self._calculate_dust_factor()
            self._set_job_time([self.TOTAL_KEY], self.start_time_total + job_duration)
            self._set_job_time(
                [self.LASER_HEAD_KEY, self._laser_head_serial],
                self.start_time_laser_head + job_duration * dust_factor,
            )
            self._set_job_time(
                [self.AIRFILTER_KEY, self._get_airfilter_serial(), self.PREFILTER_KEY],
                self.start_time_prefilter + job_duration * dust_factor,
            )
            self._set_job_time(
                [
                    self.AIRFILTER_KEY,
                    self._get_airfilter_serial(),
                    self.CARBON_FILTER_KEY,
                ],
                self.start_time_carbon_filter + job_duration * dust_factor,
            )
            self._set_job_time([self.GANTRY_KEY], self.start_time_gantry + job_duration)

            if self._plugin.compressor_handler.has_compressor():
                self._set_job_time(
                    [self.COMPRESSOR_KEY], self.start_time_compressor + job_duration
                )
            self._logger.debug(
                "job_duration actual: {:.1f}s, weighted: {:.1f}s, factor: {:.2f}".format(
                    job_duration, job_duration * dust_factor, dust_factor
                )
            )
            self._write_usage_data()

    def _calculate_ntp_fix_compensation(self, job_duration):
        job_duration_before = job_duration
        job_duration -= self._plugin._time_ntp_shift

        ntp_details = dict(
            time_shift=self._plugin._time_ntp_shift,
            job_duration_before=job_duration_before,
            job_duration_after=job_duration,
        )

        if job_duration < 0:
            job_duration = 0

        self._analytics_handler.add_job_ntp_sync_details(ntp_details)

        self._logger.info(
            "NTP shift fix - Job duration before: {}, after: {} --> shift: {}".format(
                ntp_details.get("time_shift"),
                ntp_details.get("job_duration_before"),
                ntp_details.get("job_duration_after"),
            )
        )

        return job_duration

    def _get_airfilter_usage_data(self, serial):
        """
        Returns the usage data for the airfilter with the given serial.

        Args:
            serial: Serial of the airfilter

        Returns:
            (dict): Usage data for the airfilter with the given serial
        """
        airfilter_usage_data = self._usage_data.get(self.AIRFILTER_KEY, {}).get(
            serial, {}
        )
        return airfilter_usage_data if airfilter_usage_data is not None else {}

    def _get_airfilter_prefilter_usage_data(self, serial=None):
        """
        Get the usage data for the prefilter of the airfilter with the given serial.

        Args:
            serial: Serial of the airfilter

        Returns:
            (dict): Usage data for the prefilter of the airfilter with the given serial
        """
        if serial is None:
            serial = self._get_airfilter_serial()
        return self._get_airfilter_usage_data(serial).get(self.PREFILTER_KEY, {})

    def _get_airfilter_carbon_filter_usage_data(self, serial=None):
        """
        Get the usage data for the carbon filter of the airfilter with the given serial.

        Args:
            serial: Serial of the airfilter

        Returns:
            (dict): Usage data for the carbon filter of the airfilter with the given serial
        """
        if serial is None:
            serial = self._get_airfilter_serial()
        return self._get_airfilter_usage_data(serial).get(self.CARBON_FILTER_KEY, {})

    def _set_job_time(self, component, job_time):
        """
        Set the job time for the given component.

        Args:
            component: Component to set the job time for
            job_time: job time in seconds

        Returns:
            None
        """
        element = self._usage_data
        if not isinstance(component, list):
            component = [component]
        for key in component:
            if key not in element:
                element[key] = {}
                self._logger.info("Created new usage data key: {}".format(key))
            element = element[key]
        element[self.JOB_TIME_KEY] = job_time
        self._logger.debug(
            "Set job time for component {} to {}".format(component, job_time)
        )

    def _get_job_time(self, usage_data):
        """
        Get the job time from the given usage data.

        Args:
            usage_data: Usage data to get the job time from

        Returns:
            int: job time in seconds, -1 if it could not be found
        """
        if self.JOB_TIME_KEY not in usage_data:
            self._logger.info("No job time found in usage data, returning -1")
            return -1
        return usage_data.get(self.JOB_TIME_KEY, -1)

    def _get_airfilter_serial(self):
        """
        Get the serial of the air filter. If the serial is unknown, the value 'no_serial' will be returned.

        Returns:
            str: serial of the air filter
        """
        serial = self._airfilter.serial
        if serial is None:
            self._logger.info("Air filter serial is unknown, using 'no_serial'")
            serial = self.UNKNOWN_SERIAL_KEY
        return serial

    def reset_prefilter_usage(self, serial):
        """
        Reset the prefilter usage data. This will set the job time of the prefilter to 0.

        Args:
            serial: serial of the air filter if None the UNKNOWN_SERIAL_KEY will be used

        Returns:
            None
        """
        if serial is None:
            serial = self.UNKNOWN_SERIAL_KEY
        self._set_job_time([self.AIRFILTER_KEY, serial, self.PREFILTER_KEY], 0)
        self.start_time_prefilter = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_prefilter")

    def reset_carbon_filter_usage(self, serial):
        """
        Reset the carbon filter usage data. This will set the job time of the carbon filter to 0.

        Args:
            serial: serial of the air filter if None the UNKNOWN_SERIAL_KEY will be used

        Returns:
            None
        """
        if serial is None:
            serial = self.UNKNOWN_SERIAL_KEY
        self._set_job_time(
            [self.AIRFILTER_KEY, serial, self.CARBON_FILTER_KEY],
            0,
        )
        self.start_time_prefilter = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_carbon_filter")

    def reset_laser_head_usage(self, serial):
        """
        Reset the laser head usage data. This will set the job time of the laser head to 0.

        Args:
            serial: serial of the laser head if None the UNKNOWN_SERIAL_KEY will be used

        Returns:
            None
        """
        if serial is None:
            serial = self.UNKNOWN_SERIAL_KEY
        self._set_job_time([self.LASER_HEAD_KEY, serial], 0)
        self.start_time_laser_head = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_laser_head")

    def reset_gantry_usage(self):
        self._set_job_time([self.GANTRY_KEY], 0)
        self.start_time_gantry = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_gantry")

    def get_review_given(self):
        return self._usage_data.get("review", {}).get("given", False)

    def set_review_given(self, migrated=False):
        if not self.get_review_given():
            self._usage_data["review"] = {
                "given": True,
                "ts": time.time(),
                "v": self._plugin_version,
                "migrated": migrated,
            }
            self._write_usage_data()

    def _log_usage_data(self, usage_data):
        self._logger.info(
            "USAGE DATA: prefilter={pre}, carbon_filter={carbon}, laser_head={lh}, gantry={gantry}, compressor={compressor}".format(
                pre=self._get_airfilter_prefilter_usage_data(),
                carbon=self._get_airfilter_carbon_filter_usage_data(),
                lh=usage_data[self.LASER_HEAD_KEY]["usage"],
                gantry=usage_data[self.GANTRY_KEY],
                compressor=usage_data[self.COMPRESSOR_KEY],
            )
        )

    def write_usage_analytics(self, action=None):
        try:
            usage_data = dict(
                total=self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY],
                prefilter=self.get_prefilter_usage(),
                carbon_filter=self.get_carbon_filter_usage,
                laser_head=dict(
                    usage=self._usage_data[self.LASER_HEAD_KEY][
                        self._laser_head_serial
                    ][self.JOB_TIME_KEY],
                    serial_number=self._laser_head_serial,
                ),
                gantry=self._usage_data[self.GANTRY_KEY][self.JOB_TIME_KEY],
                compressor=self._usage_data[self.COMPRESSOR_KEY][self.JOB_TIME_KEY],
                action=action,
            )

            self._analytics_handler.add_mrbeam_usage(usage_data)
            self._log_usage_data(usage_data)

        except KeyError as e:
            self._logger.info(
                "Could not write analytics for usage, missing key: {e}".format(e=e)
            )

    def get_prefilter_usage(self):
        """
        Get the usage of the prefilter in seconds.

        Returns:
            int: usage of the prefilter in seconds
        """
        return self._get_job_time(self._get_airfilter_prefilter_usage_data())

    def get_carbon_filter_usage(self):
        """
        Get the usage of the carbon filter in seconds.

        Returns:
            int: usage of the carbon filter in seconds
        """
        return self._get_job_time(self._get_airfilter_carbon_filter_usage_data())

    def get_laser_head_usage(self):
        if (
            self.LASER_HEAD_KEY in self._usage_data
            and self._laser_head_serial in self._usage_data[self.LASER_HEAD_KEY]
        ):
            return self._usage_data[self.LASER_HEAD_KEY][self._laser_head_serial][
                self.JOB_TIME_KEY
            ]
        else:
            return 0

    def get_gantry_usage(self):
        if self.GANTRY_KEY in self._usage_data:
            return self._usage_data[self.GANTRY_KEY][self.JOB_TIME_KEY]
        else:
            return 0

    def get_total_usage(self):
        if self.TOTAL_KEY in self._usage_data:
            return self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY]
        else:
            return 0

    def get_total_jobs(self):
        if self.SUCCESSFUL_JOBS_KEY in self._usage_data:
            return self._usage_data[self.SUCCESSFUL_JOBS_KEY]["count"]
        else:
            return 0

    def get_prefilter_lifespan(self):
        if self._plugin.is_heavy_duty_prefilter_enabled():
            return self.HEAVY_DUTY_PREFILTER_LIFESPAN
        else:
            return self.DEFAULT_PREFILTER_LIFESPAN

    def _load_usage_data(self):
        success = False
        recovery_try = False
        if os.path.isfile(self._storage_file):
            try:
                with self._file_lock:
                    with open(self._storage_file, "r") as stream:
                        data = yaml.safe_load(stream)
                if self._validate_data(data):
                    self._usage_data = data
                    success = True
                    self._write_usage_data(file=self._backup_file)
            except:
                self._logger.error(
                    "Can't read _storage_file file: %s", self._storage_file
                )

        if not success:
            self._logger.warn(
                "Trying to recover from _backup_file file: %s", self._backup_file
            )
            recovery_try = True
            try:
                with self._file_lock:
                    with open(self._backup_file, "r") as stream:
                        data = yaml.safe_load(stream)
                if self._validate_data(data):
                    data["restored"] = data["restored"] + 1 if "restored" in data else 1
                    self._usage_data = data
                    self._write_usage_data()
                    success = True
                    self._logger.info("Recovered from _backup_file file. Yayy!")
            except yaml.constructor.ConstructorError:
                try:
                    success = self._repair_backup_usage_data()
                except Exception:
                    self._logger.error("Repair of the _backup_file failed.")
            except OSError:
                self._logger.error("There is no _backup_file file.")
            except yaml.YAMLError:
                self._logger.error("There was a YAMLError with the _backup_file file.")
            except:
                self._logger.error("Can't read _backup_file file.")

        if not success:
            self._logger.warn("Resetting usage data. (marking as incomplete)")
            self._usage_data = self._get_usage_data_template()
            if recovery_try:
                self._write_usage_data()

    def _repair_backup_usage_data(self):
        """repairs a broken usage backup file, where the version is saved in
        unicode.

        Returns:
            boolean: successfull
        """
        success = False
        with self._file_lock:
            with open(self._backup_file, "r") as stream:
                data = yaml.load(stream)
        if self._validate_data(data):
            # checks if the version is saved in unicode and converts it into a string see SW-1269
            if isinstance(data["version"], unicode):
                data["version"] = unicodedata.normalize("NFKD", data["version"]).encode(
                    "ascii", "ignore"
                )
            data["restored"] = data["restored"] + 1 if "restored" in data else 1
            self._usage_data = data
            success = True
            self._write_usage_data()
            self._logger.info("Could repair _backup_file file. Yayy!")
        return success

    def _write_usage_data(self, file=None):
        self._usage_data["version"] = self._plugin_version
        self._usage_data["ts"] = time.time()
        self._usage_data["serial"] = self._device_serial
        file = self._storage_file if file is None else file
        try:
            with self._file_lock:
                with open(file, "w") as outfile:
                    yaml.safe_dump(self._usage_data, outfile, default_flow_style=False)
        except:
            self._logger.exception("Can't write file %s due to an exception: ", file)

    def _init_missing_usage_data(self):
        # Initialize prefilter in case it wasn't stored already --> From the total usage
        if self.PREFILTER_KEY not in self._usage_data:
            self._usage_data[self.PREFILTER_KEY] = {}
            self._usage_data[self.PREFILTER_KEY][self.COMPLETE_KEY] = self._usage_data[
                self.TOTAL_KEY
            ][self.COMPLETE_KEY]
            self._usage_data[self.PREFILTER_KEY][self.JOB_TIME_KEY] = self._usage_data[
                self.TOTAL_KEY
            ][self.JOB_TIME_KEY]
            self._logger.info(
                "Initializing prefilter usage time: {usage}".format(
                    usage=self.get_prefilter_usage()
                )
            )

        # Initialize carbon_filter in case it wasn't stored already --> From the total usage
        if self.CARBON_FILTER_KEY not in self._usage_data:
            self._usage_data[self.CARBON_FILTER_KEY] = {}
            self._usage_data[self.CARBON_FILTER_KEY][
                self.COMPLETE_KEY
            ] = self._usage_data[self.TOTAL_KEY][self.COMPLETE_KEY]
            self._usage_data[self.CARBON_FILTER_KEY][
                self.JOB_TIME_KEY
            ] = self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY]
            self._logger.info(
                "Initializing carbon filter usage time: {usage}".format(
                    usage=self._usage_data[self.CARBON_FILTER_KEY][self.JOB_TIME_KEY]
                )
            )

        # Initialize laser_head in case it wasn't stored already (+ first laser head) --> From the total usage
        if self.LASER_HEAD_KEY not in self._usage_data:
            self._usage_data[self.LASER_HEAD_KEY] = {}
            self._usage_data[self.LASER_HEAD_KEY][self._laser_head_serial] = {}
            self._usage_data[self.LASER_HEAD_KEY][self._laser_head_serial][
                self.COMPLETE_KEY
            ] = self._usage_data[self.TOTAL_KEY][self.COMPLETE_KEY]
            self._usage_data[self.LASER_HEAD_KEY][self._laser_head_serial][
                self.JOB_TIME_KEY
            ] = self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY]

        # Initialize new laser heads
        if self._laser_head_serial not in self._usage_data[self.LASER_HEAD_KEY]:
            num_serials_prev = len(self._usage_data[self.LASER_HEAD_KEY])

            # If it's the first lh with a serial, then read from 'no_serial' (if there is) or the total
            if num_serials_prev <= 1:
                if "no_serial" in self._usage_data[self.LASER_HEAD_KEY]:
                    self._usage_data[self.LASER_HEAD_KEY][
                        self._laser_head_serial
                    ] = dict(
                        complete=self._usage_data[self.LASER_HEAD_KEY][
                            self.UNKNOWN_SERIAL_KEY
                        ][self.COMPLETE_KEY],
                        job_time=self._usage_data[self.LASER_HEAD_KEY][
                            self.UNKNOWN_SERIAL_KEY
                        ][self.JOB_TIME_KEY],
                    )
                else:
                    self._usage_data[self.LASER_HEAD_KEY][
                        self._laser_head_serial
                    ] = dict(
                        complete=self._usage_data[self.TOTAL_KEY][self.COMPLETE_KEY],
                        job_time=self._usage_data[self.TOTAL_KEY][self.JOB_TIME_KEY],
                    )
            # Otherwise initialize to 0
            else:
                self._usage_data[self.LASER_HEAD_KEY][self._laser_head_serial] = dict(
                    complete=True,
                    job_time=0,
                )

            self._logger.info(
                "Initializing laser head ({lh}) usage time: {usage}".format(
                    lh=self._laser_head_serial,
                    usage=self._usage_data[self.LASER_HEAD_KEY][
                        self._laser_head_serial
                    ][self.JOB_TIME_KEY],
                )
            )

        # Initialize gantry in case it wasn't stored already --> From the total usage
        if self.GANTRY_KEY not in self._usage_data:
            self._usage_data[self.GANTRY_KEY] = {}
            self._usage_data[self.GANTRY_KEY][self.COMPLETE_KEY] = self._usage_data[
                self.TOTAL_KEY
            ][self.COMPLETE_KEY]
            self._usage_data[self.GANTRY_KEY][self.JOB_TIME_KEY] = self._usage_data[
                self.TOTAL_KEY
            ][self.JOB_TIME_KEY]
            self._logger.info(
                "Initializing gantry usage time: {usage}".format(
                    usage=self._usage_data[self.GANTRY_KEY][self.JOB_TIME_KEY]
                )
            )

        # Initialize compressor in case it wasn't stored already --> To 0
        if self.COMPRESSOR_KEY not in self._usage_data:
            self._usage_data[self.COMPRESSOR_KEY] = {}
            self._usage_data[self.COMPRESSOR_KEY][
                self.COMPLETE_KEY
            ] = self._plugin.isFirstRun()
            self._usage_data[self.COMPRESSOR_KEY][self.JOB_TIME_KEY] = 0
            self._logger.info(
                "Initializing compressor usage time: {usage}".format(
                    usage=self._usage_data[self.COMPRESSOR_KEY][self.JOB_TIME_KEY]
                )
            )

        if self.SUCCESSFUL_JOBS_KEY not in self._usage_data:
            self._usage_data[self.SUCCESSFUL_JOBS_KEY] = {}
            self._usage_data[self.SUCCESSFUL_JOBS_KEY]["count"] = 0
            self._usage_data[self.SUCCESSFUL_JOBS_KEY][
                self.COMPLETE_KEY
            ] = self._plugin.isFirstRun()

        self._write_usage_data()

    def _get_usage_data_template(self):
        return {
            self.TOTAL_KEY: {
                self.JOB_TIME_KEY: 0.0,
                self.COMPLETE_KEY: self._plugin.isFirstRun(),
            },
            self.SUCCESSFUL_JOBS_KEY: {
                "count": 0,
                self.COMPLETE_KEY: self._plugin.isFirstRun(),
            },
            self.LASER_HEAD_KEY: {
                self.UNKNOWN_SERIAL_KEY: {
                    self.JOB_TIME_KEY: 0.0,
                    self.COMPLETE_KEY: self._plugin.isFirstRun(),
                }
            },
            self.AIRFILTER_KEY: {
                self.UNKNOWN_SERIAL_KEY: {
                    self.PREFILTER_KEY: {
                        self.JOB_TIME_KEY: 0.0,
                        self.COMPLETE_KEY: self._plugin.isFirstRun(),
                    },
                    self.CARBON_FILTER_KEY: {
                        self.JOB_TIME_KEY: 0.0,
                        self.COMPLETE_KEY: self._plugin.isFirstRun(),
                    },
                }
            },
            self.GANTRY_KEY: {
                self.JOB_TIME_KEY: 0.0,
                self.COMPLETE_KEY: self._plugin.isFirstRun(),
            },
            self.COMPRESSOR_KEY: {
                self.JOB_TIME_KEY: 0.0,
                self.COMPLETE_KEY: self._plugin.isFirstRun(),
            },
            "first_write": time.time(),
            "restored": 0,
            "version": "0.0.0",
            "ts": 0.0,
            "serial": self._device_serial,
        }

    def _validate_data(self, data):
        return (
            data is not None
            and len(data) > 0
            and "version" in data
            and "ts" in data
            and "serial" in data
            and self.TOTAL_KEY in data
            and len(data[self.TOTAL_KEY]) > 0
            and self.JOB_TIME_KEY in data[self.TOTAL_KEY]
        )

    def get_duration_humanreadable(self, seconds):
        seconds = seconds if seconds else 0
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def _update_last_dust_value(self):
        new_value = self._dust_manager.get_mean_job_dust()
        if new_value is not None:
            self._last_dust_value = new_value

    def _calculate_dust_factor(self):
        dust_factor = 1

        if self._last_dust_value is not None:
            dust_factor = round(
                self._dust_mapping_m * self._last_dust_value + self._dust_mapping_b, 2
            )
            if dust_factor < self.MIN_DUST_FACTOR:
                dust_factor = self.MIN_DUST_FACTOR

        return dust_factor

    def _migrate_airfilterfilter_data_if_necessary(self):
        """
        Trigger the migration of the old airfilter data to the new structure if necessary.

        Returns:
            None
        """
        if (
            self._usage_data.get(self.CARBON_FILTER_KEY) is not None
            and self._usage_data.get(self.PREFILTER_KEY) is not None
        ):
            migration_timer = threading.Timer(
                self.MIGRATION_WAIT, self._migrate_old_airfilter_structure_to_new
            )
            migration_timer.daemon = True
            migration_timer.name = "usage_do_migration_timer"
            migration_timer.start()

    def _migrate_old_airfilter_structure_to_new(self):
        """
        Migrate the job time from the old format to the new one for AirFilter2

        Returns:
            None
        """
        # get data from old structure
        if self._airfilter.model_id not in AirFilter.AIRFILTER3_MODELS:
            serial = self._get_airfilter_serial()
        else:
            serial = self.UNKNOWN_SERIAL_KEY
        prefilter = self._usage_data.get(self.PREFILTER_KEY)
        carbon_filter = self._usage_data.get(self.CARBON_FILTER_KEY)

        # copy to new structure
        self._usage_data = dict_merge(
            self._usage_data,
            {
                self.AIRFILTER_KEY: {
                    serial: {
                        self.PREFILTER_KEY: prefilter,
                        self.CARBON_FILTER_KEY: carbon_filter,
                    }
                }
            },
        )

        # remove from old structure if serial is known
        self._usage_data.pop(self.CARBON_FILTER_KEY, None)
        self._usage_data.pop(self.PREFILTER_KEY, None)

        self._write_usage_data()

        self._logger.info(
            "Migrated AF2 filter stage job time (pre:{} carbon:{}) to serial: {}".format(
                prefilter, carbon_filter, serial
            )
        )
