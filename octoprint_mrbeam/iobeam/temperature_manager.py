
import threading
import time
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger


# singleton
_instance = None

def temperatureManager():
	global _instance
	if _instance is None:
		_instance = TemperatureManager()
	return _instance

# This guy manages the temperature of the laser head
class TemperatureManager(object):

	TEMP_TIMER_INTERVAL = 3
	TEMP_MAX_AGE = 10 # seconds

	def __init__(self):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.temperaturemanager")

		self.temperatur = None
		self.temperatur_ts = time.time()
		self.temperatur_max = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()['laser']['max_temperature']
		self.temp_timer = None

		self._shutting_down = False

		self._subscribe()
		self._start_temp_timer()

	def _subscribe(self):
		_mrbeam_plugin_implementation._event_bus.subscribe(IoBeamEvents.LASER_TEMP, self.onEvent)
		_mrbeam_plugin_implementation._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._onShutdown)

	def _onShutdown(self0):
		self._shutting_down = True

	def onEvent(self, event, payload):
		if event == IoBeamEvents.LASER_TEMP:
			self.handle_temp(payload)

	def handle_temp(self, temp):
		self._logger.debug("Current laser temperature: %s", temp)
		self.temperatur = temp
		self.temperatur_ts = time.time()
		self._check_temp_val()

	def request_temp(self):
		_mrbeam_plugin_implementation._ioBeam.send_command("laser:temp")

	def emergency_stop(self):
		_mrbeam_plugin_implementation._printer.pause_print()

	def _temp_timer_callback(self):
		self.request_temp()
		self._check_temp_is_current()
		self._start_temp_timer()

	def _start_temp_timer(self):
		if not self._shutting_down:
			self.temp_timer = threading.Timer(self.TEMP_TIMER_INTERVAL, self._temp_timer_callback)
			self.temp_timer.start()
		else:
			self._logger.info("Shutting down.")

	def _check_temp_is_current(self):
		if time.time() - self.temperatur_ts > self.TEMP_MAX_AGE:
			self._logger.error("Can't read laser temperature.")
			self.emergency_stop()

	def _check_temp_val(self):
		if self.temperatur is None or self.temperatur > self.temperatur_max:
			self._logger.warn("Laser temperatur exceeded limit. Current temp: %s, max: %s", self.temperatur, self.temperatur_max)
			self.emergency_stop()

