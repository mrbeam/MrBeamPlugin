

import logging
from octoprint.events import Events, CommandTrigger


class MrBeamEvents(object):
	PRINT_PROGRESS = "PrintProgress"
	SLICING_PROGRESS = "SlicingProgress"


class LedEventListener(CommandTrigger):

	LED_EVENTS = {}
	LED_EVENTS[Events.STARTUP] = "mrbeam_ledstrips_cli Startup"
	# connect/disconnect to printer
	LED_EVENTS[Events.CONNECTED] = "mrbeam_ledstrips_cli Connected"
	LED_EVENTS[Events.DISCONNECTED] = "mrbeam_ledstrips_cli Disconnected"
	# connect/disconnect by client
	LED_EVENTS[Events.CLIENT_OPENED] = "mrbeam_ledstrips_cli ClientOpened"
	LED_EVENTS[Events.CLIENT_CLOSED] = "mrbeam_ledstrips_cli ClientClosed"
	# print job
	LED_EVENTS[Events.PRINT_STARTED] = "mrbeam_ledstrips_cli PrintStarted"
	LED_EVENTS[Events.PRINT_DONE] = "mrbeam_ledstrips_cli PrintDone"
	LED_EVENTS[Events.PRINT_CANCELLED] = "mrbeam_ledstrips_cli PrintCancelled"
	LED_EVENTS[Events.PRINT_PAUSED] = "mrbeam_ledstrips_cli PrintPaused"
	LED_EVENTS[Events.PRINT_RESUMED] = "mrbeam_ledstrips_cli PrintResumed"
	LED_EVENTS[Events.ERROR] = "mrbeam_ledstrips_cli Error"
	# File management
	LED_EVENTS[Events.UPLOAD] = "mrbeam_ledstrips_cli Upload"
	# Slicing
	LED_EVENTS[Events.SLICING_STARTED] = "mrbeam_ledstrips_cli SlicingStarted"
	LED_EVENTS[Events.SLICING_DONE] = "mrbeam_ledstrips_cli SlicingDone"
	LED_EVENTS[Events.SLICING_CANCELLED] = "mrbeam_ledstrips_cli SlicingCancelled"
	LED_EVENTS[Events.SLICING_FAILED] = "mrbeam_ledstrips_cli SlicingFailed"
	# Settings
	LED_EVENTS[Events.SETTINGS_UPDATED] = "mrbeam_ledstrips_cli SettingsUpdated"
	# MrBeam Events
	LED_EVENTS[MrBeamEvents.SLICING_PROGRESS] = "mrbeam_ledstrips_cli SlicingProgress:{__data}"
	LED_EVENTS[MrBeamEvents.PRINT_PROGRESS] = "mrbeam_ledstrips_cli progress:{__data}"


	def __init__(self, printer, eventBusOct):
		CommandTrigger.__init__(self, printer)
		self._eventBusOct = eventBusOct
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.led_events")

		self._subscriptions = {}

		self._initSubscriptions()


	def _initSubscriptions(self):
		for event in self.LED_EVENTS:
			if not event in self._subscriptions.keys():
				self._subscriptions[event] = []
			self._subscriptions[event].append((self.LED_EVENTS[event], "system", True))

		self.subscribe(self.LED_EVENTS.keys())


	# def eventCallback(self, event, payload):
	# 	self._logger.info("ANDYTEST eventCallback() event: %s, payload: %s", event, payload)
	# 	CommandTrigger.eventCallback(self, event, payload)


