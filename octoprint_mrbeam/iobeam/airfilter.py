# singleton
import os
from enum import Enum
from collections import deque

import yaml
from flask_babel import gettext

from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents

from octoprint_mrbeam.mrbeam_events import MrBeamEvents
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

    AIRFILTER_OR_SINGLE_MODELS = [None, 0, 1]
    AIRFILTER2_MODELS = [2, 3, 4, 5, 6, 7]
    AIRFILTER3_MODELS = [8]
    AIRFILTER_OR_SINGLE_MODEL_ID = "Air Filter System | Fan"
    AIRFILTER2_MODEL_ID = "Air Filter II System"
    AIRFILTER3_MODEL_ID = "Air Filter 3 System"
    PREFILTER_LIFESPAN_FALLBACK = 40
    CARBON_LIFESPAN_FALLBACK = 280
    PREFILTER = "prefilter"
    CARBONFILTER = "carbonfilter"
    FILTERSTAGES = [PREFILTER, CARBONFILTER]
    PRESSURE_VALUES_LIST_SIZE = 5
    MAX_PRESSURE_DIFFERENCE = 1880
    MAX_FAN_TEST_RPM = 10750
    AF3_MAX_PREFILTER_PRESSURE_CHANGE = (
        100  # The maximum pressure change in Pa for the prefilter of the AF3
    )
    AF3_MAX_CARBON_FILTER_PRESSURE_CHANGE = (
        50  # The maximum pressure change in Pa for the carbon filter of the AF3
    )
    AF3_PRESSURE_DROP_PERCENTAGE_FOR_RESET = (
        40  # The percentage of the pressure drop before a reset is triggered
    )
    AF3_PRESSURE2_MIN = 9200

    AF3_PRESSURE_GRAPH_CARBON_FILTER = [
        (450, 0),
        (880, 20),
        (950, 40),
        (1150, 60),
        (1500, 80),
        (MAX_PRESSURE_DIFFERENCE, 100),
    ]
    AF3_PRESSURE_GRAPH_PREFILTER = [
        (100, 0),
        (300, 20),
        (620, 40),
        (800, 60),
        (980, 80),
        (1200, 100),
    ]
    AF3_RPM_GRAPH = [
        (9860, 0),
        (9900, 20),
        (10200, 70),
        (MAX_FAN_TEST_RPM, 100),
    ]

    class ProfileParameters(Enum):
        SHOPIFY_LINK = "shopify_link"
        LIFESPAN = "lifespan"
        HEAVY_DUTY_LIFESPAN = "heavy_duty_lifespan"
        HEAVY_DUTY_SHOPIFY_LINK = "heavy_duty_shopify_link"

    DEFAULT_PROFILE = {
        CARBONFILTER: [
            {
                ProfileParameters.LIFESPAN.value: CARBON_LIFESPAN_FALLBACK,
                ProfileParameters.SHOPIFY_LINK.value: "products/aktivkohlefilter-inklusive-zehn-vorfilter?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
            }
        ],
        PREFILTER: [
            {
                ProfileParameters.LIFESPAN.value: PREFILTER_LIFESPAN_FALLBACK,
                ProfileParameters.SHOPIFY_LINK.value: "products/vorfilter-mrbeam?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
                ProfileParameters.HEAVY_DUTY_LIFESPAN.value: PREFILTER_LIFESPAN_FALLBACK,
                ProfileParameters.HEAVY_DUTY_SHOPIFY_LINK.value: "products/mr-beam-vorfilter-kartusche-5er-pack?utm_source=beamos&utm_medium=beamos&utm_campaign=maintenance_page",
            }
        ],
        "prefilter_stages": 1,
        "carbonfilter_stages": 1,
    }

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.airfilter")
        self._plugin = plugin
        self._event_bus = plugin._event_bus
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
        self._connected = None
        self._last_pressure_values = deque(maxlen=self.PRESSURE_VALUES_LIST_SIZE)
        self._profile = None

        self._load_current_profile()

    @property
    def model(self):
        """Returns the model name of the air filter.

        Returns:
            str: Model name of the air filter
        """
        if self._model_id in self.AIRFILTER_OR_SINGLE_MODELS and self.connected:
            return self.AIRFILTER_OR_SINGLE_MODEL_ID
        elif self._model_id in self.AIRFILTER2_MODELS:
            return self.AIRFILTER2_MODEL_ID
        elif self._model_id in self.AIRFILTER3_MODELS:
            return self.AIRFILTER3_MODEL_ID

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

    def set_airfilter(self, model_id, serial):
        """Sets the air filter.

        Args:
            model_id (int): Model id of the air filter
            serial (str): Serial of the air filter
        """
        if (
            serial is not None
            and model_id is not None
            and (serial != self._serial or model_id != self._model_id)
        ):
            self.reset_data()
            self._serial = serial
            self._model_id = model_id
            self._load_current_profile()
            self._airfilter_changed()

    def _airfilter_changed(self):
        self._plugin.send_mrb_state()
        self._event_bus.fire(MrBeamEvents.AIRFILTER_CHANGED)

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
            pressure1 (int): Pressure of the air filter 3 environment pressure
            pressure2 (int): Pressure of the air filter 3 between inlet and Prefilter
            pressure3 (int): Pressure of the air filter 3 between Prefilter and Mainfilter
            pressure4 (int): Pressure of the air filter 3 between Mainfilter and Fan
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

        if all([pressure1, pressure2, pressure3, pressure4]):
            self._last_pressure_values.append(
                [self._pressure1, self._pressure2, self._pressure3, self._pressure4]
            )
        elif self._pressure1 is not None and self.model_id in self.AIRFILTER2_MODELS:
            self._last_pressure_values.append(self._pressure1)

    def _get_avg_pressure_differences(self):
        """Returns the average pressure differences of the last pressure readings.

        Returns:
            (int, int, int): Average pressure difference of the last pressure readings for prefilter mainfilter and fan
        """
        self._logger.debug(
            "Calculating average pressure differences. %s", self._last_pressure_values
        )
        prefilter_pressure = [sublist[1] for sublist in self._last_pressure_values]
        mainfilter_pressure = [sublist[2] for sublist in self._last_pressure_values]
        fan_pressure = [sublist[3] for sublist in self._last_pressure_values]

        # calculate the average
        prefilter_pressure_avg = max(
            0, sum(prefilter_pressure) / len(prefilter_pressure)
        )  # limited to min 0
        mainfilter_pressure_avg = max(
            0, sum(mainfilter_pressure) / len(mainfilter_pressure)
        )  # limited to min 0
        fan_pressure_avg = max(
            0, sum(fan_pressure) / len(fan_pressure)
        )  # limited to min 0
        return prefilter_pressure_avg, mainfilter_pressure_avg, fan_pressure_avg

    @property
    def last_pressure_values(self):
        return list(self._last_pressure_values)

    @property
    def pressure_drop_mainfilter(self):
        """Returns the pressure drop of the main filter.

        Returns:
            int: Pressure drop of the main filter
        """
        if self.model_id in self.AIRFILTER3_MODELS:
            (
                _,
                mainfilter_pressure_avg,
                fan_pressure_avg,
            ) = self._get_avg_pressure_differences()

            return mainfilter_pressure_avg - fan_pressure_avg
        return None

    def exhaust_hose_is_blocked(self):
        if self.model_id in self.AIRFILTER3_MODELS:
            return self._pressure2 < self.AF3_PRESSURE2_MIN
        return None

    @property
    def pressure_drop_prefilter(self):
        """Returns the pressure drop of the prefilter.

        Returns:
                int: Pressure drop of the prefilter
        """
        if self.model_id in self.AIRFILTER3_MODELS:
            (
                prefilter_pressure_avg,
                mainfilter_pressure_avg,
                _,
            ) = self._get_avg_pressure_differences()

            return prefilter_pressure_avg - mainfilter_pressure_avg
        return None

    @property
    def connected(self):
        return self._connected

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

    def set_connected(self, connected):
        """
        Sets the connected state and fires an event if the state changed.

        Args:
            connected: True if the fan is connected, False otherwise

        Returns:
            None
        """
        if self._connected != connected:
            self._connected = connected
            if connected:
                self._event_bus.fire(IoBeamEvents.FAN_CONNECTED)
                if self.serial is None and self.model_id is None:
                    self.set_airfilter(1, self.UNKNOWN_SERIAL_KEY)
            else:
                self._event_bus.fire(IoBeamEvents.FAN_DISCONNECTED)

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
        self._connected = None
        self._last_pressure_values = deque(maxlen=self.PRESSURE_VALUES_LIST_SIZE)

    def _load_current_profile(self):
        """Loads the current profile of the air filter and safes it in self._profile.

        Returns:
            None
        """
        if self._model_id is None:
            self._logger.debug(
                "profile not loaded as id is not valid :{}".format(self.model_id)
            )
            self._profile = self.DEFAULT_PROFILE
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
                self._profile = self.DEFAULT_PROFILE
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
                self._profile = self.DEFAULT_PROFILE

    @property
    def profile(self):
        """returns the current saved laser head profile or load new if the
        air filter system id changed.

        Returns:
            dict: current air filter system profile, None: otherwise
        """
        return self._profile

    def get_lifespan(self, filter_stage, stage_id=0):
        """Returns the lifespan of the filter stage.

        Args:
            filter_stage (str): Filter stage to get the lifespan from [FILTERSTAGES]
            stage_id (int): id of the sub stage default: 0

        Returns:
            int: Lifespan of the filter stage in hours, None: otherwise
        """
        if not isinstance(stage_id, int):
            self._logger.error(
                "stage_id is not an integer will use 0 instead: {}".format(stage_id)
            )
            stage_id = 0
        current_airfilter_profile = self.profile
        self._logger.debug(
            "get lifespan of filter_stage: {} stage id: {} in profile: {}".format(
                filter_stage, stage_id, current_airfilter_profile
            )
        )
        if filter_stage not in self.FILTERSTAGES:
            self._logger.error("filter_stage {} is not known".format(filter_stage))
            return None

        if filter_stage == self.PREFILTER:
            fallbackvalue = self.PREFILTER_LIFESPAN_FALLBACK
        elif filter_stage == self.CARBONFILTER:
            fallbackvalue = self.CARBON_LIFESPAN_FALLBACK
        else:
            fallbackvalue = 0
            self._logger.warn(
                "The selected filter stage does not have a fallback value, we will use 0 instead"
            )

        lifespan_key = self.ProfileParameters.LIFESPAN.value
        if (
            self.heavy_duty_prefilter_enabled()
            and not self._is_lifespan_value_not_present(
                current_airfilter_profile,
                filter_stage,
                stage_id,
                self.ProfileParameters.HEAVY_DUTY_LIFESPAN.value,
            )
        ):
            self._logger.debug("use heavy duty lifespan")
            lifespan_key = self.ProfileParameters.HEAVY_DUTY_LIFESPAN.value
        # Handle the exceptions
        if self._is_lifespan_value_not_present(
            current_airfilter_profile, filter_stage, stage_id, lifespan_key
        ):
            # Apply fallback
            self._logger.error(
                "Current {} ID:{} lifespan couldn't be retrieved, fallback to the fallback value of: {}".format(
                    filter_stage, stage_id, fallbackvalue
                )
            )
            return fallbackvalue
        # Reaching here means, everything looks good
        return current_airfilter_profile[filter_stage][stage_id][lifespan_key]

    def _is_lifespan_value_not_present(
        self, current_airfilter_profile, filter_stage, stage_id, lifespan_key
    ):
        return (
            (isinstance(current_airfilter_profile, dict) is False)
            or (filter_stage not in current_airfilter_profile)
            or (isinstance(current_airfilter_profile[filter_stage], list) is False)
            or (len(current_airfilter_profile[filter_stage]) < stage_id + 1)
            or (
                isinstance(current_airfilter_profile[filter_stage][stage_id], dict)
                is False
            )
            or (lifespan_key not in current_airfilter_profile[filter_stage][stage_id])
            or (
                isinstance(
                    current_airfilter_profile[filter_stage][stage_id][lifespan_key],
                    int,
                )
                is False
            )
        )

    def get_lifespans(self, filter_stage):
        """Returns the lifespan of the given filter stage and sub stages.

        Args:
            filter_stage (str): name of the filter stage [FILTERSTAGES]

        Returns:
            list: list of lifespans of the given filter stage or None if the profile is None
        """
        self._logger.debug("get lifespans of filter_stage: {}".format(filter_stage))
        current_airfilter_profile = self.profile
        if current_airfilter_profile is not None:
            stages = current_airfilter_profile.get(filter_stage + "_stages")
            if stages is not None:
                lifespans = []
                for i in range(stages):
                    lifespans.append(self.get_lifespan(filter_stage, i))
                self._logger.debug(
                    "lifespans of filter_stage: {} are: {}".format(
                        filter_stage, lifespans
                    )
                )
                return lifespans

        self._logger.error(
            "Current amount of stages couldn't be retrieved - filter stage: {} profile: {}".format(
                filter_stage, current_airfilter_profile
            )
        )
        return None

    def get_shopify_links(self, filter_stage, heavy_duty=False):
        """Returns the shopify links of the given filter stage and sub stages.

        Args:
            filter_stage (str): name of the filter stage [FILTERSTAGES]
            heavy_duty (bool): True if heavy duty prefilter is enabled

        Returns:
            list: list of shopify links of the given filter stage or None if the profile is None
        """
        current_airfilter_profile = self.profile
        shopify_link_key = self.ProfileParameters.SHOPIFY_LINK.value
        if heavy_duty:
            shopify_link_key = self.ProfileParameters.HEAVY_DUTY_SHOPIFY_LINK.value
        if current_airfilter_profile is not None:
            stages = current_airfilter_profile.get(filter_stage + "_stages")
            if stages is not None:
                shopify_links = []
                for i in range(stages):
                    try:
                        shopify_links.append(
                            gettext("https://www.mr-beam.org/en/")
                            + current_airfilter_profile[filter_stage][i][
                                shopify_link_key
                            ]
                        )
                    except KeyError:
                        self._logger.error(
                            "Shopify link not found for filter stage: {} stage id: {}".format(
                                filter_stage, i
                            )
                        )
                return shopify_links

        self._logger.error(
            "Current amount of stages couldn't be retrieved - filter stage: {} profile: {}".format(
                filter_stage, current_airfilter_profile
            )
        )
        return None

    def heavy_duty_prefilter_enabled(self):
        """
        Returns True if the heavy duty prefilter is enabled in the current profile

        Returns:
            bool: True if the heavy duty prefilter is enabled in the current profile
        """
        return self._plugin.is_heavy_duty_prefilter_enabled()
