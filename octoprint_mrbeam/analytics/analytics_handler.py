import json
import time
import os.path
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None
def analyticsHandler(plugin):
	global _instance
	if _instance is None:
		_instance = AnalyticsHandler(plugin._event_bus, plugin._settings)
	return _instance


class AnalyticsHandler(object):
	def __init__(self, event_bus, settings):
		self._event_bus = event_bus
		self._settings = settings

		self._logger = mrb_logger("octoprint.plugins.mrbeam.analyticshandler")

		analyticsfolder = os.path.join(self._settings.getBaseFolder("base"), self._settings.get(["analyticsfolder"]))
		if not os.path.isdir(analyticsfolder):
			os.makedirs(analyticsfolder)

		self._jsonfile = os.path.join(analyticsfolder, "analytics_log.json")
		self._initjsonfile()

		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._event_print_started)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self._event_print_paused)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self._event_print_resumed)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._event_print_done)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._event_print_failed)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._event_print_cancelled)
		self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self._event_print_progress)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_PAUSE, self._event_laser_cooling_pause)
		self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_RESUME, self._event_laser_cooling_resume)

	def _initjsonfile(self):
		if os.path.isfile(self._jsonfile):
			return
		else:
			with open(self._jsonfile, 'w+') as f:
				data = {
					'type':'deviceinfo',
					'v':1,
					'serialnumber': self._getserialnumber(),
					'hostname': self._gethostname(),
					'timestamp': time.time()
				}
				json.dump(data, f)
				f.write('\n')

	@staticmethod
	def _getserialnumber():
		return _mrbeam_plugin_implementation.getPiSerial()

	@staticmethod
	def _gethostname():
		return _mrbeam_plugin_implementation.getHostname()

	def _event_print_started(self, event, payload):
		self.write_event('jobevent', 'print_started', 1, {'filename': os.path.basename(payload['file'])})

	def _event_print_paused(self, event, payload):
		self.write_event('jobevent', 'print_paused', 1)

	def _event_print_resumed(self, event, payload):
		self.write_event('jobevent', 'print_resumed', 1)

	def _event_print_done(self, event, payload):
		self.write_event('jobevent', 'print_done', 1)

	def _event_print_failed(self, event, payload):
		self.write_event('jobevent', 'print_failed', 1)

	def _event_print_cancelled(self, event, payload):
		self.write_event('jobevent', 'print_cancelled', 1)

	def _event_print_progress(self, event, payload):
		self.write_event('jobevent', 'print_progress', 1, {'progress':payload})

	def _event_laser_cooling_pause(self, event, payload):
		self.write_event('jobevent', 'laser_cooling_pause', 1)

	def _event_laser_cooling_resume(self, event, payload):
		self.write_event('jobevent', 'laser_cooling_resume', 1)

	def write_event(self, typename, eventname, version, payload=None):
		data = {
			'type':typename,
			'v': version,
			'eventname': eventname,
			'timestamp': time.time()
		}
		if payload:
			data.update(payload)
		self._append_data_to_file(data)

	def add_dust_log(self, values):
		data = {
			'type':'dust',
			'v':1,
			'dust_start':values['dust_start'],
			'dust_end': values['dust_end'],
			'dust_start_ts': values['dust_start_ts'],
			'dust_end_ts': values['dust_end_ts']
		}
		self._append_data_to_file(data)

	def _append_data_to_file(self, data):
		with open(self._jsonfile, 'a') as f:
			json.dump(data, f)
			f.write('\n')
