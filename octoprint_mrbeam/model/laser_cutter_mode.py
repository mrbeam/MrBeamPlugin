from octoprint_mrbeam.mrb_logger import mrb_logger

class LaserCutterModeModel:
    """ Data object containing information about the laser cutter mode """

    MODES = {
        0: "default",
        1: "rotary",
    }
    FALLBACK_MODE = 0

    def __init__(self, id= FALLBACK_MODE):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.model.laser_cutter_mode")
        if id not in self.MODES:
            self._logger.error("Invalid laser cutter mode id during init. Falling back to default.")
            id = self.FALLBACK_MODE
        self._id = id
        self._name = self.MODES[id]

    @property
    def id(self):
        """
        Get laser cutter mode id.

        Parameters:
        - None

        Returns:
        - id (int): The id of the laser cutting mode.
        """
        return self._id

    @property
    def name(self):
        """
        Get laser cutter mode name.

        Parameters:
        - None

        Returns:
        - name (str): The name of the laser cutting mode.
        """
        return self._name

    @id.setter
    def id(self, id):
        """
        Set laser cutter mode id.

        Parameters:
        - id (int): The id of the laser cutting mode.

        Returns:
        - None

        Notes:
        - If the mode id is not found in the settings, it will fall back to default.
        """
        if id not in self.MODES:
            self._logger.error("Invalid laser cutter mode id. Falling back to default.")
            id = self.FALLBACK_MODE
        self._id = id
        self._name = self.MODES[id]

    @name.setter
    def name(self, name):
        """
        Set laser cutter mode name.

        Parameters:
        - name (str): The name of the laser cutting mode.

        Returns:
        - None

        Notes:
        - If the mode name is not found in the settings, it will fall back to default.
        """
        if name not in self.MODES.values():
            self._logger.error("Invalid laser cutter mode name. Falling back to default.")
            name = self.MODES[self.FALLBACK_MODE]
        self._name = name
        self._id = list(self.MODES.keys())[list(self.MODES.values()).index(name)]
