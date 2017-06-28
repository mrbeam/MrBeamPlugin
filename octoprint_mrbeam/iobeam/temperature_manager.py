
import threading
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from . import _mrbeam_plugin_implementation


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

	def __init__(self):
		self._plugin = _mrbeam_plugin_implementation
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.temperaturemanager")

		self.temp_timer = None
		self._subscribe()
		self._start_temp_timer()


	def _subscribe(self):
		self._plugin._event_bus.subscribe(IoBeamEvents.LASER_TEMP, self.onEvent)


	def onEvent(self, event, payload):
		if event == IoBeamEvents.LASER_TEMP:
			self.handle_temp(payload)

	def handle_temp(self, temp):
		self._logger.debug("handle_temp() ANDYTEST Current laser temperature: %s", temp)

	def request_temp(self):
		self._plugin._ioBeam.send_command("laser:temp")

	def _temp_timer_callback(self):
		self.request_temp()
		self._start_temp_timer()

	def _start_temp_timer(self):
		self.temp_timer = threading.Timer(self.TEMP_TIMER_INTERVAL,
		                                            self._temp_timer_callback)
		self.temp_timer.start()
