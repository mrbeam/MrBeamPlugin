import os
import json

from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint.events import Events as OctoPrintEvents
from uploader import ReviewFileUploader

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


class ReviewHandler:
	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.review")
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings

		self.review_folder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['analytics', 'folder']))
		self.review_file = os.path.join(self.review_folder, self._settings.get(['review', 'filename']))

		self._current_job_time_estimation = -1

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._subscribe()

		ReviewFileUploader.upload_now(self._plugin)

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_print_done)

	def _event_print_done(self, event, payload):
		num_successful_jobs_user = self._plugin.getUserSetting(self._plugin.get_user_name(), ['review', 'num_succ_jobs'], -1) + 1
		self._plugin.setUserSetting(self._plugin.get_user_name(), ['review', 'num_succ_jobs'], num_successful_jobs_user)

		num_successful_jobs_mrbeam = self._settings.get(['num_succ_jobs']) + 1
		self._settings.set_int(['num_succ_jobs'], num_successful_jobs_mrbeam)
		self._settings.save()  # This is necessary because without it the value is not saved

	def should_ask_for_review(self):
		num_successful_jobs_user = self._plugin.getUserSetting(self._plugin.get_user_name(), ['review', 'num_succ_jobs'], -1)
		review_given = self._plugin.getUserSetting(self._plugin.get_user_name(), ['review', 'given'], False)

		return num_successful_jobs_user >= 5 and not review_given

	def save_review_data(self, data):
		self._write_review_to_file(data)

		self._plugin.setUserSetting(self._plugin.get_user_name(), ['review', 'given'], data['dontShowAgain'])

		ReviewFileUploader.upload_now(self._plugin)

	def _write_review_to_file(self, review):
		try:
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
