#!/usr/bin/env python

import requests
import os
import threading
import time

try:
    from octoprint_mrbeam.mrb_logger import mrb_logger
except:
    import logging

TOKEN_URL = "https://europe-west1-mrb-analytics.cloudfunctions.net/get_upload_tocken"
UPLOAD_URL_TEMPLATE = "https://storage-upload.googleapis.com/{bucket}"

DELETE_FILES_AFTER_UPLOAD = True


class FileUploader:
    STATUS_INIT = "init"
    STATUS_VERIFY = "verify"
    STATUS_GET_TOKEN = "get_token"
    STATUS_UPLOAD = "upload_file"
    STATUS_REMOVE = "remove_file"
    STATUS_DONE = "done"

    def __init__(self, plugin, directory, file, upload_type, lock):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.uploader")
        self._plugin = plugin
        self.directory = directory
        self.file = file
        self.upload_type = upload_type
        self.delete_on_success = DELETE_FILES_AFTER_UPLOAD
        self.err_state = False
        self.worker = None
        self._lock = lock

        self.status = dict(
            file=self.file,
            status=None,
            succ=None,
            err=None,
            remote_name=None,
            ts=-1,
            duration=0,
        )

        self._start_uploader_thread()

    def is_active(self):
        return self.worker is not None and self.worker.is_alive()

    def _start_uploader_thread(self):
        if self.worker is None or not self.worker.is_alive():
            self.worker = threading.Thread(target=self._upload_and_delete_file)
            self.worker.name = (
                self.__class__.__name__
            )  # Gets the name of the current class
            self.worker.daemon = True  # !!!!
            self.worker.start()
        return self

    def _upload_and_delete_file(self):
        try:
            self._logger.debug("{} upload starting...".format(self.upload_type))
            self.status["state"] = self.STATUS_INIT
            self.status["ts"] = time.time()

            try:
                if self._file_exists():
                    with self._lock:
                        token_data = self.get_token()
                        self._upload_file(token_data)
                        self._remove_file()
                        self._successful_upload_end()

                else:
                    self._unsuccessful_upload_end(
                        "{} does not exist".format(self.file), raise_except=False
                    )

            except Exception as e:
                self._unsuccessful_upload_end(e)
        except Exception as e:
            self._logger.exception(
                "Exception during _upload_and_delete_file: {}".format(e)
            )

    def _successful_upload_end(self):
        self.status["state"] = self.STATUS_DONE
        self.status["succ"] = True
        self.status["duration"] = (
            time.time() - self.status["ts"] if self.status["ts"] > 0 else -1
        )

        self._logger.info(
            "{up_type} file upload successful! - Status: {status}".format(
                up_type=self.upload_type, status=self.status
            )
        )

    def _unsuccessful_upload_end(self, err, raise_except=True):
        self.status["err"] = err
        self.status["succ"] = False
        self.status["duration"] = (
            time.time() - self.status["ts"] if self.status["ts"] > 0 else -1
        )

        if raise_except:
            self._logger.exception(
                "{up_type} file upload was not successful: {err} - Status: {status}".format(
                    up_type=self.upload_type, err=err, status=self.status
                )
            )
        else:
            self._logger.info(
                "{up_type} file upload was not successful: {err} - Status: {status}".format(
                    up_type=self.upload_type, err=err, status=self.status
                )
            )

    def get_token(self):
        self.status["state"] = self.STATUS_GET_TOKEN

        try:
            params = self._get_system_properties()
            params["type"] = self.upload_type

            r = requests.get(TOKEN_URL, params=params)
            if r.status_code == requests.codes.ok:
                token_data = r.json()
                self.status["remote_name"] = token_data.get("key", None)
            else:
                raise Exception("status_code {}".format(r.status_code))

            return token_data

        except requests.ConnectionError as ce:
            raise Exception("ConnectionError during get_token: {}".format(ce))

        except Exception as e:
            raise Exception("Exception during get_token: {}".format(e))

    def _upload_file(self, token_data):
        self.status["state"] = self.STATUS_UPLOAD

        try:
            upload_url = UPLOAD_URL_TEMPLATE.format(bucket=token_data["bucket"])
            post_params = token_data["request_params"]
            files = {"file": open(self.file, "rb")}

            r = requests.post(upload_url, data=post_params, files=files)
            if r.status_code not in (requests.codes.ok, requests.codes.no_content):
                raise Exception("status_code {}".format(r.status_code))

            self._logger.info("{} uploaded!".format(self.file))

        except Exception as e:
            raise Exception("Exception during _upload_file: {}".format(e))

    def _remove_file(self):
        self.status["state"] = self.STATUS_REMOVE

        try:
            if self.delete_on_success:
                os.remove(self.file)
                self._logger.debug("{} removed!".format(self.file))
            else:
                new_file = os.path.join(
                    os.path.dirname(self.file),
                    "_{}".format(os.path.basename(self.file)),
                )
                os.rename(self.file, new_file)
                self._logger.debug(
                    "{} file renamed to: {}".format(self.upload_type, new_file)
                )
        except Exception as e:
            raise Exception("Exception during _remove_file: {}".format(e))

    def _file_exists(self):
        exists = True
        self.status["state"] = self.STATUS_VERIFY
        if not os.path.isfile(self.file):
            self.status["err"] = "File not found"
            exists = False
        return exists

    def _get_system_properties(self):
        return dict(
            env=self._plugin.get_env(),
            version=self._plugin.get_plugin_version(),
            name=self._plugin.getHostname(),
            serial=self._plugin.getSerialNum(),
        )


class AnalyticsFileUploader(FileUploader):
    _instance = None

    def __init__(self, plugin, analytics_lock):
        self._settings = plugin._settings
        self._analytics_handler = plugin.analytics_handler

        FileUploader.__init__(
            self,
            plugin,
            directory=self._analytics_handler.analytics_folder,
            file=self._analytics_handler.analytics_file,
            upload_type="analytics",
            lock=analytics_lock,
        )

    @staticmethod
    def upload_now(plugin, analytics_lock):
        try:
            if (
                AnalyticsFileUploader._instance is None
                or not AnalyticsFileUploader._instance.is_active()
            ):
                AnalyticsFileUploader._instance = AnalyticsFileUploader(
                    plugin, analytics_lock
                )
                AnalyticsFileUploader._instance._start_uploader_thread()
                return
        except Exception as e:
            mrb_logger("octoprint.plugins.mrbeam.analytics.uploader").exception(
                "Exception during upload_now in AnalyticsFileUploader: {}".format(e)
            )


class ReviewFileUploader(FileUploader):
    _instance = None

    def __init__(self, plugin, review_lock):
        self._settings = plugin._settings
        self._review_handler = plugin.review_handler

        FileUploader.__init__(
            self,
            plugin,
            directory=self._review_handler.review_folder,
            file=self._review_handler.review_file,
            upload_type="review",
            lock=review_lock,
        )

    @staticmethod
    def upload_now(plugin, review_lock):
        try:
            if (
                ReviewFileUploader._instance is None
                or not ReviewFileUploader._instance.is_active()
            ):
                ReviewFileUploader._instance = ReviewFileUploader(plugin, review_lock)
                ReviewFileUploader._instance._start_uploader_thread()
                return
        except Exception as e:
            mrb_logger("octoprint.plugins.mrbeam.analytics.uploader").exception(
                "Exception during upload_now in ReviewFileUploader: {}".format(e)
            )
