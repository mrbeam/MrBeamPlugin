#!/usr/bin/env python
import os
import time


from octoprint.filemanager.storage import LocalFileStorage, StorageError
from octoprint_mrbeam.mrb_logger import mrb_logger


class MrBeamFileStorage(LocalFileStorage):
    def __init__(self, basefolder, create=False):
        LocalFileStorage.__init__(self, basefolder, create)
        self._logger_mrb = mrb_logger(
            "octoprint.plugins.mrbeam.filemanager.mrbFileStorage"
        )

    def remove_multiple_files(self, files):
        """Mostly a copy of OctoPrints (1.3.6) LocalFileStorage.remove_file."""
        metadata_to_remove = {}
        f_count = 0
        ts_start = time.time()

        for path in files:
            path, name = self.sanitize(path)

            file_path = os.path.join(path, name)
            if not os.path.exists(file_path):
                continue
            if not os.path.isfile(file_path):
                self._logger_mrb.warn(
                    "remove_multiple_files(): {name} in {path} is not a file -> skipping".format(
                        name=name, path=path
                    )
                )

            try:
                os.remove(file_path)
                f_count += 1
            except Exception as e:
                self._logger_mrb.error(
                    "Could not delete {name} in {path}, cause: {cause}".format(
                        name=name, path=path, cause=e
                    )
                )
                continue

            # collect for metadata removal
            if path not in metadata_to_remove:
                metadata_to_remove[path] = []
            metadata_to_remove[path].append(name)

        self._remove_metadata_multiple_entry(metadata_to_remove)

        self._logger_mrb.info(
            "remove_multiple_files(): Deleted %s/%s files in %s paths in %.2f sec",
            f_count,
            len(files),
            len(metadata_to_remove.keys()),
            time.time() - ts_start,
        )

    def _remove_metadata_multiple_entry(self, entries):
        """Mostly a copy of OctoPrints (1.3.6)
        LocalFileStorage._remove_metadata_entry."""
        for path in entries.keys():
            with self._get_metadata_lock(path):
                metadata = self._get_metadata(path)

                for name in entries[path]:
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
