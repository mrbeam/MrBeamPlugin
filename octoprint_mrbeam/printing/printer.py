import logging
import time
from octoprint.util import dict_merge
from octoprint.printer.standard import Printer, StateMonitor
from octoprint.events import eventManager, Events
from octoprint_mrbeam.util.log import logExceptions, logme
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.printing import comm_acc2 as comm
from octoprint_mrbeam.mrb_logger import mrb_logger


class Laser(Printer):
    HOMING_POSITION = [-1.0, -1.0, 0]

    def __init__(self, fileManager, analysisQueue, printerProfileManager):
        Printer.__init__(self, fileManager, analysisQueue, printerProfileManager)
        self._logger = mrb_logger("octoprint.plugins.mrbeam.printing.printer.Laser")
        self._stateMonitor = LaserStateMonitor.fromStateMonitor(self._stateMonitor)

    # overwrite connect to use comm_acc2
    def connect(self, port=None, baudrate=None, profile=None):
        """
        Connects to the printer. If port and/or baudrate is provided, uses these settings, otherwise autodetection
        will be attempted.
        """
        self._init_terminal()
        #### OP code ####
        # TODO Add an abstraction Layer to the OP Printer and comm modules to eleviate on redundancy
        # @see all of the factories for the hooks
        if self._comm is not None:
            self.disconnect()

        eventManager().fire(Events.CONNECTING)
        self._printerProfileManager.select(profile)

        from octoprint.logging.handlers import SerialLogHandler

        SerialLogHandler.on_open_connection()
        if not logging.getLogger("SERIAL").isEnabledFor(logging.DEBUG):
            # if serial.log is not enabled, log a line to explain that to reduce "serial.log is empty" in tickets...
            logging.getLogger("SERIAL").info(
                "serial.log is currently not enabled, you can enable it via Settings > Serial Connection > Log communication to serial.log"
            )

        self._comm = comm.MachineCom(
            port,
            baudrate,
            callbackObject=self,
            printerProfileManager=self._printerProfileManager,
        )

    # send color settings to commAcc to inject settings into Gcode
    def set_colors(self, currentFileName, value):
        if self._comm is None:
            return
        self._comm.setColors(currentFileName, value)

    # extend commands: home, position, increase_passes, decrease_passes
    @logExceptions
    def home(self, axes, **kwargs):
        printer_profile = self._printerProfileManager.get_current_or_default()
        params = dict(
            x=printer_profile["volume"]["width"]
            + printer_profile["volume"]["working_area_shift_x"],
            y=printer_profile["volume"]["depth"]
            + printer_profile["volume"]["working_area_shift_y"],
            z=0,
        )
        self._comm.rescue_from_home_pos()
        command = "G92X{x}Y{y}Z{z}".format(**params)
        self.commands(["$H", command, "G90", "G21"])

    def is_homed(self):
        return self._stateMonitor._machinePosition == self.HOMING_POSITION

    @logExceptions
    def cancel_print(self, **kwargs):
        """
        Cancel the current printjob and do homing.
        """
        super(Laser, self).cancel_print()
        time.sleep(0.5)
        self.home(axes="wtf")

    @logExceptions
    def fail_print(self, error_msg=None, **kwargs):
        """
        Cancel the current printjob (as it failed) and do homing.
        """
        if self._comm is None:
            return

        # If we want the job to show as failed instead of cancelled, we have to mimic self._printer.cancel_print()
        self._comm.cancelPrint(failed=True, firmware_error=error_msg)

        time.sleep(0.5)
        self.home(axes="wtf")

    def position(self, x, y):
        printer_profile = self._printerProfileManager.get_current_or_default()
        movement_speed = min(
            printer_profile["axes"]["x"]["speed"], printer_profile["axes"]["y"]["speed"]
        )
        self.commands(["G90", "G0 X%.3f Y%.3f F%d" % (x, y, movement_speed)])

    def increase_passes(self):
        """
        increase the number of passes by one.
        """
        if self._comm is None:
            return
        self._comm.increasePasses()

    def set_passes(self, value):
        if self._comm is None:
            return
        self._comm.setPasses(value)

    def decrease_passes(self):
        """
        decrease the number of passes by one.
        """
        if self._comm is None:
            return
        self._comm.decreasePasses()

    @logExceptions
    def pause_print(self, force=False, trigger=None, **kwargs):
        """
        Pause the current printjob.
        """
        if self._comm is None:
            return

        if not force and self._comm.isPaused():
            return

        self._comm.setPause(True, send_cmd=True, trigger=trigger)

    @logExceptions
    def cooling_start(self, **kwargs):
        """
        Pasue the laser for cooling
        """
        if self._comm is None:
            return

        if self._comm.isPaused():
            return

        self._comm.setPause(True, pause_for_cooling=True, trigger="Cooling")

    # extend flags
    def is_locked(self):
        return self._comm is not None and self._comm.isLocked()

    def is_flashing(self):
        return self._comm is not None and self._comm.isFlashing()

    def _getStateFlags(self):
        # Extra gymnastics in case state flags are a frozen dict
        flags = Printer._getStateFlags(self)
        _dict = flags.__class__
        return _dict(
            dict_merge(
                dict(flags),
                {
                    "ready": flags["ready"] and not self.is_locked(),
                    "locked": self.is_locked(),
                    "flashing": self.is_flashing(),
                },
            )
        )

    # position update callbacks
    def on_comm_pos_update(self, MPos, WPos):
        self._add_position_data(MPos, WPos)

    # progress update callbacks
    def on_comm_progress(self):
        self._updateProgressData(
            self._comm.getPrintProgress(),
            self._comm.getPrintFilepos(),
            self._comm.getPrintTime(),
            self._comm.getCleanedPrintTime(),
        )
        self._stateMonitor.trigger_progress_update()

    def _add_position_data(self, MPos, WPos):
        """
        TODO This isn't clear, what is it for??
        """
        if MPos is not None:
            self._stateMonitor.setMachinePosition(MPos)
        if WPos is not None:
            self._stateMonitor.setWorkPosition(WPos)

    def _init_terminal(self):
        from collections import deque

        terminalMaxLines = _mrbeam_plugin_implementation._settings.get(
            ["dev", "terminalMaxLines"]
        )
        if terminalMaxLines is not None and terminalMaxLines > 0:
            self._log = deque(self._log, terminalMaxLines)

    # maybe one day we want to introduce special MrBeam commands....
    # def commands(self, commands):
    # 	"""
    # 	Sends one or more gcode commands to the printer.
    # 	"""
    # 	if self._comm is None:
    # 		return
    #
    # 	if not isinstance(commands, (list, tuple)):
    # 		commands = [commands]
    #
    # 	for command in commands:
    # 		self._logger.debug("Laser.commands() %s", command)
    # 		sendCommandToPrinter = True
    # 		if _mrbeam_plugin_implementation is not None:
    # 			sendCommandToPrinter = _mrbeam_plugin_implementation.execute_command(command)
    # 		if sendCommandToPrinter:
    # 			self._comm.sendCommand(command)


class LaserStateMonitor(StateMonitor):
    """
    TODO - What is the purpose of this class ??
    machinePosition: ?
    workPosition: ?
    """

    def __init__(self, *args, **kwargs):
        self.state_monitor = StateMonitor.__init__(self, *args, **kwargs)
        self._machinePosition = None
        self._workPosition = None

    @classmethod
    def fromStateMonitor(cls, state_monitor):
        """Casts the StateMonitor to LaserStateMonitor
        Beware, here be dragons - https://stackoverflow.com/a/49795902/11136955
        """
        assert isinstance(state_monitor, StateMonitor)
        state_monitor._machinePosition = None
        state_monitor._workPosition = None
        state_monitor.__class__ = cls
        assert isinstance(state_monitor, LaserStateMonitor)
        return state_monitor

    def setWorkPosition(self, workPosition):
        self._workPosition = workPosition
        self._change_event.set()

    def setMachinePosition(self, machinePosition):
        self._machinePosition = machinePosition
        self._change_event.set()

    def get_current_data(self):
        data = StateMonitor.get_current_data(self)
        data.update(
            {
                "workPosition": self._workPosition,
                "machinePosition": self._machinePosition,
            }
        )
        mrb_state = _mrbeam_plugin_implementation.get_mrb_state()
        if mrb_state:
            data["mrb_state"] = mrb_state
        return data


def laser_factory(components, *args, **kwargs):
    """
    Factory function for the Printer type used for the OctoPrint hook
    See ``octoprint.printer.factory``
    """
    from .profile import laserCutterProfileManager

    return Laser(
        components["file_manager"],
        components["analysis_queue"],
        laserCutterProfileManager(),
    )
