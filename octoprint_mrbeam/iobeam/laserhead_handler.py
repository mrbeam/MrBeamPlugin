import os
import yaml
import re
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamValueEvents

LASERHEAD_MAX_TEMP_FALLBACK = 55.0
LASERHEAD_MAX_DUST_FACTOR_FALLBACK = 3.0 # selected the highest factor

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
        self._iobeam = None
        self._laserhead_properties = {}

        self._lh_cache = {}
        self._last_used_lh_serial = None
        self._last_used_lh_model = None
        self._last_used_lh_model_id = None
        self._correction_settings = {}
        self._laser_heads_file = os.path.join(
            self._settings.getBaseFolder("base"),
            self._settings.get(["laser_heads", "filename"]),
        )
        self._load_laser_heads_file()  # Loads correction_settings, last_used_lh_serial and lh_cache

        self._current_used_lh_serial = self._last_used_lh_serial
        self._current_used_lh_model = self._last_used_lh_model
        self._current_used_lh_model_id = self._last_used_lh_model_id

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    @property
    def _current_used_lh_model_string(self):
        """
        Returns the laserhead model name

        Returns:
            str: laserhead model or None if Model name is not found
        """
        laser_head_model_str_list = [v for (k, v) in self._LASERHEAD_MODEL_STRING_MAP.items()
                                     if ((v == str(self._current_used_lh_model)) or
                                         (k == str(self._current_used_lh_model_id)))]
        try:
            return laser_head_model_str_list.pop(0)
        except IndexError:
            self._logger.error("Unknown laserhead model,  name: {} ID: {}".format(
                self._current_used_lh_model, self._current_used_lh_model_id))
            return str(None)

    def _on_mrbeam_plugin_initialized(self, event, payload):
        # the following params are Not used for the time being
        # TODO check later
        _ = event
        _ = payload
        self._analytics_handler = self._plugin.analytics_handler
        self._iobeam = self._plugin.iobeam

    def _get_lh_model(self, lh_data):
        try:
            read_model = lh_data["head"]["model"]
            if str(read_model) in self._LASERHEAD_MODEL_STRING_MAP:
                model = read_model
            else:
                model = 0
                self._logger.warn(
                    "Laserhead model received is not valid, Model: {} assume default model 0".format(read_model)
                )
            return model
        except Exception as e:
            self._logger.error(
                "Error for Laserhead model, no model found in laserhead data: {}".format(e)
            )

    def set_current_used_lh_data(self, lh_data):
        laser_head_model_changed = False

        try:
            if self._valid_lh_data(lh_data):
                self._current_used_lh_serial = lh_data["main"]["serial"]
                self._current_used_lh_model_id = self._get_lh_model(lh_data)
                self._current_used_lh_model = self._LASERHEAD_MODEL_STRING_MAP[str(self._current_used_lh_model_id)]
                # fmt: off
                if(self._current_used_lh_model_id != self._last_used_lh_model_id) \
                        and self._current_used_lh_model_id is not None:
                    laser_head_model_changed = True

                if (self._current_used_lh_serial != self._last_used_lh_serial) and self._last_used_lh_model_id is not None:
                    # fmt: on
                    if self._current_used_lh_model_id == 1:
                        self._settings.set_boolean(["laserheadChanged"], True)
                        self._settings.save()
                    self._logger.info(
                        "laserhead_handler: Laserhead changed: s/n:%s model:%s -> s/n:%s model:%s",
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

                if laser_head_model_changed:
                    # Now all the information about the new laser head should be present Thus we can fire this event
                    self._logger.info(
                        "laserhead_handler: Laserhead Model changed: s/n:%s model:%s -> s/n:%s model:%s",
                        self._last_used_lh_serial,
                        self._last_used_lh_model_id,
                        self._current_used_lh_serial,
                        self._current_used_lh_model_id,
                    )
                    # Fire the event
                    self._iobeam._call_callback(
                        IoBeamValueEvents.LASERHEAD_CHANGED,
                        "Laserhead Model changed",
                    )

            # BACKWARD_COMPATIBILITY: This is for detecting mrb_hw_info v0.0.20
            # This part of the code should never by reached, if reached then this means an update for mrb_hw_info did
            # fail TODO Remove this part of the code later
            # deprecated part Start
            elif self._valid_lh_data_backwards_compatibility(lh_data):
                self._logger.info("Laserhead (< v0.0.21): %s", lh_data)
                self._logger.warning(
                    "Received old laser head data from iobeam.", analytics=True
                )
            # deprecated part End

            elif lh_data == {}:
                # TODO this case needs to be handled better
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
        """
        Checks if essential laser head data are valid or not
        Args:
            lh_data (dict):

        Returns:
            True: if laser Head data are valid
            False: if laser Head data are not valid

        Raises:
            Exception: If the essential laser head data or parts of it are not valid
        """
        try:
            if (
                lh_data.get("main")
                and lh_data["main"].get("serial")
                and lh_data.get("power_calibrations")
                and len(lh_data["power_calibrations"]) > 0
                and lh_data["power_calibrations"][-1].get("power_65")
                and lh_data["power_calibrations"][-1].get("power_75")
                and lh_data["power_calibrations"][-1].get("power_85")
            ):
                self._logger.info("Valid Laser head Data Received: {}".format(lh_data))
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
        """
        Retrieves the current used laserhead data

        Returns:
            dict: current laserhead data if exists or default data otherwise
        """
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
        """
        Loads laser head data from a file
        """
        self._logger.debug("Loading data from  {} started...!".format(self._laser_heads_file))
        try:
            with open(self._laser_heads_file, "r") as stream:
                data = yaml.safe_load(stream)
            if data:
                self._lh_cache = data.get("laser_heads")
                self._last_used_lh_serial = data.get("last_used_lh_serial")
                self._last_used_lh_model = data.get("last_used_lh_model")
                self._last_used_lh_model_id = data.get("last_used_lh_model_id")
                self._correction_settings = data.get("correction_settings")

                self._logger.info("Loading data from  {} is successful!".format(self._laser_heads_file))
            else:
                self._logger.warn(
                    "Couldn't load laser head data, file: {} data: {}".format(self._laser_heads_file, data))
        except IOError as e:
            self._logger.error("Can't open file: {} {}".format(self._laser_heads_file, e))

    def _write_laser_heads_file(self, laser_heads_file=None):
        """
        Overwrites the file containing the laser heads info and creates the file if it doesn't exist

        Args:
            laser_heads_file (Yaml): path to the file to be used

        Returns:
            None
        """
        data = dict(
            laser_heads=self._lh_cache,
            correction_settings=self._correction_settings,
            last_used_lh_serial=self._current_used_lh_serial,
            last_used_lh_model=self._current_used_lh_model,
            last_used_lh_model_id=self._current_used_lh_model_id,
        )
        laser_heads_file = self._laser_heads_file if laser_heads_file is None else laser_heads_file
        self._logger.info("Writing to file: {} ..started".format(laser_heads_file))
        try:
            with open(laser_heads_file, "w") as outfile:
                yaml.safe_dump(data, outfile, default_flow_style=False)
                self._logger.info("Writing to file: {} ..is successful!".format(laser_heads_file))
        except IOError as e:
            self._logger.error("Can't open file: {} , Due to error: {}: ".format(laser_heads_file, e))

    @property
    def current_laserhead_max_temperature(self):
        """
        Return the current laser head max temperature

        Returns:
            float: Laser head max temp

        """
        current_laserhead_properties = self._get_laserhead_properties()

        # Handle the exceptions
        if((isinstance(current_laserhead_properties, dict) is False) or
                ("max_temperature" not in current_laserhead_properties) or
                (isinstance(current_laserhead_properties["max_temperature"], float) is False)):
            # Apply fallback
            self._logger.debug("Current laserhead properties: {}".format(current_laserhead_properties))
            self._logger.exception(
                "Current Laserhead Max temp couldn't be retrieved, fallback to the temperature value of: {}".format(
                    self.default_laserhead_max_temperature))
            return self.default_laserhead_max_temperature
        # Reaching here means, everything looks good
        self._logger.debug("Current Laserhead Max temp:{}".format(current_laserhead_properties["max_temperature"]))
        return current_laserhead_properties["max_temperature"]

    @property
    def default_laserhead_max_temperature(self):
        """
        Default max temperature for laser head. to be used by other modules at init time

        Returns:
            float: Laser head default max temp
        """

        return LASERHEAD_MAX_TEMP_FALLBACK

    def _load_current_laserhead_properties(self):
        """
        Loads the current detected laser head related properties from the laser head profile files and return them

        Returns:
            dict: current laser head properties, None: otherwise

        """
        # 1. get the ID of the current laser head
        laserhead_id = self.get_current_used_lh_model_id()

        # 2. Load the corresponding yaml file and return it's content
        lh_properties_file_path = os.path.join(self._plugin._basefolder,
                                               "profiles", "laserhead", "laserhead_id_{}.yaml".format(laserhead_id))
        if not os.path.isfile(lh_properties_file_path):
            self._logger.exception(
                "properties file for current laser head ID: {} doesn't exist or path is invalid. Path: {}".format(
                    laserhead_id, lh_properties_file_path))
            return None

        self._logger.debug(
            "properties file for current laser head ID: {} exists. Path:{}".format(
                laserhead_id, lh_properties_file_path) )
        try:
            with open(lh_properties_file_path) as lh_properties_yaml_file:
                self._logger.debug(
                    "properties file for current laser head ID: {} opened successfully".format(
                        laserhead_id))
                return yaml.safe_load(lh_properties_yaml_file)
        except (IOError, yaml.YAMLError) as e:
            self._logger.exception(
                "Exception: {} while Opening or loading the properties file for current laser head. Path: {}".format(
                    e, lh_properties_file_path))
            return None

    def _get_laserhead_properties(self):
        """
        returns the current saved laser head properties or load new if the laser head id changed

        Returns:
            dict: current laser head properties, None: otherwise

        """
        # 1. get the ID of the current laser head
        laserhead_id = self.get_current_used_lh_model_id()
        self._logger.debug("laserhead id compare {} - {}".format(laserhead_id, self._laserhead_properties.get("laserhead_id", None)))
        if laserhead_id != self._laserhead_properties.get("laserhead_id", None):
            self._logger.debug("new laserhead_id -> load current laserhead porperties")
            # 2. Load the corresponding yaml file and return it's content
            self._laserhead_properties = self._load_current_laserhead_properties()
            if self._laserhead_properties is not None:
                self._laserhead_properties.update({'laserhead_id': laserhead_id})
        else:
            self._logger.debug("no new laserhead_id -> return current laserhead_properties")

        self._logger.debug(
            "_laserhead_properties - {}".format(self._laserhead_properties))
        return self._laserhead_properties

    @property
    def current_laserhead_max_dust_factor(self):
        """
        Return the current laser head max dust factor

        Returns:
            float: Laser head max dust factor

        """
        current_laserhead_properties = self._get_laserhead_properties()

        # Handle the exceptions
        if ((isinstance(current_laserhead_properties, dict) is False) or
                ("max_dust_factor" not in current_laserhead_properties) or
                (isinstance(current_laserhead_properties["max_dust_factor"], float) is False)):
            # Apply fallback
            self._logger.debug("Current laserhead properties: {}".format(current_laserhead_properties))
            self._logger.exception(
                "Current Laserhead max dust factor couldn't be retrieved, fallback to the factor value of: {}".format(
                    self.default_laserhead_max_dust_factor))
            return self.default_laserhead_max_dust_factor
        # Reaching here means, everything looks good
        self._logger.debug("Current Laserhead max dust factor:{}".format(current_laserhead_properties["max_dust_factor"]))
        return current_laserhead_properties["max_dust_factor"]

    @property
    def default_laserhead_max_dust_factor(self):
        """
        Default max dust factor for laser head. to be used by other modules at init time

        Returns:
            float: Laser head default max dust factor
        """

        return LASERHEAD_MAX_DUST_FACTOR_FALLBACK



