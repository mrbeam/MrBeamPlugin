# coding=utf-8

import threading
import time
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents, IoBeamValueEvents
from octoprint_mrbeam.mrb_logger import mrb_logger


# singleton
_instance = None

def compressor_handler(plugin):
	global _instance
	if _instance is None:
		_instance = CompressorHandler(plugin)
	return _instance



class CompressorHandler(object):

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.temperaturemanager")
		self._plugin = plugin
		self._event_bus = plugin._event_bus

		self._iobeam = None
		self._analytics_handler = None

		self._compressor_nominal_state = 0
		self._compressor_present = False

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._iobeam = self._plugin.iobeam
		self._analytics_handler = self._plugin.analytics_handler
		self._subscribe()

	def _subscribe(self):
		# self._iobeam.subscribe(IoBeamValueEvents.LASER_TEMP, self.handle_temp)

		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.set_compressor_off)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.set_compressor_off)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.set_compressor_off)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.set_compressor_off)

		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self.set_compressor_pause)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self.set_compressor_unpause)

	def has_compressor(self):
		#TODO ANDYTEST
		return True

	def set_compressor(self, value, set_nominal_value=True):
		self._logger.info("ANDYTEST setting compressor from %s to %s (set_nominal_value: %s)", self._compressor_nominal_state, value, set_nominal_value)
		if set_nominal_value:
			self._compressor_nominal_state = value
		self._iobeam.send_compressor_command(value)

	def set_compressor_off(self, *args, **kwargs):
		self.set_compressor(0)

	def set_compressor_pause(self, *args, **kwargs):
		self.set_compressor(0, set_nominal_value=False)

	def set_compressor_unpause(self, *args, **kwargs):
		self.set_compressor(self._compressor_nominal_state)






