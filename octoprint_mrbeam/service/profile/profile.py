# coding=utf-8
from __future__ import absolute_import, division, print_function

import os
import copy
import re
from octoprint_mrbeam.mrb_logger import mrb_logger

try:
    from os import scandir
except ImportError:
    from scandir import scandir

from octoprint.settings import settings
from octoprint.util import dict_merge, dict_sanitize, dict_contains_keys, is_hidden_path


class SaveError(Exception):
    pass


class CouldNotOverwriteError(SaveError):
    pass


class InvalidProfileError(Exception):
    pass


class ProfileService(object):
    """
    Manager for profiles. Offers methods to select the globally used profile and to list, add, remove,
    load and save profiles.

    A profile is a ``dict`` of a certain structure.

    Args:
        default (dict): The default profile to use if no other profile is selected.
        folder (str): The folder to store the profiles in.
    """

    DEFAULT_PROFILE_ID = "_default"

    def __init__(self, id="", default={}):
        self._default = default
        self._id = id
        self._current = None
        self._logger = mrb_logger("octoprint.plugins.mrbeam.service.profile.profile")

        self._logger.info("Initializing profile service for id: {}".format(settings().getBaseFolder("base")))

        self._folder = os.path.join(
            settings().getBaseFolder("base"),
            "profiles",
            self._id
        )
        if not os.path.isdir(self._folder):
            os.makedirs(self._folder)

        self._migrate_old_default_profile()
        self._verify_default_available()

    def _migrate_old_default_profile(self):
        default_overrides = settings().get(["profiles", self._id, "defaultProfile"])
        if not default_overrides:
            return

        if self.exists(self.DEFAULT_PROFILE_ID):
            return

        if not isinstance(default_overrides, dict):
            self._logger.warn(
                "Existing default profile from settings is not a valid profile, refusing to migrate: {!r}".format(
                    default_overrides))
            return

        default_overrides["id"] = self.DEFAULT_PROFILE_ID
        self.save(default_overrides)

        settings().set(["profiles", self._id, "defaultProfile"], None)
        settings().save()

        self._logger.info("Migrated default profile from settings to {}.profile: {!r}".format(self.DEFAULT_PROFILE_ID, default_overrides))

    def _verify_default_available(self):
        default_id = settings().get(["profiles", self._id, "default"])
        if default_id is None:
            default_id = self.DEFAULT_PROFILE_ID

        if not self.exists(default_id):
            if not self.exists(self.DEFAULT_PROFILE_ID):
                if default_id == self.DEFAULT_PROFILE_ID:
                    self._logger.error(
                        "Profile {} does not exist, creating {} again and setting it as default".format(self.DEFAULT_PROFILE_ID, self.DEFAULT_PROFILE_ID))
                else:
                    self._logger.error(
                        "Selected default profile {} and {} do not exist, creating {} again and setting it as default".format(
                            default_id, self.DEFAULT_PROFILE_ID, self.DEFAULT_PROFILE_ID))
                self.save(self._default, allow_overwrite=True, make_default=True)
            else:
                self._logger.error(
                    "Selected default profile {} does not exists, resetting to {}".format(default_id, self.DEFAULT_PROFILE_ID))
                settings().set(["profiles", self._id, "default"], self.DEFAULT_PROFILE_ID)
                settings().save()
            default_id = self.DEFAULT_PROFILE_ID

        profile = self.get(default_id)
        if profile is None:
            self._logger.error("Selected default profile {} is invalid, resetting to default values".format(default_id))
            profile = copy.deepcopy(self._default)
            profile["id"] = default_id
            self.save(self._default, allow_overwrite=True, make_default=True)

    def select(self, identifier):
        if identifier is None or not self.exists(identifier):
            self._current = self.get_default()
            return False
        else:
            self._current = self.get(identifier)
            if self._current is None:
                self._logger.error("Profile {} is invalid, cannot select, falling back to default".format(identifier))
                self._current = self.get_default()
                return False
            else:
                return True

    def deselect(self):
        self._current = None

    def get_all(self):
        return self._load_all()

    def get(self, identifier):
        try:
            if self.exists(identifier):
                return self._load_from_path(self._get_profile_path(identifier))
            else:
                return None
        except InvalidProfileError:
            return None

    def remove(self, identifier):
        if self._current is not None and self._current["id"] == identifier:
            return False
        elif settings().get(["profiles", self._id, "default"]) == identifier:
            return False
        return self._remove_from_path(self._get_profile_path(identifier))

    def save(self, profile, allow_overwrite=False, make_default=False):
        if "id" in profile:
            identifier = profile["id"]
        elif "name" in profile:
            identifier = profile["name"]
        else:
            raise InvalidProfileError("profile must contain either id or name")

        identifier = self._sanitize(identifier)
        profile["id"] = identifier

        self._migrate_profile(profile)
        profile = dict_sanitize(profile, self._default)
        profile = dict_merge(self._default, profile)

        self._save_to_path(self._get_profile_path(identifier), profile, allow_overwrite=allow_overwrite)

        if make_default:
            settings().set(["profiles", self._id, "default"], identifier)
            settings().save()

        if self._current is not None and self._current["id"] == identifier:
            self.select(identifier)
        return self.get(identifier)

    def is_default_unmodified(self):
        default = settings().get(["profiles", self._id, "default"])
        return default is None or default == self.DEFAULT_PROFILE_ID or not self.exists(self.DEFAULT_PROFILE_ID)

    @property
    def profile_count(self):
        return len(self._load_all_identifiers())

    @property
    def last_modified(self):
        dates = [os.stat(self._folder).st_mtime]
        dates += [entry.stat().st_mtime for entry in scandir(self._folder) if entry.name.endswith(".profile")]
        return max(dates)

    def get_default(self):
        default = settings().get(["profiles", self._id, "default"])
        if default is not None and self.exists(default):
            profile = self.get(default)
            if profile is not None:
                return profile
            else:
                self._logger.warn("Default profile {} is invalid, falling back to built-in defaults".format(default))

        return copy.deepcopy(self._default)

    def set_default(self, identifier):
        all_identifiers = self._load_all_identifiers().keys()
        if identifier is not None and not identifier in all_identifiers:
            return

        settings().set(["profiles", self._id, "default"], identifier)
        settings().save()

    def get_current_or_default(self):
        self._logger.info("get_current_or_default: {}".format(self._current))
        if self._current is not None:
            return self._current
        else:
            return self.get_default()

    def get_current(self):
        return self._current

    def exists(self, identifier):
        if identifier is None:
            return False
        else:
            path = self._get_profile_path(identifier)
            return os.path.exists(path) and os.path.isfile(path)

    def _load_all(self):
        all_identifiers = self._load_all_identifiers()
        results = dict()
        for identifier, path in all_identifiers.items():
            try:
                profile = self._load_from_path(path)
            except InvalidProfileError:
                self._logger.warn("Profile {} is invalid, skipping".format(identifier))
                continue

            if profile is None:
                continue

            results[identifier] = dict_merge(self._default, profile)
        return results

    def _load_all_identifiers(self):
        results = dict()
        for entry in scandir(self._folder):
            if is_hidden_path(entry.name) or not entry.name.endswith(".profile"):
                continue

            if not entry.is_file():
                continue

            identifier = entry.name[:-len(".profile")]
            results[identifier] = entry.path
        return results

    def _load_from_path(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            return None

        import yaml
        with open(path) as f:
            profile = yaml.safe_load(f)

        if profile is None or not isinstance(profile, dict):
            raise InvalidProfileError("Profile is None or not a dictionary")

        if self._migrate_profile(profile):
            try:
                self._save_to_path(path, profile, allow_overwrite=True)
            except:
                self._logger.exception(
                    "Tried to save profile to {path} after migrating it while loading, ran into exception".format(
                        path=path))

        profile = self._ensure_valid_profile(profile)

        if not profile:
            self._logger.warn("Invalid profile: %s" % path)
            raise InvalidProfileError()
        return profile

    def _save_to_path(self, path, profile, allow_overwrite=False):
        validated_profile = self._ensure_valid_profile(profile)
        if not validated_profile:
            raise InvalidProfileError()

        if os.path.exists(path) and not allow_overwrite:
            raise SaveError("Profile %s already exists and not allowed to overwrite" % profile["id"])

        from octoprint.util import atomic_write
        import yaml
        try:
            with atomic_write(path, "wb", max_permissions=0o666) as f:
                yaml.safe_dump(profile, f, default_flow_style=False, indent="  ", allow_unicode=True)
        except Exception as e:
            self._logger.exception("Error while trying to save profile %s" % profile["id"])
            raise SaveError("Cannot save profile %s: %s" % (profile["id"], str(e)))

    def _remove_from_path(self, path):
        try:
            os.remove(path)
            return True
        except:
            return False

    def _get_profile_path(self, identifier):
        return os.path.join(self._folder, "%s.profile" % identifier)

    def _sanitize(self, name):
        if name is None:
            return None

        if "/" in name or "\\" in name:
            raise ValueError("name must not contain / or \\")

        import string
        valid_chars = "-_.() {ascii}{digits}".format(ascii=string.ascii_letters, digits=string.digits)
        sanitized_name = ''.join(c for c in name if c in valid_chars)
        sanitized_name = sanitized_name.replace(" ", "_")
        return sanitized_name

    def _migrate_profile(self, profile):
        """
        Subclasses must override this method.
        """
        return False
        # raise NotImplementedError("Subclasses must implement _migrate_profile.")

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
        Subclasses must override this method.
        """
        return profile
        # raise NotImplementedError("Subclasses must implement _ensure_valid_profile.")

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
