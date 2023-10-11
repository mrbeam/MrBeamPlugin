from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.model.laser_cutter_mode import LaserCutterModeModel

# singleton instance of the LaserCutterModeService class to be used across the application
_instance = None


def laser_cutter_mode_service(plugin):
    """
    Get or create a singleton instance of the LaserCutterModeService.

    This function is used to manage a singleton instance of the LaserCutterModeService
    class. It ensures that only one instance of the service is created and returned
    during the program's execution.

    Parameters:
    - plugin (object): An object representing the plugin that requires the
      LaserCutterModeService. This is typically an instance of the plugin class.

    Returns:
    - _instance (LaserCutterModeService): The singleton instance of the
      LaserCutterModeService class. If no instance exists, it creates one and returns it.

    Notes:
    - The singleton pattern ensures that only one instance of LaserCutterModeService
      is created and shared across the application, preventing unnecessary resource
      duplication.
    - It is crucial to provide the `plugin` parameter to initialize or
      retrieve the singleton instance correctly.

    Example Usage:
    - To obtain the LaserCutterModeService instance:
      laser_cutter_mode_service = laser_cutter_mode_service(plugin_instance)
    """
    global _instance
    if _instance is None:
        _instance = LaserCutterModeService(plugin)
    return _instance


class LaserCutterModeService:
    """ Service class for laser cutter mode. """

    def __init__(self, plugin):
        """
        Initialize laser cutter mode service.

        Parameters:
        - plugin (object): An object representing the plugin that requires the
          LaserCutterModeService. This is typically an instance of the plugin class.

        Returns:
        - None
        """
        self._logger = mrb_logger("octoprint.plugins.mrbeam.services.laser_cutter_mode")
        self._settings = plugin.get_settings()
        self._mode = LaserCutterModeModel(self._load_laser_cutter_mode_id())

    def _load_laser_cutter_mode_id(self):
        """
        Load laser cutting mode id from settings.

        Parameters:
        - None

        Returns:
        - mode_id (int): The id of the laser cutting mode.

        Notes:
        - If the mode id is not found in the settings, it will fall back to default.
        """
        self._logger.debug("Load laser cutting mode from settings.")
        mode_id = self._settings.get(["laser_cutter_mode", "id"])
        return mode_id

    def get_mode(self):
        """
        Get laser cutting mode.

        Parameters:
        - None

        Returns:
        - mode (dict): A dictionary containing the id and name of the laser cutting mode.

        Notes:
        - The dictionary has the following format:
            {
                "id": <mode_id>,
                "name": <mode_name>,
            }
        """
        self._logger.debug("Get laser cutting mode.")
        return {
            "id": self._mode.id,
            "name": self._mode.name,
        }

    def get_mode_id(self):
        """
        Get laser cutting mode id.

        Parameters:
        - None

        Returns:
        - mode_id (int): The id of the laser cutting mode.
        """
        self._logger.debug("Get laser cutting mode id.")
        return self._mode.id

    def get_mode_name(self):
        """
        Get laser cutting mode name.

        Parameters:
        - None

        Returns:
        - mode_name (str): The name of the laser cutting mode.
        """
        self._logger.debug("Get laser cutting mode name.")
        return self._mode.name

    def change_mode_by_id(self, mode_id):
        """
        Change laser cutting mode by id.

        Parameters:
        - mode_id (int): The id of the laser cutting mode.

        Returns:
        - None

        Notes:
        - If the mode id is invalid, it will fall back to default.
        """
        self._logger.info("Change laser cutting mode by id: from mode_id=%s to mode_id=%s." % (self._mode.id, mode_id))
        self._mode.id = mode_id
        self._save_laser_cutter_mode_to_settings()

    def change_mode_by_name(self, mode_name):
        """
        Change laser cutting mode by name.

        Parameters:
        - mode_name (str): The name of the laser cutting mode.

        Returns:
        - None

        Notes:
        - If the mode name is invalid, it will fall back to default.
        """
        self._logger.info("Change laser cutting mode by name: from mode_name=%s to mode_name=%s."
                          % (self._mode.name, mode_name))
        self._mode.name = mode_name
        self._save_laser_cutter_mode_to_settings()

    def _save_laser_cutter_mode_to_settings(self):
        """
        Save laser cutting mode to settings.

        Parameters:
        - None

        Returns:
        - None

        Notes:
        - This function is called after changing the laser cutting mode.
        """
        self._logger.debug("Save laser cutting mode to settings.")
        self._settings.set(["laser_cutter_mode", "id"], self._mode.id, force=True)
        self._settings.set(["laser_cutter_mode", "name"], self._mode.name, force=True)
        self._settings.save()

    # The below is for future implementation
    # def _send_update_message_or_event(self):
    #     self._plugin._plugin_manager.send_plugin_message(
    #           self._plugin._identifier, dict(laserCutterMode=self._mode.id)
    #     )
    #     self._plugin._event_bus.fire(
    #         "laserCutterModeChanged", payload=dict(laserCutterMode=self._mode.id)
    #     )
