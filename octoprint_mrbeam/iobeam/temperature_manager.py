
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

	def __init__(self, iobeam_handler, event_bus, plugin_manager, printer):
		self._plugin = _mrbeam_plugin_implementation
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.temperaturemanager")

		self._subscribe()


	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.LASER_TEMP, self.onEvent)


	def onEvent(self, event, payload):
		if event == IoBeamEvents.LASER_TEMP:
			self.handle_temp(payload)

	def handle_temp(self, temp):
		self._logger.debug("handle_temp() ANDYTEST Current laser temperature: %s", temp)
