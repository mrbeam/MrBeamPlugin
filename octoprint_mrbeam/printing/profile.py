# coding=utf-8
from __future__ import absolute_import

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"


import os
import copy
import re
import collections

from octoprint.printer.profile import PrinterProfileManager
from octoprint.util import dict_merge, dict_clean, dict_contains_keys
from octoprint.settings import settings
from octoprint_mrbeam.mrb_logger import mrb_logger

from . import profiles

# singleton
_instance = None


def laserCutterProfileManager():
    global _instance
    if _instance is None:
        _instance = LaserCutterProfileManager()
    return _instance


defaults = dict(
    # general settings
    svgDPI=90,
    pierce_time=0,
    # vector settings
    speed=300,
    intensity=500,
    fill_areas=False,
    engrave=False,
    set_passes=1,
    cut_outlines=True,
    cross_fill=False,
    fill_angle=0,
    fill_spacing=0.25,
    # pixel settings
    beam_diameter=0.25,
    intensity_white=0,
    intensity_black=500,
    feedrate_white=1500,
    feedrate_black=250,
    img_contrast=1.0,
    img_sharpening=1.0,
    img_dithering=False,
    multicolor="",
)


class SaveError(Exception):
    pass


class CouldNotOverwriteError(SaveError):
    pass


class InvalidProfileError(Exception):
    pass


LASER_PROFILE_DEFAULT = profiles.default.profile
LASER_PROFILE_2C = profiles.mrb2c.profile
LASER_PROFILE_2U = profiles.mrb2u.profile
LASER_PROFILE_DUMMY = profiles.dummy.profile

LASER_PROFILES = (
    LASER_PROFILE_DEFAULT,
    LASER_PROFILE_2C,
    LASER_PROFILE_2U,
    LASER_PROFILE_DUMMY,
)

LASER_PROFILE_IDENTIFIERS = (
    "_default",
    "MrBeam2C",
    "MrBeam2U",
    "Dummy Laser",
)


class LaserCutterProfileManager(PrinterProfileManager):

    SETTINGS_PATH_PROFILE_DEFAULT_ID = ["lasercutterProfiles", "default"]
    SETTINGS_PATH_PROFILE_DEFAULT_PROFILE = ["lasercutterProfiles", "defaultProfile"]
    # SETTINGS_PATH_PROFILE_CURRENT_ID = ['lasercutterProfiles', 'current']

    default = LASER_PROFILE_DEFAULT

    def __init__(self):
        _laser_cutter_profile_folder = (
            settings().getBaseFolder("printerProfiles") + "/lasercutterprofiles"
        )
        if not os.path.exists(_laser_cutter_profile_folder):
            os.makedirs(_laser_cutter_profile_folder)
        PrinterProfileManager.__init__(self)
        self._folder = _laser_cutter_profile_folder
        self._logger = mrb_logger(__name__)

    def _migrate_old_default_profile(self):
        # TODO
        pass

    def _verify_default_available(self):
        # Overloaded from OP because of printerProfiles path ``default_id``
        default_id = settings().get(SETTINGS_PATH_PROFILE_DEFAULT_ID)
        if default_id is None:
            default_id = "_default"

        if not self.exists(default_id):
            if not self.exists("_default"):
                if default_id == "_default":
                    self._logger.error(
                        "Profile _default does not exist, creating _default again and setting it as default"
                    )
                else:
                    self._logger.error(
                        "Selected default profile {} and _default do not exist, creating _default again and setting it as default".format(
                            default_id
                        )
                    )
                self.save(
                    self.__class__.default, allow_overwrite=True, make_default=True
                )
            else:
                self._logger.error(
                    "Selected default profile {} does not exists, resetting to _default".format(
                        default_id
                    )
                )
                settings().set(SETTINGS_PATH_PROFILE_DEFAULT_ID, "_default")
                settings().save()
            default_id = "_default"

        profile = self.get(default_id)
        if profile is None:
            self._logger.error(
                "Selected default profile {} is invalid, resetting to default values".format(
                    default_id
                )
            )
            profile = copy.deepcopy(self.__class__.default)
            profile["id"] = default_id
            self.save(self.__class__.default, allow_overwrite=True, make_default=True)

    def get(self, identifier):
        """Extend the file based ``PrinterProfileManager.get`` with the few hardcoded ones we have."""
        try:
            if identifier == "_default":
                return self._load_default()
            elif identifier in LASER_PROFILE_IDENTIFIERS:
                file_based_result = PrinterProfileManager.get(self, identifier)
                hard_coded = {}  # FIXME
                return dict_merge(hard_coded, file_based_result)
            else:
                return PrinterProfileManager.get(self, identifier)
        except InvalidProfileError:
            return None

    def remove(self, identifier):
        # Overloaded from OP because of printerProfiles path (default_id)
        if self._current is not None and self._current["id"] == identifier:
            return False
        elif settings().get(SETTINGS_PATH_PROFILE_DEFAULT_ID) == identifier:
            return False
        return self._remove_from_path(self._get_profile_path(identifier))

    def save(self, profile, allow_overwrite=False, make_default=False):
        """
        Saves given profile to file.
        /!\ make_default uses the octoprint printerProfile path.
        :param profile:
        :param allow_overwrite:
        :param make_default:
        :return:
        """
        profile = PrinterProfileManager.save(
            self, profile, allow_overwrite, make_default=False
        )
        # TODO : I don't really understand what this is for - investigate
        # if identifier == "_default":
        #     default_profile = dict_merge(self._load_default(), profile)
        #     if not self._ensure_valid_profile(default_profile):
        #         raise InvalidProfileError()

        #     settings().set(
        #         self.SETTINGS_PATH_PROFILE_DEFAULT_PROFILE,
        #         default_profile,
        #         defaults=dict(
        #             lasercutterprofiles=dict(defaultProfile=LASER_PROFILE_DEFAULT)
        #         ),
        #     )
        #     settings().save()
        # else:
        #     self._save_to_path(
        #         self._get_profile_path(identifier),
        #         profile,
        #         allow_overwrite=allow_overwrite,
        #     )

        # ``PrinterProfileManager.save`` forces profile to use the key ``id``
        # to reference the profile identifier
        identifier = profile["id"]
        if make_default:
            self.set_default(identifier)

        # Not sure if we want to sync to OP's PrinterprofileManager
        # _mrbeam_plugin_implementation._printer_profile_manager.save(profile, allow_overwrite, make_default)

        return self.get(identifier)

    def is_default_unmodified(self):
        # Overloaded because of settings path and barely used by OP
        return True

    def get_default(self):
        # Overloaded because of settings path
        default = settings().get(self.SETTINGS_PATH_PROFILE_DEFAULT_ID)
        if default is not None and self.exists(default):
            profile = self.get(default)
            if profile is not None:
                return profile

        return copy.deepcopy(self.__class__.default)

    def set_default(self, identifier):
        # Overloaded because of settings path
        all_identifiers = self._load_file_name_identifiers().keys()
        if identifier is not None and not identifier in all_identifiers:
            return

        settings().set(self.SETTINGS_PATH_PROFILE_DEFAULT_ID, identifier, force=True)
        settings().save()

    def _load_all(self):
        """Extend the file based ``PrinterProfileManager._load_all`` with the few hardcoded ones we have."""
        file_based_profiles = PrinterProfileManager._load_all(self)
        fallback_profiles = dict(zip(LASER_PROFILES, LASER_PROFILE_IDENTIFIERS))
        return dict_merge(fallback_profiles, file_based_profiles)

    def _load_default(self, defaultModel=None):
        default = copy.deepcopy(LASER_PROFILE_DEFAULT)
        profile = self._ensure_valid_profile(default)
        if not profile:
            self._logger.warn("Invalid default profile after applying overrides")
            raise InvalidProfileError()
        return profile

    def _ensure_valid_profile(self, profile):
        # # ensure all keys are present
        if not dict_contains_keys(self.default, profile):
            return False

        # conversion helper
        def convert_value(profile, path, converter):
            value = profile
            for part in path[:-1]:
                if not isinstance(value, dict) or not part in value:
                    raise RuntimeError(
                        "%s is not contained in profile" % ".".join(path)
                    )
                value = value[part]

            if not isinstance(value, dict) or not path[-1] in value:
                raise RuntimeError("%s is not contained in profile" % ".".join(path))

            value[path[-1]] = converter(value[path[-1]])

        # convert ints
        for path in (
            ("axes", "x", "speed"),
            ("axes", "y", "speed"),
            ("axes", "z", "speed"),
        ):
            try:
                convert_value(profile, path, int)
            except:
                return False

        # convert floats
        for path in (("volume", "width"), ("volume", "depth"), ("volume", "height")):
            try:
                convert_value(profile, path, float)
            except:
                return False

        # convert booleans
        for path in (
            ("axes", "x", "inverted"),
            ("axes", "y", "inverted"),
            ("axes", "z", "inverted"),
        ):
            try:
                convert_value(profile, path, bool)
            except:
                return False

        return profile
