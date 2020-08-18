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


REVIEW_FILE = 'review.json'


class ReviewHandler:
	def __init__(self, plugin):
		self._logger = mrb_logger(__name__)
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings

		self.review_folder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['analytics', 'folder']))
		self.review_file = os.path.join(self.review_folder, REVIEW_FILE)
		self._review_lock = Lock()

		self._current_job_time_estimation = -1

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		ReviewFileUploader.upload_now(self._plugin, self._review_lock)

	def save_review_data(self, data):
		self._write_review_to_file(data)
		self._settings.set_boolean(['review', 'given'], data['dontShowAgain'])
		self._settings.save()  # This is necessary because without it the value is not saved

		ReviewFileUploader.upload_now(self._plugin, self._review_lock)

	def _write_review_to_file(self, review):
		try:
			with self._review_lock:
				if not os.path.isfile(self.review_file):
					open(self.review_file, 'w+').close()

				with open(self.review_file, 'a') as f:
					data_string = None
					try:
						data_string = json.dumps(review, sort_keys=False) + '\n'
					except:
						self._logger.info('Exception during json dump in _write_review_to_file')

					if data_string:
						f.write(data_string)

		except Exception as e:
			self._logger.exception('Exception during _write_review_to_file: {}'.format(e))
