from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.service.profile.profile import ProfileService
from octoprint_mrbeam.model.laser_cutter_profile import LaserCutterProfileModel
from octoprint_mrbeam.constant.profile.laser_cutter import default_profile
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.enums.laser_cutter_mode import LaserCutterModeEnum

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

    DEFAULT_PROFILE_ID = LaserCutterModeEnum.DEFAULT.value

    def __init__(self, id, profile):
        """Initialize laser cutter profile service.

        Args:
            id (str): The id of the profile.
            profile (dict): The profile of the laser cutter.
        """
        super(LaserCutterProfileService, self).__init__(id, profile)
        self._logger = mrb_logger("octoprint.plugins.mrbeam.services.profile.laser_cutter_profile")

    def _migrate_profile(self, profile):
        """Migrate the profile to the latest version.

        Args:
            profile (dict): The profile of the laser cutter.

        Returns:
            Boolean: True if the profile was migrated, False otherwise.
        """
        self._logger.debug("Checking if profile needs to be migrated: %s", profile)
        return False

        # Implementation Sample:

        # # make sure profile format is up to date
        # modified = False
        #
        # if "volume" in profile and "formFactor" in profile["volume"] and not "origin" in profile["volume"]:
        # 	profile["volume"]["origin"] = BedOrigin.CENTER if profile["volume"]["formFactor"] == BedTypes.CIRCULAR else BedOrigin.LOWERLEFT
        # 	modified = True
        #
        # if "volume" in profile and not "custom_box" in profile["volume"]:
        # 	profile["volume"]["custom_box"] = False
        # 	modified = True
        #
        # if "extruder" in profile and not "sharedNozzle" in profile["extruder"]:
        # 	profile["extruder"]["sharedNozzle"] = False
        # 	modified = True
        #
        # if "extruder" in profile and "sharedNozzle" in profile["extruder"] and profile["extruder"]["sharedNozzle"]:
        # 	profile["extruder"]["offsets"] = [(0.0, 0.0)]
        # 	modified = True
        #
        # return modified

    def _ensure_valid_profile(self, profile):
        """
        Ensure that the profile is valid.

        Args:
            profile (dict): The profile of the laser cutter.

        Returns:
            dict: The profile of the laser cutter.
        """
        return profile

        # Implementation Sample:

        # # ensure all keys are present
        # if not dict_contains_keys(self._default, profile):
        #     self._logger.warn("Profile invalid, missing keys. Expected: {expected!r}. Actual: {actual!r}".format(
        #         expected=self._default.keys(), actual=profile.keys()))
        #     return False
        #
        # # conversion helper
        # def convert_value(profile, path, converter):
        #     value = profile
        #     for part in path[:-1]:
        #         if not isinstance(value, dict) or not part in value:
        #             raise RuntimeError("%s is not contained in profile" % ".".join(path))
        #         value = value[part]
        #
        #     if not isinstance(value, dict) or not path[-1] in value:
        #         raise RuntimeError("%s is not contained in profile" % ".".join(path))
        #
        #     value[path[-1]] = converter(value[path[-1]])
        #
        # # convert ints
        # for path in (("extruder", "count"), ("axes", "x", "speed"), ("axes", "y", "speed"), ("axes", "z", "speed")):
        #     try:
        #         convert_value(profile, path, int)
        #     except Exception as e:
        #         self._logger.warn(
        #             "Profile has invalid value for path {path!r}: {msg}".format(path=".".join(path), msg=str(e)))
        #         return False
        #
        # # convert floats
        # for path in (("volume", "width"), ("volume", "depth"), ("volume", "height"), ("extruder", "nozzleDiameter")):
        #     try:
        #         convert_value(profile, path, float)
        #     except Exception as e:
        #         self._logger.warn(
        #             "Profile has invalid value for path {path!r}: {msg}".format(path=".".join(path), msg=str(e)))
        #         return False
        #
        # # convert booleans
        # for path in (
        # ("axes", "x", "inverted"), ("axes", "y", "inverted"), ("axes", "z", "inverted"), ("extruder", "sharedNozzle")):
        #     try:
        #         convert_value(profile, path, bool)
        #     except Exception as e:
        #         self._logger.warn(
        #             "Profile has invalid value for path {path!r}: {msg}".format(path=".".join(path), msg=str(e)))
        #         return False
        #
        # # validate form factor
        # if not profile["volume"]["formFactor"] in BedTypes.values():
        #     self._logger.warn("Profile has invalid value volume.formFactor: {formFactor}".format(
        #         formFactor=profile["volume"]["formFactor"]))
        #     return False
        #
        # # validate origin type
        # if not profile["volume"]["origin"] in BedOrigin.values():
        #     self._logger.warn(
        #         "Profile has invalid value in volume.origin: {origin}".format(origin=profile["volume"]["origin"]))
        #     return False
        #
        # # ensure origin and form factor combination is legal
        # if profile["volume"]["formFactor"] == BedTypes.CIRCULAR and not profile["volume"]["origin"] == BedOrigin.CENTER:
        #     profile["volume"]["origin"] = BedOrigin.CENTER
        #
        # # force width and depth of volume to be identical for circular beds, with width being the reference
        # if profile["volume"]["formFactor"] == BedTypes.CIRCULAR:
        #     profile["volume"]["depth"] = profile["volume"]["width"]
        #
        # # if we have a custom bounding box, validate it
        # if profile["volume"]["custom_box"] and isinstance(profile["volume"]["custom_box"], dict):
        #     if not len(profile["volume"]["custom_box"]):
        #         profile["volume"]["custom_box"] = False
        #
        #     else:
        #         default_box = self._default_box_for_volume(profile["volume"])
        #         for prop, limiter in (("x_min", min), ("y_min", min), ("z_min", min),
        #                               ("x_max", max), ("y_max", max), ("z_max", max)):
        #             if prop not in profile["volume"]["custom_box"] or profile["volume"]["custom_box"][prop] is None:
        #                 profile["volume"]["custom_box"][prop] = default_box[prop]
        #             else:
        #                 value = profile["volume"]["custom_box"][prop]
        #                 try:
        #                     value = limiter(float(value), default_box[prop])
        #                     profile["volume"]["custom_box"][prop] = value
        #                 except:
        #                     self._logger.warn(
        #                         "Profile has invalid value in volume.custom_box.{}: {!r}".format(prop, value))
        #                     return False
        #
        #         # make sure we actually do have a custom box and not just the same values as the
        #         # default box
        #         for prop in profile["volume"]["custom_box"]:
        #             if profile["volume"]["custom_box"][prop] != default_box[prop]:
        #                 break
        #         else:
        #             # exactly the same as the default box, remove custom box
        #             profile["volume"]["custom_box"] = False
        #
        # # validate offsets
        # offsets = []
        # for offset in profile["extruder"]["offsets"]:
        #     if not len(offset) == 2:
        #         self._logger.warn("Profile has an invalid extruder.offsets entry: {entry!r}".format(entry=offset))
        #         return False
        #     x_offset, y_offset = offset
        #     try:
        #         offsets.append((float(x_offset), float(y_offset)))
        #     except:
        #         self._logger.warn(
        #             "Profile has an extruder.offsets entry with non-float values: {entry!r}".format(entry=offset))
        #         return False
        # profile["extruder"]["offsets"] = offsets
        #
        # return profile

        # @staticmethod
        # def _default_box_for_volume(volume):
        #     if volume["origin"] == BedOrigin.CENTER:
        #         half_width = volume["width"] / 2.0
        #         half_depth = volume["depth"] / 2.0
        #         return dict(x_min=-half_width,
        #                     x_max=half_width,
        #                     y_min=-half_depth,
        #                     y_max=half_depth,
        #                     z_min=0.0,
        #                     z_max=volume["height"])
        #     else:
        #         return dict(x_min=0.0,
        #                     x_max=volume["width"],
        #                     y_min=0.0,
        #                     y_max=volume["depth"],
        #                     z_min=0.0,
        #                     z_max=volume["height"])
