#!/usr/bin/env python
import os

from octoprint.filemanager import FileManager
from octoprint.filemanager.destinations import FileDestinations
from octoprint.filemanager.storage import LocalFileStorage, StorageError
from octoprint.events import eventManager, Events
from octoprint_mrbeam.mrb_logger import mrb_logger


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
        def __init__(self, file_name, content):
            self.filename = file_name
            self.content = content

        def save(self, absolute_dest_path):
            with open(absolute_dest_path, "wb") as d:
                d.write(self.content.encode("UTF-8"))

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

    def add_file_to_design_library(self, file_name, content, sanitize_name=False):
        try:
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
        except Exception as e:
            self._logger_mrb.exception(
                "Exception in MrbFileManager.add_file_to_design_library() ", test=True
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

            # TODO each deletion causes a filemanager push update -> slow.
            for f in sorted_by_age[:-num_files_to_keep]:
                # self.remove_file(FileDestinations.LOCAL, f[1])
                # def remove_file(self, destination, path):
                destination = FileDestinations.LOCAL
                path = f[1]
                self._logger_mrb.info("ANDYTEST _delete_files_by_age() path: %s", path)
                queue_entry = self._analysis_queue_entry(destination, path)
                self._analysis_queue.dequeue(queue_entry)
                # self._storage(destination).remove_file(path)
                self._logger_mrb.info(
                    "ANDYTEST _delete_files_by_age() append path: %s", path
                )
                files_to_delete.append(path)

                # _, name = self._storage(destination).split_path(path)
                # eventManager().fire(Events.FILE_REMOVED, dict(storage=destination,
                #                                               path=path,
                #                                               name=name,
                #                                               type=get_file_type(name)))

            self._logger_mrb.info(
                "ANDYTEST _delete_files_by_age() deleting files: %s",
                len(files_to_delete),
            )
            self._storage(destination).remove_multiple_files(files_to_delete)
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


class MrBeamFileStorage(LocalFileStorage):
    def __init__(self, basefolder, create=False):
        self._logger_mrb = mrb_logger(
            "octoprint.plugins.mrbeam.filemanager.mrbFileStorage"
        )

        LocalFileStorage.__init__(self, basefolder, create)

    def remove_multiple_files(self, files):
        self._logger_mrb.info("ANDYTEST remove_multiple_files: hello world")

        metadata_to_remove = {}

        for path in files:
            path, name = self.sanitize(path)
            self._logger_mrb.info(
                "ANDYTEST remove_multiple_files: path: %s, name: %s", path, name
            )

            file_path = os.path.join(path, name)
            if not os.path.exists(file_path):
                return
            if not os.path.isfile(file_path):
                raise StorageError(
                    "{name} in {path} is not a file".format(**locals()),
                    code=StorageError.INVALID_FILE,
                )

            try:
                os.remove(file_path)
            except Exception as e:
                raise StorageError(
                    "Could not delete {name} in {path}".format(**locals()), cause=e
                )
            # metadata_to_remove.append((path, name))
            if path not in metadata_to_remove:
                metadata_to_remove[path] = []
            metadata_to_remove[path].append(name)

        # self._remove_metadata_entry(path, name)

    def _remove_metadata_multiple_entry(self, entries):

        for path in entries.keys():
            self._logger_mrb.info(
                "ANDYTEST _remove_metadata_multiple_entry: path: %s", path
            )

            with self._get_metadata_lock(path):
                metadata = self._get_metadata(path)

                for name in entries[path]:
                    self._logger_mrb.info(
                        "ANDYTEST _remove_metadata_multiple_entry: name: %s", name
                    )

                    if not name in metadata:
                        continue

                    if "hash" in metadata[name]:
                        hash = metadata[name]["hash"]
                        for m in metadata.values():
                            if not "links" in m:
                                continue
                            links_hash = (
                                lambda link: "hash" in link
                                and link["hash"] == hash
                                and "rel" in link
                                and (
                                    link["rel"] == "model"
                                    or link["rel"] == "machinecode"
                                )
                            )
                            m["links"] = [
                                link for link in m["links"] if not links_hash(link)
                            ]

                    del metadata[name]
                self._save_metadata(path, metadata)
