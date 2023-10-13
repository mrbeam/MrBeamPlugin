from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.model.laser_cutter_mode import LaserCutterModeModel

# singleton instance of the LaserCutterModeService class to be used across the application
_instance = None


def laser_cutter_mode_service(plugin):
    """Get or create a singleton instance of the LaserCutterModeService.

    This function is used to manage a singleton instance of the LaserCutterModeService
    class. It ensures that only one instance of the service is created and returned
    during the program's execution.

    Example Usage: laser_cutter_mode_service = laser_cutter_mode_service(plugin_instance)

    Args:
        plugin (object): An object representing the MrBeamPlugin

    Returns:
        _instance (LaserCutterModeService): The singleton instance of the LaserCutterModeService
        class. If no instance exists, it creates one and returns it.

    """
    global _instance
    if _instance is None:
        _instance = LaserCutterModeService(plugin)
    return _instance


class LaserCutterModeService:
    """ Service class for laser cutter mode. """

    def __init__(self, plugin):
        """Initialize laser cutter mode service.

        Args:
            plugin (object): An object representing the plugin that requires the LaserCutterModeService.
            This is typically an instance of the plugin class.
        """
        self._logger = mrb_logger("octoprint.plugins.mrbeam.services.laser_cutter_mode")
        self._settings = plugin.get_settings()
        self._mode = LaserCutterModeModel(self._load_laser_cutter_mode_id())

    def _load_laser_cutter_mode_id(self):
        """Load laser cutting mode id from settings.

        If the mode id is not found in the settings, it will fall back to default.

        Returns:
            mode_id (int): The id of the laser cutting mode.

        """
        self._logger.debug("Load laser cutting mode from settings.")
        mode_id = self._settings.get(["laser_cutter_mode"])
        return mode_id

    def get_mode_id(self):
        """Get laser cutting mode id.

        Returns:
            mode_id (int): The id of the laser cutting mode.
        """
        self._logger.debug("Get laser cutting mode id.")
        return self._mode.id

    def change_mode_by_id(self, mode_id):
        """Change laser cutting mode by id.

        If the mode id is invalid, it will fall back to default.

        Args:
            mode_id (int): The id of the laser cutting mode.

        Returns:

        """
        self._logger.info("Change laser cutting mode by id: from mode_id=%s to mode_id=%s." % (self._mode.id, mode_id))
        self._mode.id = mode_id
        self._save_laser_cutter_mode_to_settings()

    def _save_laser_cutter_mode_to_settings(self):
        """Save laser cutting mode to settings.

        This function is called after changing the laser cutting mode.
        """
        self._logger.debug("Save laser cutting mode to settings.")
        self._settings.set(["laser_cutter_mode"], self._mode.id, force=True)
        self._settings.save()

    # The below is for future implementation
    # def _send_update_message_or_event(self):
    #     self._plugin._plugin_manager.send_plugin_message(
    #           self._plugin._identifier, dict(laserCutterMode=self._mode.id)
    #     )
    #     self._plugin._event_bus.fire(
    #         "laserCutterModeChanged", payload=dict(laserCutterMode=self._mode.id)
    #     )
