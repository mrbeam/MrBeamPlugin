import os
import time
import unicodedata

import yaml

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
    MAX_DUST_FACTOR = 2.0
    MIN_DUST_FACTOR = 0.5
    MAX_DUST_VALUE = 0.5
    MIN_DUST_VALUE = 0.2

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.usage")
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._settings = plugin._settings
        self._plugin_version = plugin.get_plugin_version()
        self._device_serial = plugin.getSerialNum()

        self.start_time_total = -1
        self.start_time_laser_head = -1
        self.start_time_prefilter = -1
        self.start_time_carbon_filter = -1
        self.start_time_gantry = -1
        self.start_time_compressor = -1
        self.start_ntp_synced = None

        self._last_dust_value = None
        self._dust_mapping_m = (self.MAX_DUST_FACTOR - self.MIN_DUST_FACTOR) / (
            self.MAX_DUST_VALUE - self.MIN_DUST_VALUE
        )
        self._dust_mapping_b = (
            self.MIN_DUST_FACTOR - self._dust_mapping_m * self.MIN_DUST_VALUE
        )

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

        self._usage_data = None
        self._load_usage_data()

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._analytics_handler = self._plugin.analytics_handler
        self._laserhead_handler = self._plugin.laserhead_handler
        self._dust_manager = self._plugin.dust_manager

        # Read laser head. If it's None, use 'no_serial'
        self._lh = self._laserhead_handler.get_current_used_lh_data()
        if self._lh["serial"]:
            self._laser_head_serial = self._lh["serial"]
        else:
            self._laser_head_serial = "no_serial"

        self._init_missing_usage_data()
        self.log_usage()

        self._subscribe()

    def log_usage(self):
        self._logger.info(
            "Usage: total_usage: {}, pre-filter: {}, main filter: {}, current laser head: {}, mechanics: {}, compressor: {} - {}".format(
                self.get_duration_humanreadable(self._usage_data["total"]["job_time"]),
                self.get_duration_humanreadable(
                    self._usage_data["prefilter"]["job_time"]
                ),
                self.get_duration_humanreadable(
                    self._usage_data["carbon_filter"]["job_time"]
                ),
                self.get_duration_humanreadable(
                    self._usage_data["laser_head"][self._laser_head_serial]["job_time"]
                ),
                self.get_duration_humanreadable(
                    self._usage_data["compressor"]["job_time"]
                ),
                self.get_duration_humanreadable(self._usage_data["gantry"]["job_time"]),
                self._usage_data,
            )
        )

    def _subscribe(self):
        self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self.event_start)
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_PAUSED, self.event_write
        )  # cooling breaks also send a regular pause event
        self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.event_stop)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.event_stop)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.event_stop)
        self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self.event_write)
        self._event_bus.subscribe(
            MrBeamEvents.LASER_HEAD_READ, self.event_laser_head_read
        )

    def event_laser_head_read(self, event, payload):
        # Update laser head info if necessary --> Only update if there is a serial number different than the previous
        if payload["serial"] and self._lh["serial"] != payload["serial"]:
            self._lh = self._laserhead_handler.get_current_used_lh_data()
            self._laser_head_serial = self._lh["serial"]
            self._init_missing_usage_data()

    def event_start(self, event, payload):
        self._load_usage_data()
        self.start_time_total = self._usage_data["total"]["job_time"]
        self.start_time_prefilter = self._usage_data["prefilter"]["job_time"]
        self.start_time_carbon_filter = self._usage_data["carbon_filter"]["job_time"]
        self.start_time_laser_head = self._usage_data["laser_head"][
            self._laser_head_serial
        ]["job_time"]
        self.start_time_gantry = self._usage_data["gantry"]["job_time"]
        self.start_time_compressor = self._usage_data["compressor"]["job_time"]
        self.start_ntp_synced = self._plugin._time_ntp_synced

        self._last_dust_value = None

    def event_write(self, event, payload):
        if self.start_time_total >= 0:
            self._update_last_dust_value()
            self._set_time(payload["time"])

    def event_stop(self, event, payload):
        if event == OctoPrintEvents.PRINT_DONE:
            self._usage_data["succ_jobs"]["count"] = (
                self._usage_data["succ_jobs"]["count"] + 1
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

    def _set_time(self, job_duration):
        if job_duration is not None and job_duration > 0.0:

            # If it wasn't ntp synced at the beginning of the job, but it is now, we subtract the time shift
            if self.start_ntp_synced != self._plugin._time_ntp_synced:
                job_duration = self._calculate_ntp_fix_compensation(job_duration)

            dust_factor = self._calculate_dust_factor()
            self._usage_data["total"]["job_time"] = self.start_time_total + job_duration
            self._usage_data["laser_head"][self._laser_head_serial]["job_time"] = (
                self.start_time_laser_head + job_duration * dust_factor
            )
            self._usage_data["prefilter"]["job_time"] = (
                self.start_time_prefilter + job_duration * dust_factor
            )
            self._usage_data["carbon_filter"]["job_time"] = (
                self.start_time_carbon_filter + job_duration * dust_factor
            )
            self._usage_data["gantry"]["job_time"] = (
                self.start_time_gantry + job_duration
            )

            if self._plugin.compressor_handler.has_compressor():
                self._usage_data["compressor"]["job_time"] = (
                    self.start_time_compressor + job_duration
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

    def reset_prefilter_usage(self):
        self._usage_data["prefilter"]["job_time"] = 0
        self.start_time_prefilter = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_prefilter")

    def reset_carbon_filter_usage(self):
        self._usage_data["carbon_filter"]["job_time"] = 0
        self.start_time_prefilter = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_carbon_filter")

    def reset_laser_head_usage(self):
        self._usage_data["laser_head"][self._laser_head_serial]["job_time"] = 0
        self.start_time_laser_head = -1
        self._write_usage_data()
        self.write_usage_analytics(action="reset_laser_head")

    def reset_gantry_usage(self):
        self._usage_data["gantry"]["job_time"] = 0
        self.start_time_prefilter = -1
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
                pre=usage_data["prefilter"],
                carbon=usage_data["carbon_filter"],
                lh=usage_data["laser_head"]["usage"],
                gantry=usage_data["gantry"],
                compressor=usage_data["compressor"],
            )
        )

    def write_usage_analytics(self, action=None):
        try:
            usage_data = dict(
                total=self._usage_data["total"]["job_time"],
                prefilter=self._usage_data["prefilter"]["job_time"],
                carbon_filter=self._usage_data["carbon_filter"]["job_time"],
                laser_head=dict(
                    usage=self._usage_data["laser_head"][self._laser_head_serial][
                        "job_time"
                    ],
                    serial_number=self._laser_head_serial,
                ),
                gantry=self._usage_data["gantry"]["job_time"],
                compressor=self._usage_data["compressor"]["job_time"],
                action=action,
            )

            self._analytics_handler.add_mrbeam_usage(usage_data)
            self._log_usage_data(usage_data)

        except KeyError as e:
            self._logger.info(
                "Could not write analytics for usage, missing key: {e}".format(e=e)
            )

    def get_prefilter_usage(self):
        if "prefilter" in self._usage_data:
            return self._usage_data["prefilter"]["job_time"]
        else:
            return 0

    def get_carbon_filter_usage(self):
        if "carbon_filter" in self._usage_data:
            return self._usage_data["carbon_filter"]["job_time"]
        else:
            return 0

    def get_laser_head_usage(self):
        if (
            "laser_head" in self._usage_data
            and self._laser_head_serial in self._usage_data["laser_head"]
        ):
            return self._usage_data["laser_head"][self._laser_head_serial]["job_time"]
        else:
            return 0

    def get_gantry_usage(self):
        if "gantry" in self._usage_data:
            return self._usage_data["gantry"]["job_time"]
        else:
            return 0

    def get_total_usage(self):
        if "total" in self._usage_data:
            return self._usage_data["total"]["job_time"]
        else:
            return 0

    def get_total_jobs(self):
        if "succ_jobs" in self._usage_data:
            return self._usage_data["succ_jobs"]["count"]
        else:
            return 0

    def _load_usage_data(self):
        success = False
        recovery_try = False
        if os.path.isfile(self._storage_file):
            try:
                data = None
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
                with open(self._backup_file, "r") as stream:
                    data = yaml.safe_load(stream)
                if self._validate_data(data):
                    data["restored"] = (
                        data["restored"] + 1 if "restored" in data else 1
                    )
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
        """
        repairs a broken usage backup file, where the version is saved in unicode

        Returns:
            boolean: successfull
        """
        success = False
        with open(self._backup_file, "r") as stream:
            data = yaml.load(stream)
        if self._validate_data(data):
            #checks if the version is saved in unicode and converts it into a string see SW-1269
            if isinstance(data["version"], unicode):
                data["version"] = unicodedata.normalize('NFKD', data["version"]).encode('ascii', 'ignore')
            data["restored"] = (
                data["restored"] + 1 if "restored" in data else 1
            )
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
            with open(file, "w") as outfile:
                yaml.safe_dump(self._usage_data, outfile, default_flow_style=False)
        except:
            self._logger.exception("Can't write file %s due to an exception: ", file)

    def _init_missing_usage_data(self):
        # Initialize prefilter in case it wasn't stored already --> From the total usage
        if "prefilter" not in self._usage_data:
            self._usage_data["prefilter"] = {}
            self._usage_data["prefilter"]["complete"] = self._usage_data["total"][
                "complete"
            ]
            self._usage_data["prefilter"]["job_time"] = self._usage_data["total"][
                "job_time"
            ]
            self._logger.info(
                "Initializing prefilter usage time: {usage}".format(
                    usage=self._usage_data["prefilter"]["job_time"]
                )
            )

        # Initialize carbon_filter in case it wasn't stored already --> From the total usage
        if "carbon_filter" not in self._usage_data:
            self._usage_data["carbon_filter"] = {}
            self._usage_data["carbon_filter"]["complete"] = self._usage_data["total"][
                "complete"
            ]
            self._usage_data["carbon_filter"]["job_time"] = self._usage_data["total"][
                "job_time"
            ]
            self._logger.info(
                "Initializing carbon filter usage time: {usage}".format(
                    usage=self._usage_data["carbon_filter"]["job_time"]
                )
            )

        # Initialize laser_head in case it wasn't stored already (+ first laser head) --> From the total usage
        if "laser_head" not in self._usage_data:
            self._usage_data["laser_head"] = {}
            self._usage_data["laser_head"][self._laser_head_serial] = {}
            self._usage_data["laser_head"][self._laser_head_serial][
                "complete"
            ] = self._usage_data["total"]["complete"]
            self._usage_data["laser_head"][self._laser_head_serial][
                "job_time"
            ] = self._usage_data["total"]["job_time"]

        # Initialize new laser heads
        if self._laser_head_serial not in self._usage_data["laser_head"]:
            num_serials_prev = len(self._usage_data["laser_head"])

            # If it's the first lh with a serial, then read from 'no_serial' (if there is) or the total
            if num_serials_prev <= 1:
                if "no_serial" in self._usage_data["laser_head"]:
                    self._usage_data["laser_head"][self._laser_head_serial] = dict(
                        complete=self._usage_data["laser_head"]["no_serial"][
                            "complete"
                        ],
                        job_time=self._usage_data["laser_head"]["no_serial"][
                            "job_time"
                        ],
                    )
                else:
                    self._usage_data["laser_head"][self._laser_head_serial] = dict(
                        complete=self._usage_data["total"]["complete"],
                        job_time=self._usage_data["total"]["job_time"],
                    )
            # Otherwise initialize to 0
            else:
                self._usage_data["laser_head"][self._laser_head_serial] = dict(
                    complete=True,
                    job_time=0,
                )

            self._logger.info(
                "Initializing laser head ({lh}) usage time: {usage}".format(
                    lh=self._laser_head_serial,
                    usage=self._usage_data["laser_head"][self._laser_head_serial][
                        "job_time"
                    ],
                )
            )

        # Initialize gantry in case it wasn't stored already --> From the total usage
        if "gantry" not in self._usage_data:
            self._usage_data["gantry"] = {}
            self._usage_data["gantry"]["complete"] = self._usage_data["total"][
                "complete"
            ]
            self._usage_data["gantry"]["job_time"] = self._usage_data["total"][
                "job_time"
            ]
            self._logger.info(
                "Initializing gantry usage time: {usage}".format(
                    usage=self._usage_data["gantry"]["job_time"]
                )
            )

        # Initialize compressor in case it wasn't stored already --> To 0
        if "compressor" not in self._usage_data:
            self._usage_data["compressor"] = {}
            self._usage_data["compressor"]["complete"] = self._plugin.isFirstRun()
            self._usage_data["compressor"]["job_time"] = 0
            self._logger.info(
                "Initializing compressor usage time: {usage}".format(
                    usage=self._usage_data["compressor"]["job_time"]
                )
            )

        if "succ_jobs" not in self._usage_data:
            self._usage_data["succ_jobs"] = {}
            self._usage_data["succ_jobs"]["count"] = 0
            self._usage_data["succ_jobs"]["complete"] = self._plugin.isFirstRun()

        self._write_usage_data()

    def _get_usage_data_template(self):
        return {
            "total": {
                "job_time": 0.0,
                "complete": self._plugin.isFirstRun(),
            },
            "succ_jobs": {
                "count": 0,
                "complete": self._plugin.isFirstRun(),
            },
            "prefilter": {
                "job_time": 0.0,
                "complete": self._plugin.isFirstRun(),
            },
            "laser_head": {
                "no_serial": {
                    "job_time": 0.0,
                    "complete": self._plugin.isFirstRun(),
                }
            },
            "carbon_filter": {
                "job_time": 0.0,
                "complete": self._plugin.isFirstRun(),
            },
            "gantry": {
                "job_time": 0.0,
                "complete": self._plugin.isFirstRun(),
            },
            "compressor": {
                "job_time": 0.0,
                "complete": self._plugin.isFirstRun(),
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
            and "total" in data
            and len(data["total"]) > 0
            and "job_time" in data["total"]
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
