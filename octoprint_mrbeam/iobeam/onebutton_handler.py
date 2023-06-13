import threading
import time
from subprocess import check_output

from octoprint.events import Events as OctoPrintEvents
from octoprint.filemanager import valid_file_type
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from flask.ext.babel import gettext
from octoprint_mrbeam.printing.comm_acc2 import PrintingGcodeFromMemoryInformation

# singleton
_instance = None


def oneButtonHandler(plugin):
    global _instance
    if _instance is None:
        _instance = OneButtonHandler(
            plugin,
            plugin._event_bus,
            plugin._plugin_manager,
            plugin._file_manager,
            plugin._settings,
            plugin._printer,
        )
    return _instance


# This guy handles OneButton Events and many more... It's more a Hydra now... :-/
# it basically also handles the ReadyToLaser state
class OneButtonHandler(object):

    PRINTER_STATE_PRINTING = "PRINTING"
    PRINTER_STATE_PAUSED = "PAUSED"

    CLIENT_RTL_STATE_START = "start"
    CLIENT_RTL_STATE_START_PAUSE = "start_pause"
    CLIENT_RTL_STATE_END_LASERING = "end_lasering"
    CLIENT_RTL_STATE_END_CANCELED = "end_canceled"
    CLIENT_RTL_STATE_END_RESUMED = "end_resumed"

    READY_TO_PRINT_MAX_WAITING_TIME = 1200  # 20min
    READY_TO_PRINT_CHECK_INTERVAL = 1
    LASER_PAUSE_WAITING_TIME = 3

    PRESS_TIME_SHUTDOWN_PREPARE = 1.0  # seconds
    PRESS_TIME_SHUTDOWN_DOIT = 5.0  # seconds

    SHUTDOWN_STATE_NONE = 0
    SHUTDOWN_STATE_PREPARE = 1
    SHUTDOWN_STATE_GOING_DOWN = 2

    def __init__(
        self, plugin, event_bus, plugin_manager, file_manager, settings, printer
    ):
        self._plugin = plugin
        self._event_bus = event_bus
        self._plugin_manager = plugin_manager
        self._file_manager = file_manager
        self._settings = settings
        self._printer = printer
        self._user_notification_system = plugin.user_notification_system
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.onebutton_handler")
        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

        self.ready_to_laser_ts = -1
        self.ready_to_laser_flag = False
        self.ready_to_laser_file = None
        self.ready_to_laser_timer = None
        self.print_started = -1

        self.pause_laser_ts = -1
        self.pause_need_to_release = False
        self.pause_safety_timeout_timer = None

        self.shutdown_command = self._get_shutdown_command()
        self.shutdown_state = self.SHUTDOWN_STATE_NONE
        self.shutdown_prepare_was_initiated_during_pause_saftey_timeout = None

        self.behave_cooling_state = False
        self.intended_pause = False

        self.hardware_malfunction_notified = False

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._temperature_manager = self._plugin.temperature_manager
        self._iobeam = self._plugin.iobeam
        self._dust_manager = self._plugin.dust_manager
        self._hw_malfunction = self._plugin.hw_malfunction_handler

        self._subscribe()

    def _subscribe(self):
        self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_DOWN, self.onEvent)
        self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_PRESSED, self.onEvent)
        self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
        self._event_bus.subscribe(IoBeamEvents.INTERLOCK_OPEN, self.onEvent)
        self._event_bus.subscribe(IoBeamEvents.INTERLOCK_CLOSED, self.onEvent)
        self._event_bus.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.CLIENT_CLOSED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.SLICING_STARTED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.FILE_SELECTED, self.onEvent)
        self._event_bus.subscribe(MrBeamEvents.HARDWARE_MALFUNCTION, self.onEvent)

    def onEvent(self, event, payload):
        # first, log da shit...
        msg = ""
        msg += "event:{}".format(event)
        msg += ", payload:{}".format(payload)

        msg += " - shutdown_state:{}".format(self.shutdown_state)
        msg += (
            " - shutdown_prepare_was_initiated_during_pause_saftey_timeout:{}".format(
                self.shutdown_prepare_was_initiated_during_pause_saftey_timeout
            )
        )

        msg += ", is_ready_to_laser():{}".format(self.is_ready_to_laser())
        msg += ", ready_to_laser_ts:{}".format(self.ready_to_laser_ts)
        msg += ", ready_to_laser_flag:{}".format(self.ready_to_laser_flag)
        msg += ", ready_to_laser_file:{}".format(self.ready_to_laser_file)
        msg += ", ready_to_laser_timer:{}".format(self.ready_to_laser_timer)
        msg += ", print_started:{}".format(self.print_started)

        msg += ", pause_laser_ts:{}".format(self.pause_laser_ts)
        msg += ", pause_need_to_release:{}".format(self.pause_need_to_release)
        msg += ", pause_safety_timeout_timer:{}".format(self.pause_safety_timeout_timer)
        msg += ", _is_during_pause_waiting_time():{}".format(
            self._is_during_pause_waiting_time()
        )
        msg += ", behave_cooling_state:{}".format(self.behave_cooling_state)

        msg += ", _printer.get_state_id():{}".format(self._printer.get_state_id())
        msg += ", _printer.is_operational():{}".format(self._printer.is_operational())
        msg += ", _iobeam.is_interlock_closed():{}".format(self.is_interlock_closed())

        self._logger.debug("onEvent() %s", msg)

        # return if we're already shutting down
        if self.shutdown_state == self.SHUTDOWN_STATE_GOING_DOWN:
            self._logger.debug(
                "onEvent() SHUTDOWN_STATE_GOING_DOWN: no processing any further events."
            )
            return

        # ...and the we can go:
        if event == IoBeamEvents.ONEBUTTON_PRESSED:
            if (
                self.print_started > 0
                and time.time() - self.print_started > 1
                and self._printer.get_state_id() == self.PRINTER_STATE_PRINTING
            ):  # TODO replace with self._printer.is_printing() ?
                self._logger.debug("onEvent() ONEBUTTON_PRESSED: self.pause_laser()")
                self.pause_laser(
                    need_to_release=True,
                    trigger="OneButton pressed, regular pause mode",
                )
            elif (
                self.print_started > 0
                and time.time() - self.print_started > 1
                and self._printer.get_state_id() == self.PRINTER_STATE_PAUSED
                and self.behave_cooling_state
            ):
                self._logger.debug(
                    "onEvent() ONEBUTTON_PRESSED: stop_cooling_behavior and pause_laser()"
                )
                self.stop_cooling_behavior()
                self.pause_laser(
                    need_to_release=True,
                    trigger="OneButton pressed, stop_cooling_behavior and switch to pause_laser",
                )
            elif self.pause_need_to_release and self._is_during_pause_waiting_time():
                self._logger.debug("onEvent() ONEBUTTON_PRESSED: timeout block")
                self.pause_need_to_release = True
                self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_BLOCK)

        elif event == IoBeamEvents.ONEBUTTON_DOWN:
            # shutdown prepare
            if (
                self.shutdown_state == self.SHUTDOWN_STATE_NONE
                and float(payload) >= self.PRESS_TIME_SHUTDOWN_PREPARE
            ):
                self._logger.debug("onEvent() ONEBUTTON_DOWN: ShutdownPrepareStart")
                self.shutdown_prepare_start()
                # shutdown
            elif (
                self.shutdown_state == self.SHUTDOWN_STATE_PREPARE
                and float(payload) >= self.PRESS_TIME_SHUTDOWN_DOIT
            ):
                self._logger.debug("onEvent() ONEBUTTON_DOWN: shutdown!")
                self._shutdown()
            elif (
                not self.pause_need_to_release and self._is_during_pause_waiting_time()
            ):
                self._logger.debug("onEvent() ONEBUTTON_DOWN: timeout block")
                self.pause_need_to_release = True
                self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_BLOCK)

        elif event == IoBeamEvents.ONEBUTTON_RELEASED:
            # pause_need_to_release
            if (
                self.pause_need_to_release
                and self.shutdown_state == self.SHUTDOWN_STATE_NONE
            ):
                self._logger.debug(
                    "onEvent() ONEBUTTON_RELEASED: set pause_need_to_release = false"
                )
                self.pause_need_to_release = False
            # end shutdown prepare
            elif self.shutdown_state == self.SHUTDOWN_STATE_PREPARE:
                self._logger.debug("onEvent() ONEBUTTON_RELEASED: shutdown cancel")
                self.shutdown_prepare_cancel()
                self.pause_need_to_release = False
            # start laser
            elif (
                self._printer.is_operational()
                and self.ready_to_laser_ts > 0
                and self.is_interlock_closed()
                and self.is_fan_connected()
            ):
                self._logger.debug("onEvent() ONEBUTTON_RELEASED: start laser")
                self._start_laser()
            elif (
                self._printer.is_operational()
                and self.ready_to_laser_ts > 0
                and not (self.is_interlock_closed() and self.is_fan_connected())
            ):
                # can't start laser
                self._logger.debug(
                    "onEvent() ONEBUTTON_RELEASED: interlock open or fan not connected: sending BUTTON_PRESS_REJECT."
                )
                self._fireEvent(MrBeamEvents.BUTTON_PRESS_REJECT)
            # resume laser (or timeout block)
            elif self._printer.get_state_id() == self.PRINTER_STATE_PAUSED:
                if self._is_during_pause_waiting_time():
                    self._logger.debug("onEvent() ONEBUTTON_RELEASED: timeout block")
                    self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_BLOCK)
                elif not self.is_interlock_closed():
                    # TODO: switch to BUTTON_PRESS_REJECT
                    self._logger.debug(
                        "onEvent() ONEBUTTON_RELEASED: interlock open: sending LASER_PAUSE_SAFETY_TIMEOUT_BLOCK to have the light flash up."
                    )
                    self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_BLOCK)
                elif not self.is_fan_connected():
                    self._logger.debug(
                        "onEvent() ONEBUTTON_RELEASED: fan not connected: sending BUTTON_PRESS_REJECT."
                    )
                    self._fireEvent(MrBeamEvents.BUTTON_PRESS_REJECT)
                elif self.is_interlock_closed() and self.is_cooling():
                    self._logger.debug(
                        "onEvent() ONEBUTTON_RELEASED: start_cooling_behavior"
                    )
                    self.start_cooling_behavior()
                elif self.is_interlock_closed():
                    self._logger.debug(
                        "onEvent() ONEBUTTON_RELEASED: resume_laser_if_waitingtime_is_over"
                    )
                    self.resume_laser_if_waitingtime_is_over()

        elif event == IoBeamEvents.INTERLOCK_OPEN:
            if self._printer.get_state_id() == self.PRINTER_STATE_PRINTING:
                self._logger.debug("onEvent() INTERLOCK_OPEN: pausing laser")
                self.pause_laser(need_to_release=False, trigger="INTERLOCK_OPEN")
            elif (
                self._printer.get_state_id() == self.PRINTER_STATE_PAUSED
                and self.behave_cooling_state
            ):
                self._logger.debug(
                    "onEvent() INTERLOCK_OPEN: pausing from cooling state"
                )
                self.pause_laser(
                    need_to_release=False, trigger="INTERLOCK_OPEN during cooling pause"
                )
                self.stop_cooling_behavior()
            else:
                self._logger.debug(
                    "onEvent() INTERLOCK_OPEN: not printing, nothing to do. printer state is: %s",
                    self._printer.get_state_id(),
                )

        elif event == OctoPrintEvents.SLICING_STARTED:
            self.hardware_malfunction_notified = False

        # OctoPrint 1.3.4 doesn't provide the file name in FILE_SELECTED anymore, so we need to get it here and save it for later.
        elif event == OctoPrintEvents.SLICING_DONE:
            if (
                not self.is_ready_to_laser()
                and self._printer.is_operational()
                and not self._printer.get_state_id()
                in (self.PRINTER_STATE_PRINTING, self.PRINTER_STATE_PAUSED)
            ):
                self._logger.debug(
                    "onEvent() SLICING_DONE set_rtl_file filename: %s:",
                    "gcode" in payload,
                )
                try:
                    self.set_rtl_file(payload["gcode"])
                except:
                    self._logger.exception("Error while setting ready_to_laser_file.")

        elif event == OctoPrintEvents.FILE_SELECTED:
            if (
                not self.is_ready_to_laser(False)
                and self._printer.is_operational()
                and not self._printer.get_state_id()
                in (self.PRINTER_STATE_PRINTING, self.PRINTER_STATE_PAUSED)
                and ("filename" in payload or len(payload) == 0)
            ):
                self._logger.debug(
                    "onEvent() FILE_SELECTED set_ready_to_laser filename: %s:",
                    "filename" in payload,
                )
                try:
                    # OctoPrint 1.3.4 doesn't provide the file name anymore
                    path = payload["path"] if "path" in payload else None
                    self.set_ready_to_laser(path)
                except Exception as e:
                    self._logger.exception(
                        "Error while going into state ReadyToLaser: {}".format(e)
                    )

        elif event == OctoPrintEvents.PRINT_STARTED:
            self._logger.debug("onEvent() print_started = True")
            self.print_started = time.time()

        elif event == OctoPrintEvents.PRINT_PAUSED:
            # Webinterface / OctoPrint caused the pause state but ignore cooling state
            if self.pause_laser_ts <= 0 and (
                "cooling" not in payload or not payload["cooling"]
            ):
                self._logger.debug("onEvent() pause_laser(need_to_release=False)")
                self.pause_laser(
                    need_to_release=False,
                    trigger="OctoPrintEvents.PRINT_PAUSED",
                    pause_print=False,
                )

        elif event == OctoPrintEvents.PRINT_RESUMED:
            # Webinterface / OctoPrint caused the resume
            self._logger.debug("onEvent() _reset_pause_configuration()")
            self._reset_pause_configuration()

        elif event == OctoPrintEvents.CLIENT_CLOSED:
            self.unset_ready_to_laser(lasering=False)

        elif event == MrBeamEvents.HARDWARE_MALFUNCTION:
            # iobeam could set stop_laser to false to avoid cancellation of current laserjob
            if payload["data"].get(
                "stop_laser", True
            ) and self._printer.get_state_id() in (
                self.PRINTER_STATE_PRINTING,
                self.PRINTER_STATE_PAUSED,
            ):
                self._logger.warn("Hardware Malfunction: cancelling laser job!")
                self._printer.fail_print(error_msg="HW malfunction during job")

    def is_cooling(self):
        return self._temperature_manager.is_cooling()

    def is_printing(self):
        return self._printer.get_state_id() == self.PRINTER_STATE_PRINTING

    def is_paused(self):
        return self._printer.is_paused()

    def cooling_down_pause(self):
        self.start_cooling_behavior()
        self._printer.cooling_start()

    def cooling_down_end(self, only_if_behavior_is_cooling=False):
        if not only_if_behavior_is_cooling or self.behave_cooling_state:
            self.stop_cooling_behavior()
            if self.is_interlock_closed():
                self._printer.resume_print()

    def stop_cooling_behavior(self):
        self.behave_cooling_state = False

    def start_cooling_behavior(self):
        self.behave_cooling_state = True

    def set_rtl_file(self, gcode_file):
        self._test_conditions(gcode_file)
        self.ready_to_laser_file = gcode_file

    def set_ready_to_laser(self, gcode_file=None):
        if gcode_file is not None:
            self._test_conditions(gcode_file)
            self.ready_to_laser_file = gcode_file
        self.ready_to_laser_flag = True
        self.ready_to_laser_ts = time.time()
        self.print_started = -1
        self._fireEvent(MrBeamEvents.READY_TO_LASER_START)
        self._check_if_still_ready_to_laser()

    def unset_ready_to_laser(self, lasering=False):
        self._logger.debug("unset_ready_to_laser()")
        self._cancel_ready_to_laser_timer()
        was_ready_to_laser = self.ready_to_laser_ts > 0
        self.ready_to_laser_ts = -1
        self.ready_to_laser_file = None
        self.ready_to_laser_flag = False
        if not lasering and was_ready_to_laser:
            self._fireEvent(MrBeamEvents.READY_TO_LASER_CANCELED)
        if (
            self._hw_malfunction.hardware_malfunction
            and not self.hardware_malfunction_notified
        ):
            self._logger.error(
                "Hardware Malfunction: Not possible to start laser job. %s",
                self._hw_malfunction.get_messages_to_show(),
                analytics="Hardware Malfunction: Not possible to start laser job",
            )
            self._hw_malfunction.show_hw_malfunction_notification()
            self.hardware_malfunction_notified = True

    def is_ready_to_laser(self, rtl_expected_to_be_there=True):
        return (
            self.ready_to_laser_ts > 0
            and time.time() - self.ready_to_laser_ts
            < self.READY_TO_PRINT_MAX_WAITING_TIME
            and self.ready_to_laser_flag
            and (not rtl_expected_to_be_there or self.ready_to_laser_file is not None)
            and self.print_started < 0
            and not self._hw_malfunction.hardware_malfunction
        )

    def is_intended_pause(self):
        """
        This is called by com_acc2 to avoid unintended pauses
        :return: Boolean
        """
        return self.intended_pause or self.behave_cooling_state

    def _check_if_still_ready_to_laser(self):
        self._iobeam.request_available_malfunctions()  # check if malfunctions are present
        if self.is_ready_to_laser():
            self._start_ready_to_laser_timer()
        else:
            self.unset_ready_to_laser(lasering=False)

    def _start_laser(self):
        self._logger.debug(
            "_start_laser() ...shall we laser file %s ?", self.ready_to_laser_file
        )
        if not self.ready_to_laser_flag:
            self._logger.warn(
                "_start_laser() Preconditions not met: self.ready_to_laser_flag not True"
            )
            return
        if not (
            self._printer.is_operational()
            and self.ready_to_laser_ts > 0
            and self.is_interlock_closed()
        ):
            self._logger.warn(
                "_start_laser() Preconditions not met. Triggered per dev-start_button?"
            )
            return
        if (
            self.ready_to_laser_ts <= 0
            or time.time() - self.ready_to_laser_ts
            > self.READY_TO_PRINT_MAX_WAITING_TIME
        ):
            self._logger.warn(
                "_start_laser() READY_TO_PRINT_MAX_WAITING_TIME exceeded."
            )
            return

        # TODO: these guys throw exceptions that are not handled
        self._test_conditions(self.ready_to_laser_file)
        self._check_system_integrity()

        self._reset_pause_configuration()

        self._logger.debug(
            "_start_laser() LET'S LASER BABY!!! it's file %s", self.ready_to_laser_file
        )
        myFile = self._file_manager.path_on_disk("local", self.ready_to_laser_file)
        result = self._printer.select_file(myFile, False, True)

        self.unset_ready_to_laser(lasering=True)

    # I guess there's no reason anymore to raise these exceptions. Just returning false would be better.
    def _test_conditions(self, file):
        self._logger.debug(
            "_test_conditions() laser file %s, printer state: %s",
            file,
            self._printer.get_state_id(),
        )
        self._logger.debug("file %s, class %s, str %s", file, file.__class__, str(file))

        if (
            str(file) is "in_memory_gcode"
        ):  # should be (but doesn't work) isinstance(PrintingGcodeFromMemoryInformation):
            if (
                not self._printer.is_operational()
                or not self._printer.get_state_id() == "OPERATIONAL"
            ):
                raise Exception(
                    "ReadyToLaser: printer is not ready. printer state is: %s"
                    % self._printer.get_state_id()
                )

        else:
            if (
                not self._printer.is_operational()
                or not self._printer.get_state_id() == "OPERATIONAL"
            ):
                raise Exception(
                    "ReadyToLaser: printer is not ready. printer state is: %s"
                    % self._printer.get_state_id()
                )
            if file is None:
                raise Exception("ReadyToLaser: file is None")
            if not self._file_manager.file_exists("local", file):
                raise Exception("ReadyToLaser: file not found '%s'" % file)
            if not valid_file_type(file, type="machinecode"):
                raise Exception("ReadyToLaser: file is not of type machine code")

    def _check_system_integrity(self):
        """We're going to need a concept of what to do if something here
        fails...

        :return:
        """
        temp_ok = self._temperature_manager.is_temperature_recent()
        if not temp_ok:
            msg = "iobeam: Laser temperature not available"
            self._user_notification_system.show_notifications(
                self._user_notification_system.get_legacy_notification(
                    title="Error",
                    text=msg,
                    is_err=True,
                )
            )
            raise Exception(msg)

        iobeam_ok = self._iobeam.is_iobeam_version_ok()
        if not iobeam_ok:
            self._iobeam.notify_user_old_iobeam()
            raise Exception("iobeam version is outdated. Please try Software update.")

        if (
            self._hw_malfunction.hardware_malfunction
            and not self.hardware_malfunction_notified
        ):
            self._logger.error(
                "Hardware Malfunction: Not possible to start laser job. %s",
                self._hw_malfunction.get_messages_to_show(),
                analytics="Hardware Malfunction: Not possible to start laser job",
            )
            self._user_notification_system.replay_notifications()
            self.hardware_malfunction_notified = True
            raise Exception("Hardware Malfunction: Not possible to start laser job.")

    def _start_ready_to_laser_timer(self):
        self.ready_to_laser_timer = threading.Timer(
            self.READY_TO_PRINT_CHECK_INTERVAL, self._check_if_still_ready_to_laser
        )
        self.ready_to_laser_timer.daemon = True
        self.ready_to_laser_timer.start()

    def _cancel_ready_to_laser_timer(self):
        if self.ready_to_laser_timer is not None:
            self.ready_to_laser_timer.cancel()
            self.ready_to_laser_timer = None

    def _start_pause_safety_timeout_timer(self):
        self.pause_safety_timeout_timer = threading.Timer(
            self.LASER_PAUSE_WAITING_TIME, self._end_pause_safety_timeout
        )
        self.pause_safety_timeout_timer.daemon = True
        self.pause_safety_timeout_timer.start()

    def _end_pause_safety_timeout(self):
        if self.shutdown_state != self.SHUTDOWN_STATE_PREPARE:
            self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_END)
        self._cancel_pause_safety_timeout_timer()

    def _cancel_pause_safety_timeout_timer(self):
        if self.pause_safety_timeout_timer is not None:
            self.pause_safety_timeout_timer.cancel()
            self.pause_safety_timeout_timer = None

    def pause_laser(
        self, need_to_release=True, force=False, trigger=None, pause_print=True
    ):
        """Pauses laser, switches machine to paused mode.

        :param need_to_release: If True (default), machine does not accept a button press for some period (3sec) and indicates this per leds.
                        This is a safety feature to prevent user from pausing and immediately resuming laser in case if he presses the button multiple times because he's nervous.
                        This is not needed if pause mode is triggered by other mechanisms than the button.
        :param force: Forwarded to _printer. If False, com_acc isn't called if printer is already in paused state
        :param trigger: Used for debugging purposes.
        :param pause_print: Indicates if the pause_print method from Octoprint should be called. This is not necessary
                        if OctoPrint already did (so if the trigger was OctoPrintEvents.PRINT_PAUSED).
        """
        self.pause_laser_ts = time.time()
        self.intended_pause = True
        self.pause_need_to_release = self.pause_need_to_release or need_to_release

        if pause_print:
            self._printer.pause_print(force=force, trigger=trigger)

        self._fireEvent(
            MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_START,
            payload=dict(trigger=trigger, mrb_state=self._plugin.get_mrb_state()),
        )
        self._start_pause_safety_timeout_timer()

    def _is_during_pause_waiting_time(self):
        return (
            self.pause_laser_ts > 0
            and time.time() - self.pause_laser_ts <= self.LASER_PAUSE_WAITING_TIME
        )

    def resume_laser_if_waitingtime_is_over(self):
        if self.is_interlock_closed():
            if not self._is_during_pause_waiting_time():
                self._logger.debug("Resuming laser job...")
                self._printer.resume_print()
                self.pause_laser_ts = -1
                self.intended_pause = False
            else:
                self._logger.info("Not resuming laser job, still in waiting time.")

    def _reset_pause_configuration(self):
        self.pause_laser_ts = -1
        self.intended_pause = False
        self.pause_need_to_release = False
        self._cancel_pause_safety_timeout_timer()

    def shutdown_prepare_start(self):
        self.shutdown_state = self.SHUTDOWN_STATE_PREPARE
        self.shutdown_prepare_was_initiated_during_pause_saftey_timeout = (
            self._is_during_pause_waiting_time()
        )
        self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE_START)

    def shutdown_prepare_cancel(self):
        self.shutdown_state = self.SHUTDOWN_STATE_NONE
        self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE_CANCEL)
        if (
            self.shutdown_prepare_was_initiated_during_pause_saftey_timeout
            and not self._is_during_pause_waiting_time()
        ):
            # we didn't fire this event when it actually timed out, so let's make up leeway
            self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFETY_TIMEOUT_END)
        self.shutdown_prepare_was_initiated_during_pause_saftey_timeout = None

    def is_interlock_closed(self):
        if self._iobeam:
            return self._iobeam.is_interlock_closed()
        else:
            raise Exception("iobeam handler not available from Plugin.")

    def is_fan_connected(self):
        if self._dust_manager:
            return self._dust_manager.is_fan_connected()
        else:
            raise Exception("dust_manager handler not available from Plugin.")

    def _get_shutdown_command(self):
        c = self._settings.global_get(["server", "commands", "systemShutdownCommand"])
        if c is None:
            self._logger.warn(
                "No shutdown command in settings. Can't shut down system per OneButton."
            )
        return c

    def _shutdown(self):
        self._logger.info("Shutting system down...")

        self.shutdown_state = self.SHUTDOWN_STATE_GOING_DOWN
        self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE_SUCCESS)

        self._iobeam.shutdown_fan()

        if self.shutdown_command is not None:
            try:
                output = check_output(self.shutdown_command, shell=True)
            except Exception as e:
                self._logger.warn("Exception during OneButton shutdown: %s", e)
                pass
        else:
            self._logger.warn(
                "No shutdown command in settings. Can't shut down system per OneButton."
            )

    def _fireEvent(self, event, payload=None):
        self._plugin.fire_event(event, payload)
