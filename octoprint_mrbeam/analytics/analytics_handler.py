import json
import time
import os.path
from octoprint.events import Events as OctoPrintEvents
from octoprint.settings import settings
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None
def analyticsHandler(plugin):
	global _instance
	if _instance is None:
		_instance = AnalyticsHandler(plugin._event_bus)
	return _instance


class AnalyticsHandler(object):
	def __init__(self, event_bus):
		self._event_bus = event_bus

		self._logger = mrb_logger("octoprint.plugins.mrbeam.analyticshandler")

		basefolder = settings().getBaseFolder("logs")
		self._jsonfile = os.path.join(basefolder, "analytics_log.json")
		self._initjsonfile()

		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.onEvent)
		self._event_bus.subscribe(MrBeamEvents.PRINT_PROGRESS, self.onEvent)

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
		with open("/proc/cpuinfo") as f:
			for line in f:
				if line.startswith("Serial"):
					return line.split(' ')[-1].rstrip()

	@staticmethod
	def _gethostname():
		import socket
		return socket.gethostname()

	def onEvent(self, event, payload):
		data = None
		typename = 'jobevent'

		if event == OctoPrintEvents.PRINT_STARTED:
			data = {
				'type':typename,
				'v':1,
				'eventname':'print_started',
				'filename':os.path.basename(payload['file']),
				'timestamp':time.time()
			}
		elif event == MrBeamEvents.PRINT_PROGRESS:
			data = {
				'type':typename,
				'v':1,
				'eventname':'print_progress',
				'progress':payload,
				'timestamp':time.time()
			}
		elif event == OctoPrintEvents.PRINT_PAUSED:
			data = {
				'type':typename,
				'v': 1,
				'eventname':'print_paused',
				'timestamp':time.time()
			}
		elif event == OctoPrintEvents.PRINT_RESUMED:
			data = {
				'type':typename,
				'v': 1,
				'eventname':'print_resumed',
				'timestamp':time.time()
			}
		elif event == OctoPrintEvents.PRINT_DONE:
			data = {
				'type':typename,
				'v': 1,
				'eventname':'print_done',
				'timestamp':time.time()
			}
		elif event == OctoPrintEvents.PRINT_CANCELLED:
			data = {
				'type':typename,
				'v': 1,
				'eventname':'print_cancelled',
				'timestamp':time.time()
			}
		elif event == OctoPrintEvents.PRINT_FAILED:
			data = {
				'type':typename,
				'v': 1,
				'eventname':'print_failed',
				'timestamp':time.time()
			}

		if data is not None:
			with open(self._jsonfile, 'a') as f:
				json.dump(data, f)
				f.write('\n')
