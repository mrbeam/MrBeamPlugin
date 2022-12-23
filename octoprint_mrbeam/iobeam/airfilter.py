# singleton
from octoprint_mrbeam.mrb_logger import mrb_logger

_instance = None


def airfilter(plugin):
    global _instance
    if _instance is None:
        _instance = AirFilter(plugin)
    return _instance


class AirFilter(object):
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
        return self._model_id

    @property
    def serial(self):
        return self._serial

    @property
    def pressure(self):
        if self._pressure2 is not None:
            return {
                "pressure1": self._pressure1,
                "pressure2": self._pressure2,
                "pressure3": self._pressure3,
                "pressure4": self._pressure4,
            }
        return self._pressure1

    def set_serial(self, serial):
        self._serial = serial

    def set_model_id(self, model_id):
        self._model_id = model_id

    def set_pressure(
        self,
        pressure=None,
        pressure1=None,
        pressure2=None,
        pressure3=None,
        pressure4=None,
    ):
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
