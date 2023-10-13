from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.enums.laser_cutter_mode import LaserCutterModeEnum


class LaserCutterModeModel(object):
    """ Data object containing information about the laser cutter mode """
    FALLBACK_MODE_ID = LaserCutterModeEnum.DEFAULT.value
    FALLBACK_WARNING = "Falling back to {}".format(FALLBACK_MODE_ID)

    MODES = [mode.value for mode in LaserCutterModeEnum]

    def __init__(self, mode_id=FALLBACK_MODE_ID):
        """Initialize laser cutter mode.

        If the mode id is not found in the defined MODES, it will fall back to default.

        Args:
            mode_id (int): The id of the laser cutter mode.
        """
        self._logger = mrb_logger("octoprint.plugins.mrbeam.model.laser_cutter_mode")

        if mode_id in self.MODES:
            self._id = mode_id
        else:
            self._logger.error("Invalid laser cutter mode id during init: {}".format(mode_id))
            self._logger.warn(self.FALLBACK_WARNING)
            self._id = self.FALLBACK_MODE_ID

    @property
    def id(self):
        """Get laser cutter mode id.

        Returns:
            id (int): The id of the laser cutter mode.
        """
        return self._id

    @id.setter
    def id(self, mode_id):
        """Set laser cutter mode id.

        If the mode id is not found in the defined MODES, it will fall back to default.

        Args:
            mode_id (int): The id of the laser cutter mode.
        """
        if mode_id in self.MODES:
            self._id = mode_id
        else:
            self._logger.error("Invalid laser cutter mode id during set: {}".format(mode_id))
            self._logger.warn(self.FALLBACK_WARNING)
            self._id = self.FALLBACK_MODE_ID
