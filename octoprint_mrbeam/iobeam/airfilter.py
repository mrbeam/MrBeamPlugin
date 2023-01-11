# singleton
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

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.airfilter")
        self._plugin = plugin
        self._serial = None
        self._model_id = None
        self._pressure1 = None
        self._pressure2 = None
        self._pressure3 = None
        self._pressure4 = None

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

    @serial.setter
    def serial(self, serial):
        """Sets the serial of the air filter.

        Args:
            serial (str): Serial of the air filter
        """
        self._serial = serial

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

    def reset_data(self):
        """Resets all data of the air filter."""
        self._serial = None
        self._model_id = None
        self._pressure1 = None
        self._pressure2 = None
        self._pressure3 = None
        self._pressure4 = None
