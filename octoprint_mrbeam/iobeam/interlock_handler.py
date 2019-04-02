
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger


# singleton
_instance = None


def interLockHandler(plugin):
	global _instance
	if _instance is None:
		_instance = InterLockHandler(plugin,
									 plugin._event_bus,
									 plugin._plugin_manager)
	return _instance


# This guy handles InterLock Events
# Honestly, I'm not sure if we need a separate handler for this...
class InterLockHandler(object):

	def __init__(self, plugin, event_bus, plugin_manager):
		self._plugin = plugin
		self._event_bus = event_bus
		self._plugin_manager = plugin_manager
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.interlockhandler")

		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_OPEN, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_CLOSED, self.onEvent)
		self._event_bus.subscribe(MrBeamEvents.READY_TO_LASER_START, self.onEvent)
		# self._event_bus.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.INTERLOCK_OPEN \
				or event == IoBeamEvents.INTERLOCK_CLOSED \
				or event == MrBeamEvents.READY_TO_LASER_START:
			self.send_state()

	def send_state(self):
		if self._plugin._ioBeam:
			self._plugin_manager.send_plugin_message("mrbeam",
							 dict(interlocks_closed=self._plugin._ioBeam.is_interlock_closed(),
								  interlocks_open=self._plugin._ioBeam.open_interlocks()))
		else:
			raise Exception("iobeam handler not available from Plugin. Can't notify frontend about interlock state change.")
