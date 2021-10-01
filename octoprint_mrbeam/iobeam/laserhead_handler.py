import os
import yaml
import re
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None


def laserheadHandler(plugin):
    global _instance
    if _instance is None:
        _instance = LaserheadHandler(plugin)
    return _instance


class LaserheadHandler(object):
    LASER_POWER_GOAL_DEFAULT = 950
    LASER_POWER_GOAL_MAX = 1300
    LASERHEAD_SERIAL_REGEXP = re.compile("^[0-9a-f-]{36}$")
    _LASERHEAD_MODEL_STRING_MAP = {
        "0": '0',  # dreamcut, mrbeam2 and mrbeam laserheads
        "1": 'S',  # dreamcut[S] laserhead
    }

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.laserhead")
        self._plugin = plugin
        self._settings = plugin._settings
        self._event_bus = plugin._event_bus
        self._plugin_version = plugin.get_plugin_version()

        self._lh_cache = {}
        self._last_used_lh_serial = None
        self._last_used_lh_model_id = None
        self._correction_settings = {}
        self._laser_heads_file = os.path.join(
            self._settings.getBaseFolder("base"),
            self._settings.get(["laser_heads", "filename"]),
        )
        self._load_laser_heads_file()  # Loads correction_settings, last_used_lh_serial and lh_cache

        self._current_used_lh_serial = self._last_used_lh_serial
        self._current_used_lh_model_id = self._last_used_lh_model_id

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    @property
    def _current_used_lh_model_string(self):
        if str(self._current_used_lh_model_id) in self._LASERHEAD_MODEL_STRING_MAP:
            return self._LASERHEAD_MODEL_STRING_MAP.get(str(self._current_used_lh_model_id))
        else:
            raise ValueError("Unknown laserhead model ID {!r}".format(self._current_used_lh_model_id))



    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._analytics_handler = self._plugin.analytics_handler

    def _get_lh_model(self, lh_data):
        try:
            read_model = lh_data["head"]["model"]
            if str(read_model) in self._LASERHEAD_MODEL_STRING_MAP:
                model = read_model
            else:
                model = 0
                self._logger.warn(
                    "No valid Laserhead model found, assume it is model 0"
                )
            return model
        except Exception as e:
            self._logger.error(
                "Error for Laserhead model, no model found in laserhead data: {}".format(e)
            )

    def set_current_used_lh_data(self, lh_data):
        try:
            if self._valid_lh_data(lh_data):
                self._logger.info("Laserhead: %s", lh_data)
                self._current_used_lh_serial = lh_data["main"]["serial"]
                self._current_used_lh_model_id = self._get_lh_model(lh_data)
                # fmt: off
                if (self._current_used_lh_serial != self._last_used_lh_serial) and self._last_used_lh_model_id is not None:
                    # fmt: on
                    if self._current_used_lh_model_id == 1:
                        self._settings.set_boolean(["laserheadChanged"], True)
                        self._settings.save()
                    self._logger.info(
                        "Laserhead changed: s/n:%s model:%s -> s/n:%s model:%s",
                        self._last_used_lh_serial,
                        self._last_used_lh_model_id,
                        self._current_used_lh_serial,
                        self._current_used_lh_model_id,
                    )
                self._write_lh_data_to_cache(lh_data)

                self._calculate_and_write_correction_factor()

                self._analytics_handler.add_laserhead_info()
                self._write_laser_heads_file()
                self._plugin.fire_event(
                    MrBeamEvents.LASER_HEAD_READ,
                    dict(
                        serial=self._current_used_lh_serial,
                        model=self._current_used_lh_model_id,
                    ),
                )

            # BACKWARD_COMPATIBILITY: This is for detecting mrb_hw_info v0.0.20
            elif self._valid_lh_data_backwards_compatibility(lh_data):
                self._logger.info("Laserhead (< v0.0.21): %s", lh_data)
                self._logger.warning(
                    "Received old laser head data from iobeam.", analytics=True
                )

            elif lh_data == {}:
                self._logger.warn("Received empty laser head data from iobeam.")

            else:
                if lh_data.get("main", {}).get("serial") is None:
                    self._logger.exception(
                        "Received invalid laser head data from iobeam - no serial number. Laser head dataset: {}".format(
                            lh_data
                        ),
                        analytics="received-no-lh-data",
                    )
                elif (
                    not lh_data.get("power_calibrations")
                    or not len(lh_data["power_calibrations"]) > 0
                    or not lh_data["power_calibrations"][-1].get("power_65")
                    or not lh_data["power_calibrations"][-1].get("power_75")
                    or not lh_data["power_calibrations"][-1].get("power_85")
                ):
                    self._logger.exception(
                        "Received invalid laser head data from iobeam - invalid power calibrations data: {}".format(
                            lh_data.get("power_calibrations", [])
                        ),
                        analytics="invalid-power-calibration",
                    )
                else:
                    self._logger.exception(
                        "Received invalid laser head data from iobeam {}".format(
                            lh_data
                        ),
                        analytics="received-invalid-lh-data",
                    )
        except Exception as e:
            self._logger.exception(
                "Exception during set_current_used_lh_data: {}".format(e)
            )

    def _valid_lh_data(self, lh_data):
        try:
            if (
                lh_data.get("main")
                and lh_data["main"].get("serial")
                and lh_data["head"].get("model") is not None
                and lh_data.get("power_calibrations")
                and len(lh_data["power_calibrations"]) > 0
                and lh_data["power_calibrations"][-1].get("power_65")
                and lh_data["power_calibrations"][-1].get("power_75")
                and lh_data["power_calibrations"][-1].get("power_85")
            ):
                return True
            else:
                return False
        except Exception as e:
            self._logger.exception("Exception during _valid_lh_data: {}".format(e))
            return False

    def _valid_lh_data_backwards_compatibility(self, lh_data):
        try:
            if (
                lh_data.get("serial")
                and lh_data.get("calibration_data")
                and len(lh_data["calibration_data"]) > 0
                and lh_data["calibration_data"][-1].get("power_65")
                and lh_data["calibration_data"][-1].get("power_75")
                and lh_data["calibration_data"][-1].get("power_85")
            ):
                return True
            else:
                return False
        except Exception as e:
            self._logger.exception("Exception during _valid_lh_data: {}".format(e))
            return False

    def _write_lh_data_to_cache(self, lh_data):
        self._lh_cache[self._current_used_lh_serial] = lh_data

    def get_current_used_lh_data(self):
        if self._current_used_lh_serial:
            data = dict(
                serial=self._current_used_lh_serial,
                model=self._current_used_lh_model_string,
                info=self._lh_cache[self._current_used_lh_serial],
            )
        else:
            data = dict(
                serial=None,
                model=None,
                info=dict(
                    correction_factor=1,
                ),
            )
        return data

    def get_current_used_lh_power(self):
        lh = self.get_current_used_lh_data()["info"]
        if lh and lh["power_calibrations"]:
            return lh["power_calibrations"][-1]

    def get_correction_settings(self):
        settings = self._correction_settings
        if "gcode_intensity_limit" not in settings:
            settings["gcode_intensity_limit"] = None
        if "correction_factor_override" not in settings:
            settings["correction_factor_override"] = None
        if "correction_enabled" not in settings:
            settings["correction_enabled"] = True

        return self._correction_settings

    def get_current_used_lh_model_id(self):
        return self._current_used_lh_model_id

    def _validate_lh_serial(self, serial):
        try:
            return bool(self.LASERHEAD_SERIAL_REGEXP.match(serial))
        except Exception as e:
            self._logger.exception(
                "_validate_lh_serial() Failed to validate serial due to exception. Serial: {serial} e:{e}".format(serial=serial, e=e),
                serial,
            )
            return False

    def _calculate_and_write_correction_factor(self):
        correction_factor = self._calculate_power_correction_factor()
        self._lh_cache[self._current_used_lh_serial][
            "correction_factor"
        ] = correction_factor
        self._lh_cache[self._current_used_lh_serial][
            "mrbeam_plugin_version"
        ] = self._plugin_version

    def _calculate_power_correction_factor(self):
        power_calibration = self.get_current_used_lh_power()
        p_65 = None
        p_75 = None
        p_85 = None
        target_power = self.LASER_POWER_GOAL_DEFAULT
        if power_calibration:
            p_65 = power_calibration.get("power_65")
            p_75 = power_calibration.get("power_75")
            p_85 = power_calibration.get("power_85")
            target_power = power_calibration.get(
                "target_power", self.LASER_POWER_GOAL_DEFAULT
            )

            # laserhead model S fix for correction factor
            # TODO fix this GOAL_MAX problem for all laser heads in a separate issue SW-394
            if self._current_used_lh_model_id == 1:
                if target_power < 0 or target_power >= p_85:
                    self._logger.warn(
                        "Laserhead target_power ({target}) over p_85 ({p_85}) => target_power will be set to GOAL_DEFAULT ({default}) for the calculation of the correction factor".format(
                            target=target_power,
                            p_85=p_85,
                            default=self.LASER_POWER_GOAL_DEFAULT,
                        )
                    )
                    target_power = self.LASER_POWER_GOAL_DEFAULT
            else:
                if target_power < 0 or target_power >= self.LASER_POWER_GOAL_MAX:
                    self._logger.warn(
                        "Laserhead target_power ({target}) over LASER_POWER_MAX ({max}) => target_power will be set to GOAL_DEFAULT ({default}) for the calculation of the correction factor".format(
                            target=target_power,
                            max=self.LASER_POWER_GOAL_MAX,
                            default=self.LASER_POWER_GOAL_DEFAULT,
                        )
                    )
                    target_power = self.LASER_POWER_GOAL_DEFAULT

        correction_factor = 1

        if p_65 and p_75 and p_85:
            if p_65 < target_power < p_75:
                step_difference = float(p_75 - p_65)
                goal_difference = target_power - p_65
                new_intensity = goal_difference * (75 - 65) / step_difference + 65
                correction_factor = new_intensity / 65.0

            elif p_75 < target_power < p_85:
                step_difference = float(p_85 - p_75)
                goal_difference = target_power - p_75
                new_intensity = goal_difference * (85 - 75) / step_difference + 75
                correction_factor = new_intensity / 65.0
            else:
                self._logger.warn(
                    "Laserhead target power not in valid range => correction_factor will be set to 1"
                )

        else:
            self._logger.info(
                "Insufficient data for correction factor. Default factor: {cf}".format(
                    cf=correction_factor
                )
            )

        self._logger.info(
            "Laserhead info - serial={serial}, p_65={p65}, p_75={p75}, p_85={p85}, correction_factor={cf}, target_power={tp}".format(
                serial=self._current_used_lh_serial,
                p65=p_65,
                p75=p_75,
                p85=p_85,
                cf=correction_factor,
                tp=target_power,
            )
        )

        return correction_factor

    def _load_laser_heads_file(self):
        if os.path.isfile(self._laser_heads_file):
            self._logger.info("Loading laser_heads.yaml...")
            try:
                with open(self._laser_heads_file, "r") as stream:
                    data = yaml.safe_load(stream)

                if data:
                    self._lh_cache = data.get("laser_heads")
                    self._last_used_lh_serial = data.get("last_used_lh_serial")
                    self._last_used_lh_model_id = data.get("last_used_lh_model_id")
                    self._correction_settings = data.get("correction_settings")
            except IOError:
                self._logger.exception(
                    "Can't read _laser_heads_file file: %s", self._laser_heads_file
                )
        else:
            self._logger.warn("The laser_heads.yaml file can't be found at this location {}".format(self._laser_heads_file))

    def _write_laser_heads_file(self, file=None):
        self._logger.info("Writing to laser_heads.yaml...")

        data = dict(
            laser_heads=self._lh_cache,
            correction_settings=self._correction_settings,
            last_used_lh_serial=self._current_used_lh_serial,
            last_used_lh_model_id=self._current_used_lh_model_id,
        )
        file = self._laser_heads_file if file is None else file
        try:
            with open(file, "w") as outfile:
                yaml.safe_dump(data, outfile, default_flow_style=False)
        except IOError:
            self._logger.exception("Can't write file %s due to an exception: ", file)
