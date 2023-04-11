import threading
from distutils.version import LooseVersion
from octoprint.events import Events, CommandTrigger, GenericEventListener
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger


class LedEventListener(CommandTrigger):

    WIFI_CHECK_INTERVAL = 1.0
    VERSION_MIN_FINDMRBEAM = LooseVersion("0.2.0")

    LED_EVENTS = {}
    LED_EVENTS[Events.STARTUP] = "mrbeam_ledstrips_cli listening"
    # connect/disconnect by client
    LED_EVENTS[Events.CLIENT_OPENED] = "mrbeam_ledstrips_cli ClientOpened"
    LED_EVENTS[Events.CLIENT_CLOSED] = "mrbeam_ledstrips_cli ClientClosed"
    # ready to laser
    LED_EVENTS[MrBeamEvents.READY_TO_LASER_START] = "mrbeam_ledstrips_cli ReadyToPrint"
    LED_EVENTS[
        MrBeamEvents.READY_TO_LASER_CANCELED
    ] = "mrbeam_ledstrips_cli ReadyToPrintCancel"
    # print job
    LED_EVENTS[Events.PRINT_STARTED] = "mrbeam_ledstrips_cli PrintStarted"
    LED_EVENTS[Events.PRINT_DONE] = "mrbeam_ledstrips_cli PrintDone"
    LED_EVENTS[Events.PRINT_CANCELLED] = "mrbeam_ledstrips_cli PrintCancelled"
    LED_EVENTS[Events.PRINT_RESUMED] = "mrbeam_ledstrips_cli PrintResumed"
    LED_EVENTS[Events.ERROR] = "mrbeam_ledstrips_cli Error"
    LED_EVENTS[MrBeamEvents.LASER_JOB_DONE] = "mrbeam_ledstrips_cli LaserJobDone"
    LED_EVENTS[
        MrBeamEvents.LASER_JOB_CANCELLED
    ] = "mrbeam_ledstrips_cli LaserJobCancelled"
    LED_EVENTS[MrBeamEvents.LASER_JOB_FAILED] = "mrbeam_ledstrips_cli LaserJobFailed"
    # LaserPauseSafetyTimeout Events
    LED_EVENTS[
        MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_START
    ] = "mrbeam_ledstrips_cli PrintPausedTimeout"
    LED_EVENTS[
        MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_END
    ] = "mrbeam_ledstrips_cli PrintPaused"
    LED_EVENTS[
        MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_BLOCK
    ] = "mrbeam_ledstrips_cli PrintPausedTimeoutBlock"

    LED_EVENTS[
        MrBeamEvents.BUTTON_PRESS_REJECT
    ] = "mrbeam_ledstrips_cli ButtonPressReject"

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
    LED_EVENTS[
        MrBeamEvents.SLICING_PROGRESS
    ] = "mrbeam_ledstrips_cli SlicingProgress:{__progress}"
    LED_EVENTS[
        MrBeamEvents.PRINT_PROGRESS
    ] = "mrbeam_ledstrips_cli progress:{__progress}"

    # Fire warning
    LED_EVENTS[MrBeamEvents.LED_ERROR_ENTER] = "mrbeam_ledstrips_cli Error"
    LED_EVENTS[MrBeamEvents.LED_ERROR_EXIT] = "mrbeam_ledstrips_cli ClientOpened"

    # Camera Calibration Screen Events
    LED_EVENTS[
        MrBeamEvents.RAW_IMAGE_TAKING_START
    ] = "mrbeam_ledstrips_cli flash_blue:1"
    LED_EVENTS[
        MrBeamEvents.RAW_IMAGE_TAKING_DONE
    ] = "mrbeam_ledstrips_cli blue"  # flash_color:200:200:30:1:50" #color:200:200:30" # TODO undo -> last state
    LED_EVENTS[
        MrBeamEvents.RAW_IMG_TAKING_LAST
    ] = "mrbeam_ledstrips_cli flash_green:1:30"
    LED_EVENTS[MrBeamEvents.RAW_IMG_TAKING_FAIL] = "mrbeam_ledstrips_cli flash_red:1:30"
    LED_EVENTS[
        MrBeamEvents.LENS_CALIB_START
    ] = "mrbeam_ledstrips_cli lens_calibration"  # dims interieur for better pictures
    LED_EVENTS[
        MrBeamEvents.LENS_CALIB_PROCESSING_BOARDS
    ] = "mrbeam_ledstrips_cli flash_blue:3"
    LED_EVENTS[MrBeamEvents.LENS_CALIB_RUNNING] = "mrbeam_ledstrips_cli flash_green:2"
    LED_EVENTS[MrBeamEvents.LENS_CALIB_IDLE] = "mrbeam_ledstrips_cli blue"
    LED_EVENTS[MrBeamEvents.LENS_CALIB_DONE] = "mrbeam_ledstrips_cli green"
    LED_EVENTS[MrBeamEvents.LENS_CALIB_FAIL] = "mrbeam_ledstrips_cli orange"
    LED_EVENTS[MrBeamEvents.LENS_CALIB_EXIT] = "mrbeam_ledstrips_cli ClientOpened"
    LED_EVENTS[
        MrBeamEvents.BLINK_PRINT_LABELS
    ] = "mrbeam_ledstrips_cli upload:0:255:0"  # switch to 'blink_green' in future

    # Shutdown
    LED_EVENTS[
        MrBeamEvents.SHUTDOWN_PREPARE_START
    ] = "mrbeam_ledstrips_cli ShutdownPrepare"
    LED_EVENTS[
        MrBeamEvents.SHUTDOWN_PREPARE_CANCEL
    ] = "mrbeam_ledstrips_cli ShutdownPrepareCancel"
    LED_EVENTS[MrBeamEvents.SHUTDOWN_PREPARE_SUCCESS] = "mrbeam_ledstrips_cli Shutdown"
    LED_EVENTS[Events.SHUTDOWN] = "mrbeam_ledstrips_cli Shutdown"

    # LISTENING COMMANDS for breathing in different colors
    COMMAND_LISTENING_FINDMRBEAM = "mrbeam_ledstrips_cli listening_findmrbeam"
    COMMAND_LISTENING_AP_AND_NET = "mrbeam_ledstrips_cli listening_ap_and_net"
    COMMAND_LISTENING_NET = "mrbeam_ledstrips_cli listening_net"
    COMMAND_LISTENING_AP = "mrbeam_ledstrips_cli listening_ap"

    # LEDSTRIPS SETTINGS for adjusting brightness and maybe more some time
    COMMAND_SET_EDGEBRIGHTNESS = (
        "mrbeam_ledstrips_cli set:edge_brightness:{__brightness}"
    )
    COMMAND_SET_INSIDEBRIGHTNESS = (
        "mrbeam_ledstrips_cli set:inside_brightness:{__brightness}"
    )
    COMMAND_SET_FPS = "mrbeam_ledstrips_cli set:fps:{__fps}"

    def __init__(self, plugin):
        CommandTrigger.__init__(self, plugin._printer)
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._logger = mrb_logger("octoprint.plugins.mrbeam.led_events")

        self._watch_thread = None
        self._watch_active = False
        self._listening_state = None
        self._analytics_handler = None
        self.block_on_error = False
        self._subscriptions = {}

        self._connections_states = []

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def set_brightness(self, brightness):
        if isinstance(brightness, int) and brightness > 0 and brightness <= 255:
            command = self.COMMAND_SET_EDGEBRIGHTNESS.replace(
                "{__brightness}", str(brightness)
            )
            commandType = "system"
            debug = False
            self._execute_command(command, commandType, debug)

    def set_inside_brightness(self, brightness):
        if isinstance(brightness, int) and brightness > 0 and brightness <= 255:
            command = self.COMMAND_SET_INSIDEBRIGHTNESS.replace(
                "{__brightness}", str(brightness)
            )
            commandType = "system"
            debug = False
            self._execute_command(command, commandType, debug)

    def set_fps(self, fps):
        if isinstance(fps, int) and fps >= 15 and fps <= 45:
            command = self.COMMAND_SET_FPS.replace("{__fps}", str(fps))
            commandType = "system"
            debug = False
            self._execute_command(command, commandType, debug)

    def _on_mrbeam_plugin_initialized(self, event, payload):
        from octoprint_mrbeam import IS_X86

        if IS_X86:
            return
        self._analytics_handler = self._plugin.analytics_handler

        self._initSubscriptions()
        # We need to re-play the Startup Event for the LED system....
        self.eventCallback(Events.STARTUP)

    def _initSubscriptions(self):
        for event in self.LED_EVENTS:
            if not event in self._subscriptions.keys():
                self._subscriptions[event] = []
            self._subscriptions[event].append((self.LED_EVENTS[event], "system", False))

        self.subscribe(self.LED_EVENTS.keys())

    def eventCallback(self, event, payload=None):
        # really, just copied this one from OctoPrint to add my debug log line.
        GenericEventListener.eventCallback(self, event, payload)

        if not event in self._subscriptions:
            return
        if event == MrBeamEvents.LED_ERROR_ENTER:
            self.block_on_error = True
        elif event == MrBeamEvents.LED_ERROR_EXIT:
            self.block_on_error = False

        if self.block_on_error and event not in [
            MrBeamEvents.LED_ERROR_EXIT,
            MrBeamEvents.SHUTDOWN_PREPARE_START,
            MrBeamEvents.SHUTDOWN_PREPARE_CANCEL,
            MrBeamEvents.SHUTDOWN_PREPARE_SUCCESS,
            Events.SHUTDOWN,
        ]:
            self._logger.debug(
                "LED_EVENT %s: Ignoring Event because as we are currently blocking on a error",
                event,
            )
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
                "There was an error processing one or more placeholders in the following command: %s"
                % command
            )

    def _handleStartupCommand(self, command):
        if command in (
            self.LED_EVENTS[Events.STARTUP],
            self.LED_EVENTS[Events.CLIENT_CLOSED],
        ):
            self._listening_state = self.get_listening_state()
            command = self._get_listening_command()
            self._start_wifi_watcher()
        else:
            self._stop_wifi_watcher()
        return command

    def get_listening_state(self):
        res = dict(wifi=None, ap=None, wired=None, findmrbeam=None)
        try:
            pluginInfo = self._plugin._plugin_manager.get_plugin_info("findmymrbeam")
            if (
                pluginInfo is not None
                and LooseVersion(pluginInfo.version) >= self.VERSION_MIN_FINDMRBEAM
            ):
                res["findmrbeam"] = pluginInfo.implementation.is_registered()
            else:
                # we know we can't read find state, so we must assume false
                res["findmrbeam"] = False
        except Exception as e:
            self._logger.exception(
                "Exception while reading is_registered state from findmymrbeam:"
            )

        try:
            pluginInfo = self._plugin._plugin_manager.get_plugin_info("netconnectd")
            if pluginInfo is not None:
                status = pluginInfo.implementation._get_status()
                if "wifi" in status["connections"]:
                    res["wifi"] = status["connections"]["wifi"]
                if "ap" in status["connections"]:
                    res["ap"] = status["connections"]["ap"]
                if "wired" in status["connections"]:
                    res["wired"] = status["connections"]["wired"]

                if status["connections"] not in self._connections_states:
                    self._connections_states.append(status["connections"])
                    self._analytics_handler.add_connections_state(status["connections"])
        except Exception as e:
            self._logger.exception(
                "Exception while reading wifi/ap state from netconnectd: {}".format(e)
            )

        return res

    def log_listening_state(self, command=None):
        self._logger.info(
            "LED Connectivity command: %s , state: %s, is_boot_grace_period: %s",
            command,
            self._listening_state,
            self._plugin.is_boot_grace_period(),
        )

    def _get_listening_command(self):
        command = self.LED_EVENTS[Events.STARTUP]
        if self._listening_state is not None and (
            self._listening_state["findmrbeam"] is not None
            or not self._plugin.is_boot_grace_period()
        ):
            if self._listening_state["findmrbeam"]:
                command = self.COMMAND_LISTENING_FINDMRBEAM
            elif self._listening_state["ap"] and (
                self._listening_state["wifi"] or self._listening_state["wired"]
            ):
                command = self.COMMAND_LISTENING_AP_AND_NET
            elif self._listening_state["ap"] and not (
                self._listening_state["wifi"] or self._listening_state["wired"]
            ):
                command = self.COMMAND_LISTENING_AP
            elif self._listening_state["wifi"] or self._listening_state["wired"]:
                command = self.COMMAND_LISTENING_NET
        self.log_listening_state(command=command)
        return command

    def _start_wifi_watcher(self, force=False):
        if force or not self._watch_thread or not self._watch_thread.is_alive:
            self._watch_thread = threading.Timer(
                self.WIFI_CHECK_INTERVAL, self.__run_wifi_watcher
            )
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
