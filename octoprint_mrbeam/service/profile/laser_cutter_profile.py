from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.service.profile.profile import ProfileService
from octoprint_mrbeam.model.laser_cutter_profile import LaserCutterProfileModel
from octoprint_mrbeam.constant.profile.laser_cutter.profile_1 import profile as default_profile
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton instance of the LaserCutterProfileService class to be used across the application
_instance = None


def laser_cutter_profile_service(plugin=None, profile=default_profile):
    """
    Get or create a singleton instance of the LaserCutterProfileService.

    This function is used to manage a singleton instance of the LaserCutterProfileService
    class. It ensures that only one instance of the service is created and returned
    during the program's execution.

    Example Usage: laser_cutter_profile_service = laser_cutter_profile_service(plugin_instance)

    Args:
        plugin (object): An object representing the MrBeamPlugin
        profile (dict): The default profile of the laser cutter.

    Returns:
        _instance (LaserCutterProfileService): The singleton instance of the LaserCutterProfileService
        class. If no instance exists, it creates one and returns it.
    """
    global _instance
    if _instance is None:
        _instance = LaserCutterProfileService(id="laser_cutter", profile=LaserCutterProfileModel(profile).data)
        # fire event to notify other plugins that the laser cutter profile is initialized
        if plugin is not None:
            plugin.fire_event(
                MrBeamEvents.LASER_CUTTER_PROFILE_INITIALIZED,
                dict(),
            )

    return _instance


class LaserCutterProfileService(ProfileService):
    """ Service class for laser cutter profile. """

    DEFAULT_PROFILE_ID = "profile_1"

    def __init__(self, id, profile):
        """Initialize laser cutter profile service.

        Args:
            id (str): The id of the laser cutter profile.
            profile (dict): The profile of the laser cutter.
        """
        super(LaserCutterProfileService, self).__init__(id, profile)
        self._logger = mrb_logger("octoprint.plugins.mrbeam.services.profile.laser_cutter_profile")
