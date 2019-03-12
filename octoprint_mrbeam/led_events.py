

import threading
from distutils.version import StrictVersion
from octoprint.events import Events, CommandTrigger, GenericEventListener
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger


class LedEventListener(CommandTrigger):

	WIFI_CHECK_INTERVAL = 1.0
	VERSION_MIN_FINDMRBEAM = StrictVersion("0.2.0")


	LED_EVENTS = {}
	LED_EVENTS[Events.STARTUP] = "mrbeam_ledstrips_cli listening"
	# connect/disconnect by client
	LED_EVENTS[Events.CLIENT_OPENED] = "mrbeam_ledstrips_cli ClientOpened"
	LED_EVENTS[Events.CLIENT_CLOSED] = "mrbeam_ledstrips_cli ClientClosed"
	# ready to laser
	LED_EVENTS[MrBeamEvents.READY_TO_LASER_START] = "mrbeam_ledstrips_cli ReadyToPrint"
	LED_EVENTS[MrBeamEvents.READY_TO_LASER_CANCELED] = "mrbeam_ledstrips_cli ReadyToPrintCancel"
	# print job
	LED_EVENTS[Events.PRINT_STARTED] = "mrbeam_ledstrips_cli PrintStarted"
	LED_EVENTS[Events.PRINT_DONE] = "mrbeam_ledstrips_cli PrintDone"
	LED_EVENTS[Events.PRINT_CANCELLED] = "mrbeam_ledstrips_cli PrintCancelled"
	LED_EVENTS[Events.PRINT_RESUMED] = "mrbeam_ledstrips_cli PrintResumed"
	LED_EVENTS[Events.ERROR] = "mrbeam_ledstrips_cli Error"
	LED_EVENTS[MrBeamEvents.LASER_JOB_DONE] = "mrbeam_ledstrips_cli LaserJobDone"
	LED_EVENTS[MrBeamEvents.LASER_JOB_CANCELLED] = "mrbeam_ledstrips_cli LaserJobCancelled"
	LED_EVENTS[MrBeamEvents.LASER_JOB_FAILED] = "mrbeam_ledstrips_cli LaserJobFailed"
	# LaserPauseSafetyTimeout Events
	LED_EVENTS[MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_START] = "mrbeam_ledstrips_cli PrintPausedTimeout"
	LED_EVENTS[MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_END] = "mrbeam_ledstrips_cli PrintPaused"
	LED_EVENTS[MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_BLOCK] = "mrbeam_ledstrips_cli PrintPausedTimeoutBlock"

	LED_EVENTS[MrBeamEvents.BUTTON_PRESS_REJECT] = "mrbeam_ledstrips_cli ButtonPressReject"


	# File management
	# LED_EVENTS[Events.UPLOAD] = "mrbeam_ledstrips_cli Upload"
	# Slicing
	LED_EVENTS[Events.SLICING_STARTED] = "mrbeam_ledstrips_cli SlicingStarted"
	LED_EVENTS[Events.SLICING_DONE] = "mrbeam_ledstrips_cli SlicingDone"
	LED_EVENTS[Events.SLICING_CANCELLED] = "mrbeam_ledstrips_cli SlicingCancelled"
	LED_EVENTS[Events.SLICING_FAILED] = "mrbeam_ledstrips_cli SlicingFailed"
	# Settings
	# LED_EVENTS[Events.SETTINGS_UPDATED] = "mrbeam_ledstrips_cli SettingsUpdated"
	# MrBeam Events
	LED_EVENTS[MrBeamEvents.SLICING_PROGRESS] = "mrbeam_ledstrips_cli SlicingProgress:{__progress}"
	LED_EVENTS[MrBeamEvents.PRINT_PROGRESS] = "mrbeam_ledstrips_cli progress:{__progress}"
	#Shutdown
	LED_EVENTS[MrBeamEvents.SHUTDOWN_PREPARE_START] = "mrbeam_ledstrips_cli ShutdownPrepare"
	LED_EVENTS[MrBeamEvents.SHUTDOWN_PREPARE_CANCEL] = "mrbeam_ledstrips_cli ShutdownPrepareCancel"
	LED_EVENTS[MrBeamEvents.SHUTDOWN_PREPARE_SUCCESS] = "mrbeam_ledstrips_cli Shutdown"
	LED_EVENTS[Events.SHUTDOWN] = "mrbeam_ledstrips_cli Shutdown"


	# LISTENING COMMANDS for breathing in different colors
	COMMAND_LISTENING_FINDMRBEAM =   "mrbeam_ledstrips_cli listening_findmrbeam"
	COMMAND_LISTENING_AP_AND_NET =   "mrbeam_ledstrips_cli listening_ap_and_net"
	COMMAND_LISTENING_NET =          "mrbeam_ledstrips_cli listening_net"
	COMMAND_LISTENING_AP =           "mrbeam_ledstrips_cli listening_ap"


	def __init__(self, event_bus, printer):
		CommandTrigger.__init__(self, printer)
		self._event_bus = event_bus
		self._logger = mrb_logger("octoprint.plugins.mrbeam.led_events")

		self._watch_thread = None
		self._watch_active = False
		self._listening_state = None

		self._subscriptions = {}

		self._initSubscriptions()


	def _initSubscriptions(self):
		for event in self.LED_EVENTS:
			if not event in self._subscriptions.keys():
				self._subscriptions[event] = []
			self._subscriptions[event].append((self.LED_EVENTS[event], "system", False))

		self.subscribe(self.LED_EVENTS.keys())


	def eventCallback(self, event, payload):
		# really, just copied this one from OctoPrint to add my debug log line.
		GenericEventListener.eventCallback(self, event, payload)

		if not event in self._subscriptions:
			return

		for command, commandType, debug in self._subscriptions[event]:
			command = self._handleStartupCommand(command)
			self._execute_command(command, commandType, debug, event, payload)


	def _execute_command(self, command, commandType, debug, event=None, payload=None):
		try:
			if isinstance(command, (tuple, list, set)):
				processedCommand = []
				for c in command:
					processedCommand.append(self._processCommand(c, payload))
			else:
				processedCommand = self._processCommand(command, payload)

			self._logger.debug("LED_EVENT %s: '%s'", event, processedCommand)
			self.executeCommand(processedCommand, commandType, debug=debug)
		except KeyError as e:
			self._logger.warn(
				"There was an error processing one or more placeholders in the following command: %s" % command)

	def _handleStartupCommand(self, command):
		if command in (self.LED_EVENTS[Events.STARTUP], self.LED_EVENTS[Events.CLIENT_CLOSED]):
			self._listening_state = self.get_listening_state()
			command = self._get_listening_command()
			self._start_wifi_watcher()
		else:
			self._stop_wifi_watcher()
		return command

	def get_listening_state(self):
		res = dict(wifi=None,
		           ap=None,
		           wired=None,
		           findmrbeam=None)
		try:
			pluginInfo = _mrbeam_plugin_implementation._plugin_manager.get_plugin_info("findmymrbeam")
			if pluginInfo is not None and StrictVersion(pluginInfo.version) >= self.VERSION_MIN_FINDMRBEAM:
				res['findmrbeam'] = pluginInfo.implementation.is_registered()
			else:
				# we know we can't read find state, so we must assume false
				res['findmrbeam'] = False
		except Exception as e:
			self._logger.exception("Exception while reading is_registered state from findmymrbeam:")

		try:
			pluginInfo = _mrbeam_plugin_implementation._plugin_manager.get_plugin_info("netconnectd")
			if pluginInfo is not None:
				status = pluginInfo.implementation._get_status()
				if 'wifi' in status["connections"]:
					res['wifi'] = status["connections"]['wifi']
				if 'ap' in status["connections"]:
					res['ap'] = status["connections"]['ap']
				if 'wired' in status["connections"]:
					res['wired'] = status["connections"]['wired']
		except Exception as e:
			self._logger.exception("Exception while reading wifi/ap state from netconnectd:")

		return res

	def log_listening_state(self, command=None):
		self._logger.info("LED Connectivity command: %s , state: %s, is_boot_grace_period: %s", command, self._listening_state, _mrbeam_plugin_implementation.is_boot_grace_period())

	def _get_listening_command(self):
		command = self.LED_EVENTS[Events.STARTUP]
		if self._listening_state is not None and \
			(self._listening_state['findmrbeam'] is not None
			 or not _mrbeam_plugin_implementation.is_boot_grace_period()):
				if self._listening_state['findmrbeam']:
					command = self.COMMAND_LISTENING_FINDMRBEAM
				elif self._listening_state['ap'] and (self._listening_state['wifi'] or self._listening_state['wired']):
					command = self.COMMAND_LISTENING_AP_AND_NET
				elif self._listening_state['ap'] and not (self._listening_state['wifi'] or self._listening_state['wired']):
					command = self.COMMAND_LISTENING_AP
				elif self._listening_state['wifi'] or self._listening_state['wired']:
					command = self.COMMAND_LISTENING_NET
		self.log_listening_state(command=command)
		return command

	def _start_wifi_watcher(self, force=False):
		if force or not self._watch_thread or not self._watch_thread.is_alive:
			self._watch_thread = threading.Timer(self.WIFI_CHECK_INTERVAL, self.__run_wifi_watcher)
			self._watch_thread.daemon = True
			self._watch_thread.name = "led_events.__run_wifi_watcher"
			self._watch_thread.start()

	def _stop_wifi_watcher(self):
		if self._watch_thread:
			self._watch_thread.cancel()
			self._watch_thread = None

	def __run_wifi_watcher(self):
		current_listening_state = self.get_listening_state()
		if current_listening_state != self._listening_state:
			self._listening_state = current_listening_state
			command = self._get_listening_command()
			self._execute_command(command, "system", False)
		self._start_wifi_watcher(force=True)

