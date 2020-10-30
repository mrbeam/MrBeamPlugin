#!/usr/bin/env python
import os

from octoprint.filemanager import FileManager
from octoprint.filemanager.destinations import FileDestinations
from octoprint.filemanager.storage import LocalFileStorage


# singleton
_instance = None


def mrbFileManager(plugin):
    global _instance
    if _instance is None:
        _instance = MrbFileManager(plugin)
    return _instance


class MrbFileManager(FileManager):
    class File:
        def __init__(self, file_name, content):
            self.filename = file_name
            self.content = content

        def save(self, absolute_dest_path):
            with open(absolute_dest_path, "w") as d:
                d.write(self.content)
                d.close()

    def __init__(self, plugin):
        self._plugin = plugin
        storage_managers = dict()
        storage_managers[FileDestinations.LOCAL] = LocalFileStorage(
            self._plugin._settings.getBaseFolder("uploads")
        )

        FileManager.__init__(
            self,
            self._plugin._analysis_queue,
            self._plugin._slicing_manager,
            self._plugin.laserCutterProfileManager,
            initial_storage_managers=storage_managers,
        )

    def add_file_to_design_library(self, file_name, content, sanitize_name=False):
        if sanitize_name:
            file_name = self._sanitize_file_name(file_name)
        content = self._sanitize_content(file_name, content)

        file_obj = self.File(file_name, content)
        self.add_file(
            FileDestinations.LOCAL,
            file_name,
            file_obj,
            links=None,
            allow_overwrite=True,
        )

    def _sanitize_content(self, file_name, content):
        _, extension = os.path.splitext(file_name)
        if extension == ".svg":
            # TODO stripping non-ascii is a hack - svg contains lots of non-ascii in <text> tags. Fix this!
            content = "".join(i for i in content if ord(i) < 128)
        return content

    def _sanitize_file_name(self, file_name):
        file_name = self.sanitize_name(
            destination=FileDestinations.LOCAL, name=file_name
        )

        return file_name
