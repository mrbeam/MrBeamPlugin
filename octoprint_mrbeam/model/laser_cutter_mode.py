from octoprint_mrbeam.mrb_logger import mrb_logger


class LaserCutterModeModel(object):
    """ Data object containing information about the laser cutter mode """

    MODES = {
        0: "default",
        1: "rotary",
    }
    FALLBACK_MODE_ID = 0
    FALLBACK_WARNING = "Falling back to default."

    def __init__(self, mode_id=FALLBACK_MODE_ID):
        """Initialize laser cutter mode.

        If the mode id is not found in the defined MODES, it will fall back to default.

        Args:
            mode_id (int): The id of the laser cutter mode.
        """
        self._logger = mrb_logger("octoprint.plugins.mrbeam.model.laser_cutter_mode")

        # Set mode id and name based on the given mode id
        # If the mode id is not found in the defined MODES, it will fall back
        # to default.
        if mode_id in self.MODES:
            self._id = mode_id
            self._name = self.MODES[mode_id]
        else:
            self._logger.error("Invalid laser cutter mode id during init.")
            self._logger.warn(self.FALLBACK_WARNING)
            self._id = self.FALLBACK_MODE_ID
            self._name = self.MODES[self.FALLBACK_MODE_ID]

    @property
    def id(self):
        """Get laser cutter mode id.

        Returns:
            id (int): The id of the laser cutter mode.
        """
        return self._id

    @property
    def name(self):
        """Get laser cutter mode name.

        Returns:
            name (str): The name of the laser cutter mode.
        """
        return self._name

    @id.setter
    def id(self, mode_id):
        """Set laser cutter mode id.

        If the mode id is not found in the defined MODES, it will fall back to default.

        Args:
            mode_id (int): The id of the laser cutter mode.
        """
        if mode_id in self.MODES:
            self._id = mode_id
            self._name = self.MODES[mode_id]
        else:
            self._logger.error("Invalid laser cutter mode id during init.")
            self._logger.warn(self.FALLBACK_WARNING)
            self._id = self.FALLBACK_MODE_ID
            self._name = self.MODES[self.FALLBACK_MODE_ID]

    @name.setter
    def name(self, mode_name):
        """Set laser cutter mode name.

        If the mode name is not in the defined MODES, it will fall back to default.

        Args:
            mode_name (str): The name of the laser cutter mode.
        """
        if mode_name in self.MODES.values():
            self._id = self._get_mode_key(mode_name)
            self._name = self.MODES[self._id]
        else:
            self._logger.error("Invalid laser cutter mode name.")
            self._logger.warn(self.FALLBACK_WARNING)
            self._id = self.FALLBACK_MODE_ID
            self._name = self.MODES[self.FALLBACK_MODE_ID]

    def _get_mode_key(self, mode_name):
        """Get laser cutter mode key.

        If the mode name is not found in the defined MODES, it will fall back to default.

        Args:
            mode_name (str): The name of the laser cutter mode.

        Returns:
            mode_key (int): The key of the laser cutter mode.
        """
        try:
            return list(self.MODES.values()).index(mode_name)
        except ValueError as e:
            self._logger.error("Invalid laser cutter mode name: %s", e)
            self._logger.warn(self.FALLBACK_WARNING)
            return self.FALLBACK_MODE_ID
