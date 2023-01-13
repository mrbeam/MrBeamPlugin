# singleton
import os

import yaml

from octoprint_mrbeam.mrb_logger import mrb_logger

_instance = None


def airfilter(plugin):
    """Returns the singleton instance of the AirFilter class

    Args:
        plugin: MrBeamPlugin

    Returns:
        AirFilter: singleton instance
    """
    global _instance
    if _instance is None:
        _instance = AirFilter(plugin)
    return _instance


class AirFilter(object):
    """
    Air Filter class to collect the data we receive over iobeam for the air filter system.
    """

    AIRFILTER2_MODELS = [1, 2, 3, 4, 5, 6, 7]
    AIRFILTER3_MODELS = [8]
    PREFILTER_LIFESPAN_FALLBACK = 40
    CARBON_LIFESPAN_FALLBACK = 280
    PREFILTER = "prefilter"
    CARBONFILTER = "carbonfilter"
    FILTERSTAGES = [PREFILTER, CARBONFILTER]

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.airfilter")
        self._plugin = plugin
        self._serial = None
        self._model_id = None
        self._pressure1 = None
        self._pressure2 = None
        self._pressure3 = None
        self._pressure4 = None
        self._temperature1 = None
        self._temperature2 = None
        self._temperature3 = None
        self._temperature4 = None
        self._profile = None

    @property
    def model(self):
        """Returns the model name of the air filter.

        Returns:
            str: Model name of the air filter
        """
        if self._model_id == 0:
            return "Air Filter System | Fan"
        elif self._model_id in self.AIRFILTER2_MODELS:
            return "Air Filter II System"
        elif self._model_id in self.AIRFILTER3_MODELS:
            return "Air Filter 3 System"
        else:
            return "Unknown"

    @property
    def model_id(self):
        """Returns the model id of the air filter.

        Returns:
            int: Model id of the air filter
        """
        return self._model_id

    @property
    def serial(self):
        """Returns the serial number of the air filter.

        Returns:
            str: Serial number of the air filter
        """
        return self._serial

    @property
    def pressure(self):
        """Returns the pressure readings of the air filter.

        Returns:
            int: Pressure of the air filter 2 | {'pressure1': int, 'pressure2': int, 'pressure3': int, 'pressure4': int}
        """
        if self._pressure2 is not None:
            return {
                "pressure1": self._pressure1,
                "pressure2": self._pressure2,
                "pressure3": self._pressure3,
                "pressure4": self._pressure4,
            }
        return self._pressure1

    @property
    def temperatures(self):
        """Returns the temperature readings of the air filter 3 system.

        Returns:
            {'temperature1': float, 'temperature2': float, 'temperature3': int, 'temperature4': float}
        """
        if (
            self._temperature1 is not None
            or self._temperature2 is not None
            or self._temperature3 is not None
            or self._temperature4 is not None
        ):
            return {
                "temperature1": self._temperature1,
                "temperature2": self._temperature2,
                "temperature3": self._temperature3,
                "temperature4": self._temperature4,
            }
        return None

    @serial.setter
    def serial(self, serial):
        """Sets the serial of the air filter.

        Args:
            serial (str): Serial of the air filter
        """
        if serial != self._serial:
            self._serial = serial
            self._plugin.send_mrb_state()

    @model_id.setter
    def model_id(self, model_id):
        """Sets the model id of the air filter.

        Args:
            model_id (int): Model id of the air filter
        """
        # if model id is not the same as before, reset data
        if self._model_id != model_id:
            self.reset_data()
            self._model_id = model_id
            self._plugin.send_mrb_state()
            self._load_current_profile()

    def set_pressure(
        self,
        pressure=None,
        pressure1=None,
        pressure2=None,
        pressure3=None,
        pressure4=None,
    ):
        """Sets the pressure of the air filter.

        Args:
            pressure: Pressure of the air filter 2
            pressure1 (int): Pressure of the air filter 3 Inlet
            pressure2 (int): Pressure of the air filter 3 1. Prefilter to 2. Prefilter
            pressure3 (int): Pressure of the air filter 3 2. Prefilter to Mainfilter
            pressure4 (int): Pressure of the air filter 3 Mainfilter to Fan
        """
        if pressure is not None:
            self._pressure1 = pressure
        elif pressure1 is not None:
            self._pressure1 = pressure1
        if pressure2 is not None:
            self._pressure2 = pressure2
        if pressure3 is not None:
            self._pressure3 = pressure3
        if pressure4 is not None:
            self._pressure4 = pressure4

    def set_temperatures(
        self,
        temperature1=None,
        temperature2=None,
        temperature3=None,
        temperature4=None,
    ):
        """Sets the temperatures of the air filter 3 system.

        Args:
            temperature1 (float): Temperature of the air filter 3 Inlet
            temperature2 (float): Temperature of the air filter 3 1. Prefilter to 2. Prefilter
            temperature3 (float): Temperature of the air filter 3 2. Prefilter to Mainfilter
            temperature4 (float): Temperature of the air filter 3 Mainfilter to Fan
        """
        if temperature1 is not None:
            self._temperature1 = temperature1
        if temperature2 is not None:
            self._temperature2 = temperature2
        if temperature3 is not None:
            self._temperature3 = temperature3
        if temperature4 is not None:
            self._temperature4 = temperature4

    def reset_data(self):
        """Resets all data of the air filter."""
        self._serial = None
        self._model_id = None
        self._pressure1 = None
        self._pressure2 = None
        self._pressure3 = None
        self._pressure4 = None
        self._temperature1 = None
        self._temperature2 = None
        self._temperature3 = None
        self._temperature4 = None
        self._profile = None

    def _load_current_profile(self):
        if self._model_id is None:
            self._logger.debug(
                "profile not loaded as id is not valid :{}".format(self.model_id)
            )
        else:
            self._logger.debug(
                "load profile for air filter system ID:{}".format(self.model_id)
            )
            # 1. Load the corresponding yaml file and return it's content
            af_profile_file_path = os.path.join(
                self._plugin._basefolder,
                "profiles",
                "airfilter_system",
                "airfilter_system_id_{}.yaml".format(self.model_id),
            )
            if not os.path.isfile(af_profile_file_path):
                self._logger.exception(
                    "profile file for current air filter system ID: {} doesn't exist or path is invalid. Path: {}".format(
                        self.model_id, af_profile_file_path
                    )
                )
                self._profile = None
            #
            self._logger.debug(
                "profile file for current air filter system ID: {} exists. Path:{}".format(
                    self.model_id, af_profile_file_path
                )
            )
            try:
                with open(af_profile_file_path) as af_profile_yaml_file:
                    self._logger.debug(
                        "profile file for current air filter system ID: {} opened successfully".format(
                            self.model_id
                        )
                    )
                    self._profile = yaml.safe_load(af_profile_yaml_file)
            except (IOError, yaml.YAMLError) as e:
                self._logger.exception(
                    "Exception: {} while Opening or loading the profile file for current air filter system. Path: {}".format(
                        e, af_profile_file_path
                    )
                )
                self._profile = None

    @property
    def profile(self):
        """returns the current saved laser head profile or load new if the
        air filter system id changed.

        Returns:
            dict: current air filter system profile, None: otherwise
        """
        self._logger.debug(
            "get profile for air filter system ID:{}".format(self.model_id)
        )
        return self._profile

    def get_lifespan(self, filterstage, stage_id=0):
        current_airfilter_profile = self.profile
        if filterstage not in self.FILTERSTAGES:
            self._logger.error("filterstage {} is not known".format(filterstage))
            return None

        if filterstage == self.PREFILTER:
            fallbackvalue = self.PREFILTER_LIFESPAN_FALLBACK
        elif filterstage == self.CARBONFILTER:
            fallbackvalue = self.CARBON_LIFESPAN_FALLBACK
        else:
            fallbackvalue = 0
        # Handle the exceptions
        if (
            (isinstance(current_airfilter_profile, dict) is False)
            or (filterstage not in current_airfilter_profile)
            or (isinstance(current_airfilter_profile[filterstage], list) is False)
            or (
                isinstance(current_airfilter_profile[filterstage][stage_id], dict)
                is False
            )
            or (
                isinstance(
                    current_airfilter_profile[filterstage][stage_id]["lifespan"], int
                )
                is False
            )
        ):
            # Apply fallback
            self._logger.debug(
                "Current air filter system profile: {}".format(
                    current_airfilter_profile
                )
            )
            self._logger.error(
                "Current {} ID:{} lifespan couldn't be retrieved, fallback to the fallback value of: {}".format(
                    filterstage, stage_id, fallbackvalue
                )
            )
            return fallbackvalue
        # Reaching here means, everything looks good
        self._logger.debug(
            "Current {} ID:{} lifespan:{}".format(
                filterstage,
                stage_id,
                current_airfilter_profile[filterstage][stage_id]["lifespan"],
            )
        )
        return current_airfilter_profile[filterstage][stage_id]["lifespan"]
