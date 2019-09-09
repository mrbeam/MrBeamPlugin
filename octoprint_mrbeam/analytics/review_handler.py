import os

from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint.events import Events as OctoPrintEvents

# singleton
_instance = None


class ReviewHandler:
	def __init__(self, plugin):
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings

		self.review_folder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(['analytics', 'folder']))
		self.review_file = os.path.join(self.review_folder, self._settings.get(['review', 'filename']))

		self._num_successful_jobs = self._settings.get(['review', 'num_succ_jobs'])
		self._review_given = self._settings.get(['review', 'given'])

		self._current_job_time_estimation = -1

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_print_done)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._event_print_started)
		self._event_bus.subscribe(MrBeamEvents.JOB_TIME_ESTIMATED, self._event_job_time_estimated)

	def _event_print_started(self):
		if self.ask_for_review():
			# todo iratxe ask for review + save + skip...
			pass

		# Reset the job time estimation just in case
		self._current_job_time_estimation = -1

	def _event_print_done(self):
		self._num_successful_jobs += 1

	def _event_job_time_estimated(self, event, payload):
		self._current_job_time_estimation = payload['job_time_estimation']

	def ask_for_review(self):
		return self._num_successful_jobs >= 5 and not self._review_given and self._current_job_time_estimation >= 60
