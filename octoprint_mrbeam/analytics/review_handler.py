import os
import json

from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from uploader import ReviewFileUploader
from threading import Lock

try:
    from octoprint_mrbeam.mrb_logger import mrb_logger
except:
    import logging

# singleton
_instance = None


def reviewHandler(plugin):
    global _instance
    if _instance is None:
        _instance = ReviewHandler(plugin)
    return _instance


REVIEW_FILE = "review.json"


class ReviewHandler:
    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.review")
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._settings = plugin._settings
        self._usage_handler = plugin.usage_handler
        self._device_info = plugin._device_info

        self.review_folder = os.path.join(
            self._settings.getBaseFolder("base"),
            self._settings.get(["analytics", "folder"]),
        )
        self.review_file = os.path.join(self.review_folder, REVIEW_FILE)
        self._review_lock = Lock()

        self._current_job_time_estimation = -1

        # sync given value from settings to usage_handler
        self._sync_given_val_to_usage_handler()

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        ReviewFileUploader.upload_now(self._plugin, self._review_lock)

    def is_review_already_given(self):
        return bool(
            self._usage_handler.get_review_given()
            # deprecated
            or self._settings.get(["review", "given"])
        )

    def save_review_data(self, data):
        if not self.is_review_already_given() or data.get("debug", False):
            data = self._add_review_data(data)
            self._write_review_to_file(data)
            if data["dontShowAgain"]:
                if data["rating"] > 0:
                    # write here only if we really go a review
                    # if user clicked don't show again, we ask after a reset or rescue stick
                    self._usage_handler.set_review_given(migrated=False)
                    # deprecated but needed while this version is in beta and users could go back
                    self._settings.set_boolean(["review", "given"], True)
                else:
                    self._settings.set_boolean(["review", "doNotAskAgain"], True)
                self._settings.save()  # This is necessary because without it the value is not saved

            ReviewFileUploader.upload_now(self._plugin, self._review_lock)
        else:
            self._logger.warn("Not accepting user review since it was already given.")

    def _sync_given_val_to_usage_handler(self):
        """_settings.get(["review", "given"]) is deprecated."""
        if not self._usage_handler.get_review_given() and self._settings.get(
            ["review", "given"]
        ):
            self._logger.info("Syncing review state 'given' to _usage_handler...")
            self._usage_handler.set_review_given(migrated=True)

    def _add_review_data(self, data):
        try:
            data["env"] = self._plugin.get_env()
            data["snr"] = self._device_info.get_serial()
            data["sw_version"] = self._plugin._plugin_version
            data["sw_tier"] = self._settings.get(["dev", "software_tier"])
            data["model"] = self._device_info.get_model()
            data["production_date"] = self._device_info.get_production_date()
            data["total_usage"] = self._usage_handler.get_total_usage()
            data["total_jobs"] = self._usage_handler.get_total_jobs()
        except:
            self._logger.exception("Unable to fill system data to user review.")
        return data

    def _write_review_to_file(self, review):
        try:
            with self._review_lock:
                if not os.path.isfile(self.review_file):
                    open(self.review_file, "w+").close()

                with open(self.review_file, "a") as f:
                    data_string = None
                    try:
                        data_string = json.dumps(review, sort_keys=False) + "\n"
                    except:
                        self._logger.info(
                            "Exception during json dump in _write_review_to_file"
                        )

                    if data_string:
                        f.write(data_string)

        except Exception as e:
            self._logger.exception(
                "Exception during _write_review_to_file: {}".format(e)
            )
