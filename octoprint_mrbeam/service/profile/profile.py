# coding=utf-8
"""
This file is a modified version of the original file from OctoPrint.
The original file is profile.py located in the folder octoprint/printer/profile.py.
The original class was designed to work only with printer profiles and with defined
dictionary structures. This modified version is designed to work with any kind of
profile and with any kind of dictionary structure. The only requirement is that the
profile is a dictionary.
"""

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
    PROFILE_CONFIGURATION_FILE_ENDING = ".profile"

    def __init__(self, id="", default=None):
        self._default = default
        self._id = id
        self._current = None
        self._logger = mrb_logger("octoprint.plugins.mrbeam.service.profile.profile")

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

        settings().set(["profiles", self._id, "defaultProfile"], None, force=True)
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
                settings().set(["profiles", self._id, "default"], self.DEFAULT_PROFILE_ID, force=True)
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
        if (self._current is not None and self._current["id"] == identifier) or settings().get(["profiles", self._id, "default"]) == identifier:
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
            settings().set(["profiles", self._id, "default"], identifier, force=True)
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
        dates += [entry.stat().st_mtime for entry in scandir(self._folder) if entry.name.endswith(self.PROFILE_CONFIGURATION_FILE_ENDING)]
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
        if identifier is not None and identifier not in all_identifiers:
            return

        settings().set(["profiles", self._id, "default"], identifier, force=True)
        settings().save()

    def get_current_or_default(self):
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
            if is_hidden_path(entry.name) or not entry.name.endswith(self.PROFILE_CONFIGURATION_FILE_ENDING):
                continue

            if not entry.is_file():
                continue

            identifier = entry.name[:-len(self.PROFILE_CONFIGURATION_FILE_ENDING)]
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
            except Exception as e:
                self._logger.exception(
                    "Tried to save profile to {path} after migrating it while loading, ran into exception: {e}".format(
                        path=path, e=e))

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
        except Exception as e:
            self._logger.warn(
                "Tried to remove profile from {path}, ran into exception: {e}".format(
                    path=path, e=e))
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
        raise NotImplementedError("Subclasses must implement _migrate_profile")

    def _ensure_valid_profile(self, profile):
        """
        Subclasses must override this method.
        """
        raise NotImplementedError("Subclasses must implement _ensure_valid_profile.")
