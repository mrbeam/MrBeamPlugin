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

	COMPRESSOR_MIN = 0
	COMPRESSOR_MAX = 100

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.compressorhandler")
		self._plugin = plugin
		self._event_bus = plugin._event_bus

		self._iobeam = None
		self._analytics_handler = None

		self._compressor_current_state = -1
		self._compressor_nominal_state = 0
		self._compressor_present = False

		self._last_dynamic_data = {}

		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._iobeam = self._plugin.iobeam
		self._analytics_handler = self._plugin.analytics_handler
		self._subscribe()

	def _subscribe(self):
		self._iobeam.subscribe(IoBeamValueEvents.COMPRESSOR_STATIC, self._handle_static_data)
		self._iobeam.subscribe(IoBeamValueEvents.COMPRESSOR_DYNAMIC, self._handle_dynamic_data)
		self._iobeam.subscribe(IoBeamValueEvents.COMPRESSOR_ERROR, self._handle_error_data)

		self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.set_compressor_off)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.set_compressor_off)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.set_compressor_off)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.set_compressor_off)

		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self.set_compressor_pause)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self.set_compressor_unpause)

	def has_compressor(self):
		# return self._plugin.is_mrbeam2_dreamcut()
		return True

	def get_current_state(self):
		if self.has_compressor():
			return self._compressor_current_state
		else:
			return None

	def set_compressor(self, value, set_nominal_value=True):
		if self.has_compressor():
			self._logger.info("Compressor set to %s (nominal state before: %s, real state: %s)",
			                  value, self._compressor_nominal_state, self._compressor_current_state)
			if value > self.COMPRESSOR_MAX:
				value = self.COMPRESSOR_MAX
			if value < self.COMPRESSOR_MIN:
				value = self.COMPRESSOR_MIN
			if set_nominal_value:
				self._compressor_nominal_state = value
			self._iobeam.send_compressor_command(value)

	def set_compressor_off(self, *args, **kwargs):
		self.set_compressor(0)

	def set_compressor_pause(self, *args, **kwargs):
		self.set_compressor(0, set_nominal_value=False)

	def set_compressor_unpause(self, *args, **kwargs):
		self.set_compressor(self._compressor_nominal_state)

	def _handle_error_data(self, payload):
		dataset = payload.get('message', {})
		self._compressor_present = False
		self._add_static_and_error_data_analytics(dataset)

	def _handle_static_data(self, payload):
		dataset = payload.get('message', {})
		if dataset:
			self._add_static_and_error_data_analytics(dataset)

		if 'version' in dataset:
			self._compressor_present = True
			self._logger.info("Enabling compressor. compressor_static: %s", dataset)
		else:
			self._logger.warn("Received compressor_static dataset without version information: compressor_static: %s", dataset)

	def _handle_dynamic_data(self, payload):
		dataset = payload.get('message', {})
		if len(dataset) > 1:
			self._last_dynamic_data = dataset
			if 'state' in dataset:
				try:
					self._compressor_current_state = int(dataset['state'])
				except:
					self._logger.error("Cant convert compressor state to int from compressor_dynamic: %s", dataset)

	def _add_static_and_error_data_analytics(self, data):
		data = dict(
			check=data.get('compressor_check', None),
			error_msg=data.get('error', {}).get('msg', None),
			error_id=data.get('error', {}).get('id', None),
		)

		self._analytics_handler.add_compressor_data(data)

	def get_compressor_data(self):
		data = dict(
			voltage=self._last_dynamic_data.get('voltage', None),
			current=self._last_dynamic_data.get('current', None),
			rpm=self._last_dynamic_data.get('rpm_actual', None),
			pressure=self._last_dynamic_data.get('press_actual', None),
			state=self._compressor_nominal_state,
			mode_name=self._last_dynamic_data.get('mode_name', None),
		)

		return data




