import time
import threading
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

	DUST_TIMER_INTERVAL = 3
	DUST_MAX_AGE = 10 # seconds

	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.dustmanager")

		self.dust = None
		self.dust_ts = None

		self._shutting_down = False

		self._subscribe()
		self._start_dust_timer()

	def _subscribe(self):
		_mrbeam_plugin_implementation._event_bus.subscribe(IoBeamEvents.DUST_VALUE, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.DUST_VALUE:
			self.handle_dust(payload)
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def shutdown(self):
		self._shutting_down = True

	def handle_dust(self, payload):
		self._logger.debug("got dust value {}".format(repr(payload)))
		self.dust = payload['val'] if 'val' in payload else None
		self.dust_ts = time.time()
		self.check_dust_value()
		self.send_status_to_frontend(self.dust)

	def check_dust_value(self):
		pass

	def _check_dust_is_current(self):
		if time.time() - self.dust_ts > self.DUST_MAX_AGE:
			self._logger.error("Can't read dust value.")
			#self.cooling_stop()  # TODO ask andy why cooling_stop

	def request_dust(self):
		self._logger.debug("send dust request")
		_mrbeam_plugin_implementation._ioBeam.send_command("fan:dust")

	def _dust_timer_callback(self):
		self.request_dust()
		self._check_dust_is_current()
		self._start_dust_timer()

	def _start_dust_timer(self):
		if not self._shutting_down:
			self._logger.debug("start dust timer")
			self.temp_timer = threading.Timer(self.DUST_TIMER_INTERVAL, self._dust_timer_callback)
			self.temp_timer.daemon = True
			self.temp_timer.start()
		else:
			self._logger.debug("Shutting down.")

	def send_status_to_frontend(self, dust):
		self._logger.debug("send data to frontend")
		_mrbeam_plugin_implementation._plugin_manager.send_plugin_message("mrbeam", dict(status=dict(dust_value=dust)))
