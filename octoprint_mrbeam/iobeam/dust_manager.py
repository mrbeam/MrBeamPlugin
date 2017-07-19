import time
import threading
import numbers
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None

def dustManager():
	global _instance
	if _instance is None:
		_instance = DustManager()
	return _instance

class DustManager(object):

	DEFAULT_DUST_TIMER_INTERVAL = 3
	DEFAUL_DUST_MAX_AGE = 10  # seconds

	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.dustmanager")

		self._dust = None
		self._dust_ts = None

		self._shutting_down = False
		self._trail_extraction = None

		self._subscribe()
		self._start_dust_timer()

		self._logger.debug("initialized!")

	def _subscribe(self):
		_mrbeam_plugin_implementation._event_bus.subscribe(IoBeamEvents.DUST_VALUE, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.DUST_VALUE:
			self._handle_dust(payload)
		elif event == OctoPrintEvents.PRINT_STARTED:
			self._start_dust_extraction()
		elif event in (OctoPrintEvents.PRINT_DONE, OctoPrintEvents.PRINT_FAILED, OctoPrintEvents.PRINT_CANCELLED):
			self._stop_dust_extraction_when_below(0.15)  # TODO change this hardcoded value to something from the machine profile
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def shutdown(self):
		self._shutting_down = True

	def _handle_dust(self, payload):
		tmp = payload['val'] if 'val' in payload else None
		if not isinstance(tmp, numbers.Number):
			self._logger("GOT WRONG TYPE {} instead of number".format(self._dust))
		else:
			self._dust = tmp
		self._dust_ts = time.time()
		self.check_dust_value()
		self.send_status_to_frontend(self._dust)

	def _start_dust_extraction(self, value=None):
		if value is None:
			_mrbeam_plugin_implementation._ioBeam.send_command("fan:auto")
		else:
			if value > 100:
				value = 100
			elif value < 0:
				value = 0
			_mrbeam_plugin_implementation._ioBeam.send_command("fan:on:{:d}".format(int(value)))

	def _stop_dust_extraction(self):
		_mrbeam_plugin_implementation._ioBeam.send_command("fan:off")

	def _stop_dust_extraction_when_below(self, value):
		if self._trail_extraction is None:
			self._trail_extraction = threading.Thread(target=self._wait_until, args=(value,))
			self._trail_extraction.daemon = True
			self._trail_extraction.start()

	def _wait_until(self, value):
		self._logger.debug("starting trial dust extraction.")
		dust_start = self._dust
		dust_start_ts = self._dust_ts
		self._start_dust_extraction(100)
		while self._dust > value:
			time.sleep(self.DEFAULT_DUST_TIMER_INTERVAL)
		dust_end = self._dust
		dust_end_ts = self._dust_ts
		self._stop_dust_extraction()
		self._logger.debug("dust extraction time {} from {} to {} (gradient: {})".format(dust_end_ts - dust_start_ts, dust_start, dust_end, (dust_start-dust_end)/(dust_end_ts-dust_start_ts)))
		self._trail_extraction = None

	def check_dust_value(self):
		pass

	def _check_dust_is_current(self):
		if time.time() - self._dust_ts > self.DEFAUL_DUST_MAX_AGE:
			self._logger.error("Can't read dust value.")

	def request_dust(self):
		_mrbeam_plugin_implementation._ioBeam.send_command("fan:dust")

	def _dust_timer_callback(self):
		self.request_dust()
		self._check_dust_is_current()
		self._start_dust_timer()

	def _start_dust_timer(self):
		if not self._shutting_down:
			self.temp_timer = threading.Timer(self.DEFAULT_DUST_TIMER_INTERVAL, self._dust_timer_callback)
			self.temp_timer.daemon = True
			self.temp_timer.start()
		else:
			self._logger.debug("Shutting down.")

	def send_status_to_frontend(self, dust):
		_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", dict(status=dict(dust_value=dust)))
