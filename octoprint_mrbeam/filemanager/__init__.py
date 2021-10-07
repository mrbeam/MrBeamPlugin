#!/usr/bin/env python
import os

from octoprint.filemanager import FileManager
from octoprint.filemanager.destinations import FileDestinations
from octoprint.events import eventManager, Events
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.filemanager.file_storage import MrBeamFileStorage


# singleton
_instance = None


def mrbFileManager(plugin):
    global _instance
    if _instance is None:
        _instance = MrbFileManager(plugin)
    return _instance


class MrbFileManager(FileManager):
    MAX_HISTORY_FILES = 25  # TODO fetch from settings
    MAX_GCODE_FILES = 25  # TODO fetch from settings

    FILE_EXTENSIONS_SVG = ["svg"]
    FILE_EXTENSIONS_HISTORY = ["mrb"]
    FILE_EXTENSIONS_GCODE = ["g", "gc", "gco", "gcode", "nc"]

    class File:
        def __init__(self, file_name, content, binary=False):
            self.filename = file_name
            if binary == True:
                self.content = content
            else:
                self.content = content.encode("UTF-8")

        def save(self, absolute_dest_path):
            with open(absolute_dest_path, "wb") as d:
                d.write(self.content)

    def __init__(self, plugin):
        self._plugin = plugin
        self._logger_mrb = mrb_logger("octoprint.plugins.mrbeam.filemanager")
        self._settings = plugin._settings

        storage_managers = dict()
        storage_managers[FileDestinations.LOCAL] = MrBeamFileStorage(
            self._plugin._settings.getBaseFolder("uploads")
        )

        FileManager.__init__(
            self,
            self._plugin._analysis_queue,
            self._plugin._slicing_manager,
            self._plugin.laserCutterProfileManager,
            initial_storage_managers=storage_managers,
        )

    def add_file_to_design_library(
        self, file_name, content, sanitize_name=False, binary=False
    ):
        try:
            if sanitize_name:
                file_name = self._sanitize_file_name(file_name)
            content = self._sanitize_content(file_name, content)

            file_obj = self.File(file_name, content, binary)
            self.add_file(
                FileDestinations.LOCAL,
                file_name,
                file_obj,
                links=None,
                allow_overwrite=True,
            )
        except Exception as e:
            self._logger_mrb.exception(
                "Exception in MrbFileManager.add_file_to_design_library() "
            )
            raise e

    def delete_old_files(self):
        try:
            self.delete_old_history_files()
            if self._settings.get(["gcodeAutoDeletion"]):
                self.delete_old_gcode_files()
        except Exception as e:
            self._logger_mrb.exception("Exception in delete_old_files()")
            raise e

    def delete_old_history_files(self):
        mrb_filter_func = lambda entry, entry_data: self._is_history_file(entry)
        resp = self.list_files(path="", filter=mrb_filter_func, recursive=True)
        files = resp[FileDestinations.LOCAL]

        self._delete_files_by_age(files, self.MAX_HISTORY_FILES)

    def delete_old_gcode_files(self):
        mrb_filter_func = lambda entry, entry_data: self._is_gcode_file(entry)
        resp = self.list_files(path="", filter=mrb_filter_func, recursive=True)
        files = resp[FileDestinations.LOCAL]

        self._delete_files_by_age(files, self.MAX_GCODE_FILES)

    def _delete_files_by_age(self, files, num_files_to_keep=0):
        if len(files) > num_files_to_keep:
            removals = []
            for key in files:
                f = files[key]
                tpl = (
                    self.last_modified(FileDestinations.LOCAL, path=f["path"]),
                    f["path"],
                )
                removals.append(tpl)
            sorted_by_age = sorted(removals, key=lambda tpl: tpl[0])

            files_to_delete = []
            for _, path in sorted_by_age[:-num_files_to_keep]:
                queue_entry = self._analysis_queue_entry(FileDestinations.LOCAL, path)
                self._analysis_queue.dequeue(queue_entry)
                files_to_delete.append(path)

                # we do not send this event and hope it's fine
                # eventManager().fire(Events.FILE_REMOVED, dict(storage=destination,
                #                                               path=path,
                #                                               name=name,
                #                                               type=get_file_type(name)))

            self._storage(FileDestinations.LOCAL).remove_multiple_files(files_to_delete)
            eventManager().fire(Events.UPDATED_FILES, dict(type="printables"))

    @staticmethod
    def _is_history_file(entry):
        _, extension = os.path.splitext(entry)
        extension = extension[1:].lower()
        return extension in MrbFileManager.FILE_EXTENSIONS_HISTORY

    @staticmethod
    def _is_gcode_file(entry):
        _, extension = os.path.splitext(entry)
        extension = extension[1:].lower()
        return extension in MrbFileManager.FILE_EXTENSIONS_GCODE

    @staticmethod
    def _sanitize_content(file_name, content):
        _, extension = os.path.splitext(file_name)
        extension = extension[1:].lower()
        if (
            extension
            in MrbFileManager.FILE_EXTENSIONS_SVG
            + MrbFileManager.FILE_EXTENSIONS_GCODE
            + MrbFileManager.FILE_EXTENSIONS_HISTORY
        ):
            # TODO stripping non-ascii is a hack - svg contains lots of non-ascii in <text> tags. Fix this!
            content = "".join(i for i in content if ord(i) < 128)
        return content

    def _sanitize_file_name(self, file_name):
        file_name = self.sanitize_name(
            destination=FileDestinations.LOCAL, name=file_name
        )

        return file_name
