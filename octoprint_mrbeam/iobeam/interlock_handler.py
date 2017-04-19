import logging

from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents



# This guy handles InterLock Events
# Honestly, I'm not sure if we need a separate handler for this...
class InterLockHandler(object):

	def __init__(self, iobeam_handler, event_bus, plugin_manager):
		self._iobeam_handler = iobeam_handler
		self._event_bus = event_bus
		self._plugin_manager = plugin_manager
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.interlockhandler")

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
		self._plugin_manager.send_plugin_message("mrbeam",
						 dict(interlocks_closed=self._iobeam_handler.is_interlock_closed(),
							  interlocks_open=self._iobeam_handler.open_interlocks()))
