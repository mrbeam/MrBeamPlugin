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
LASER_PROFILE_MAP = dict(
    zip(
        LASER_PROFILE_IDENTIFIERS,
        LASER_PROFILES,
    )
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
        default_id = settings().get(self.SETTINGS_PATH_PROFILE_DEFAULT_ID)
        if default_id is None:
            default_id = "_default"

        if not self.exists(default_id):
            if default_id in LASER_PROFILE_IDENTIFIERS:
                # Will select hard coded profiles
                pass
            elif not self.exists("_default"):
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
                settings().set(self.SETTINGS_PATH_PROFILE_DEFAULT_ID, "_default")
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
                # Update derivated profiles using the default profile.
                hard_coded = dict_merge(
                    self._load_default(), LASER_PROFILE_MAP[identifier]
                )
                return dict_merge(hard_coded, file_based_result)
            else:
                return PrinterProfileManager.get(self, identifier)
        except InvalidProfileError:
            return None

    def remove(self, identifier):
        # Overloaded from OP because of printerProfiles path (default_id)
        if self._current is not None and self._current["id"] == identifier:
            return False
        elif settings().get(self.SETTINGS_PATH_PROFILE_DEFAULT_ID) == identifier:
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
        all_identifiers = self._load_all_identifiers().keys()
        if identifier is not None and not identifier in all_identifiers:
            return

        settings().set(self.SETTINGS_PATH_PROFILE_DEFAULT_ID, identifier, force=True)
        settings().save()

    # @logme(output=True)
    def get_current_or_default(self):
        return PrinterProfileManager.get_current_or_default(self)

    def _load_all(self):
        """Extend the file based ``PrinterProfileManager._load_all`` with the few hardcoded ones we have."""
        file_based_profiles = PrinterProfileManager._load_all(self)
        return dict_merge(LASER_PROFILE_MAP, file_based_profiles)

    def _load_default(self, defaultModel=None):
        # Overloaded because of settings path
        default = copy.deepcopy(LASER_PROFILE_DEFAULT)
        profile = self._ensure_valid_profile(default)
        if not profile:
            self._logger.warn("Invalid default profile after applying overrides")
            raise InvalidProfileError()
        return profile

    def _ensure_valid_profile(self, profile):
        # Ensuring that all keys are present is the default behaviour of the OP ``PrinterProfileManager``
        # This ``LaserCutterProfileManager`` can use partially declared profiles, as they are
        # completed using the default profile.
        #
        # # ensure all keys are present
        # if not dict_contains_keys(self.default, profile):
        #     return False

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

    # ~ Extra functionality

    def converted_profiles(self):
        ret = {}

        default = self.get_default()["id"]
        current = self.get_current_or_default()["id"]
        for identifier, profile in self.get_all().items():
            ret[identifier] = copy.deepcopy(profile)
            ret[identifier]["default"] = profile["id"] == default
            ret[identifier]["current"] = profile["id"] == current

        return ret


class Profile(object):
    regex_extruder_offset = re.compile("extruder_offset_([xy])(\d)")
    regex_filament_diameter = re.compile("filament_diameter(\d?)")
    regex_print_temperature = re.compile("print_temperature(\d?)")
    regex_strip_comments = re.compile(";.*$", flags=re.MULTILINE)

    @classmethod
    def from_svgtogcode_ini(cls, path):
        import os

        if not os.path.exists(path) or not os.path.isfile(path):
            return None

        import ConfigParser

        config = ConfigParser.ConfigParser()
        try:
            config.read(path)
        except:
            return None

        arrayified_options = [
            "print_temperature",
            "filament_diameter",
            "start.gcode",
            "end.gcode",
        ]
        translated_options = dict(
            inset0_speed="outer_shell_speed",
            insetx_speed="inner_shell_speed",
            layer0_width_factor="first_layer_width_factor",
            simple_mode="follow_surface",
        )
        translated_options["start.gcode"] = "start_gcode"
        translated_options["end.gcode"] = "end_gcode"
        value_conversions = dict(
            platform_adhesion={
                "None": PlatformAdhesionTypes.NONE,
                "Brim": PlatformAdhesionTypes.BRIM,
                "Raft": PlatformAdhesionTypes.RAFT,
            },
            support={
                "None": SupportLocationTypes.NONE,
                "Touching buildplate": SupportLocationTypes.TOUCHING_BUILDPLATE,
                "Everywhere": SupportLocationTypes.EVERYWHERE,
            },
            support_type={"Lines": SupportTypes.LINES, "Grid": SupportTypes.GRID},
            support_dual_extrusion={
                "Both": SupportDualTypes.BOTH,
                "First extruder": SupportDualTypes.FIRST,
                "Second extruder": SupportDualTypes.SECOND,
            },
        )

        result = dict()
        for section in config.sections():
            if not section in ("profile", "alterations"):
                continue

            for option in config.options(section):
                ignored = False
                key = option

                # try to fetch the value in the correct type
                try:
                    value = config.getboolean(section, option)
                except:
                    # no boolean, try int
                    try:
                        value = config.getint(section, option)
                    except:
                        # no int, try float
                        try:
                            value = config.getfloat(section, option)
                        except:
                            # no float, use str
                            value = config.get(section, option)
                index = None

                for opt in arrayified_options:
                    if key.startswith(opt):
                        if key == opt:
                            index = 0
                        else:
                            try:
                                # try to convert the target index, e.g. print_temperature2 => print_temperature[1]
                                index = int(key[len(opt) :]) - 1
                            except ValueError:
                                # ignore entries for which that fails
                                ignored = True
                        key = opt
                        break
                if ignored:
                    continue

                if key in translated_options:
                    # if the key has to be translated to a new value, do that now
                    key = translated_options[key]

                if key in value_conversions and value in value_conversions[key]:
                    value = value_conversions[key][value]

                if index is not None:
                    # if we have an array to fill, make sure the target array exists and has the right size
                    if not key in result:
                        result[key] = []
                    if len(result[key]) <= index:
                        for n in xrange(index - len(result[key]) + 1):
                            result[key].append(None)
                    result[key][index] = value
                else:
                    # just set the value if there's no array to fill
                    result[key] = value

        # merge it with our default settings, the imported profile settings taking precedence
        return cls.merge_profile(result)

    @classmethod
    def merge_profile(cls, profile, overrides=None):
        import copy

        result = copy.deepcopy(defaults)
        for k in result.keys():
            profile_value = None
            override_value = None

            if k in profile:
                profile_value = profile[k]
            if overrides and k in overrides:
                override_value = overrides[k]

            if profile_value is None and override_value is None:
                # neither override nor profile, no need to handle this key further
                continue

            # just change the result value to the override_value if available, otherwise to the profile_value if
            # that is given, else just leave as is
            if override_value is not None:
                result[k] = override_value
            elif profile_value is not None:
                result[k] = profile_value
        return result

    def __init__(self, profile):
        self.profile = profile

    def get(self, key):
        if key in self.profile:
            return self.profile[key]
        elif key in defaults:
            return defaults[key]
        else:
            return None

    def get_int(self, key, default=None):
        value = self.get(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            return default

    def get_float(self, key, default=None):
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, (str, unicode, basestring)):
            value = value.replace(",", ".").strip()

        try:
            return float(value)
        except ValueError:
            return default

    def get_boolean(self, key, default=None):
        value = self.get(key)
        if value is None:
            return default

        if isinstance(value, bool):
            return value
        elif isinstance(value, (str, unicode, basestring)):
            return (
                value.lower() == "true"
                or value.lower() == "yes"
                or value.lower() == "on"
                or value == "1"
            )
        elif isinstance(value, (int, float)):
            return value > 0
        else:
            return value == True

    def get_microns(self, key, default=None):
        value = self.get_float(key, default=None)
        if value is None:
            return default
        return int(value * 1000)

    def convert_to_engine(self):

        settings = {
            "--engraving-laser-speed": self.get_int("speed"),
            "--laser-intensity": self.get_int("intensity"),
            "--beam-diameter": self.get_float("beam_diameter"),
            "--img-intensity-white": self.get_int("intensity_white"),
            "--img-intensity-black": self.get_int("intensity_black"),
            "--img-speed-white": self.get_int("feedrate_white"),
            "--img-speed-black": self.get_int("feedrate_black"),
            "--pierce-time": self.get_float("pierce_time"),
            "--contrast": self.get_float("img_contrast"),
            "--sharpening": self.get_float("img_sharpening"),
            "--img-dithering": self.get_boolean("img_dithering"),
        }

        return settings

    def convert_to_engine2(self):
        # engrave is mirrored fill area, needs to be removed in next iteration
        settings = {
            "engraving_laser_speed": self.get_int("speed"),
            "laser_intensity": self.get_int("intensity"),
            "beam_diameter": self.get_float("beam_diameter"),
            "intensity_white": self.get_int("intensity_white"),
            "intensity_black": self.get_int("intensity_black"),
            "speed_white": self.get_int("feedrate_white"),
            "speed_black": self.get_int("feedrate_black"),
            "pierce_time": self.get_float("pierce_time"),
            "contrast": self.get_float("img_contrast"),
            "sharpening": self.get_float("img_sharpening"),
            "dithering": self.get_boolean("img_dithering"),
            "fill_areas": self.get_boolean("fill_areas"),
            "engrave": self.get_boolean("fill_areas"),
            "set_passes": self.get_int("set_passes"),
            "cut_outlines": self.get_boolean("cut_outlines"),
            "cross_fill": self.get_boolean("cross_fill"),
            "fill_angle": self.get_float("fill_angle"),
            "fill_spacing": self.get_float("fill_spacing"),
            "svgDPI": self.get_float("svgDPI"),
        }

        return settings
