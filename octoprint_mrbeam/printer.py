import traceback
import time
from octoprint.printer.standard import Printer, StateMonitor, PrinterInterface
from octoprint.settings import settings
from octoprint.events import eventManager, Events
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from . import comm_acc2 as comm
from octoprint_mrbeam.mrb_logger import mrb_logger

class Laser(Printer):

	def __init__(self, fileManager, analysisQueue, printerProfileManager):
		Printer.__init__(self, fileManager, analysisQueue, printerProfileManager)
		self._logger = mrb_logger("octoprint.plugins.mrbeam.printer")
		self._stateMonitor = LaserStateMonitor(
			interval=0.5,
			on_update=self._sendCurrentDataCallbacks,
			on_add_temperature=self._sendAddTemperatureCallbacks,
			on_add_log=self._sendAddLogCallbacks,
			on_add_message=self._sendAddMessageCallbacks,
			on_get_progress = self._updateProgressDataCallback
		)
		self._stateMonitor.reset(
			state={"text": self.get_state_string(), "flags": self._getStateFlags()},
			job_data={
				"file": {
					"name": None,
					"size": None,
					"origin": None,
					"date": None
				},
				"estimatedPrintTime": None,
				"lastPrintTime": None,
				"filament": {
					"length": None,
					"volume": None
				}
			},
			progress={"completion": None, "filepos": None, "printTime": None, "printTimeLeft": None},
			current_z=None
		)

	# overwrite connect to use comm_acc2
	def connect(self, port=None, baudrate=None, profile=None):
		"""
		 Connects to the printer. If port and/or baudrate is provided, uses these settings, otherwise autodetection
		 will be attempted.
		"""
		self._init_terminal()

		if self._comm is not None:
			self._comm.close()

		eventManager().fire(Events.CONNECTING, payload=dict(profile=profile))
		self._printerProfileManager.select(profile)
		self._comm = comm.MachineCom(port, baudrate, callbackObject=self, printerProfileManager=self._printerProfileManager)

	# overwrite operational state to accept commands in locked state
	def is_operational(self):
		return Printer.is_operational(self) or self.is_locked()

	# send color settings to commAcc to inject settings into Gcode
	def set_colors(self, currentFileName,value):
		if self._comm is None:
			return
		self._comm.setColors(currentFileName,value)

	# extend commands: home, position, increase_passes, decrease_passes
	def home(self, axes):
		printer_profile = self._printerProfileManager.get_current_or_default()
		params = dict(
			x=printer_profile['volume']['width'] + printer_profile['volume']['working_area_shift_x'],
			y=printer_profile['volume']['depth'] + printer_profile['volume']['working_area_shift_y'],
			z=0
		)
		self._comm.rescue_from_home_pos()
		command = "G92X{x}Y{y}Z{z}".format(**params)
		self.commands(["$H", command, "G90", "G21"])

	def cancel_print(self):
		"""
		 Cancel the current printjob and do homing.
		"""
		super(Laser, self).cancel_print()
		time.sleep(0.5)
		self.home(axes="wtf")
		eventManager().fire(MrBeamEvents.PRINT_CANCELING_DONE)

	def position(self, x, y):
		printer_profile = self._printerProfileManager.get_current_or_default()
		movement_speed = min(printer_profile["axes"]["x"]["speed"], printer_profile["axes"]["y"]["speed"])
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

	def select_file(self, path, sd, printAfterSelect=False, pos=None):
		self._logger.info("ANDYTEST printer.select_file() path: %s, sd: %s, printAfterSelect: %s, pos %s", path, sd, printAfterSelect, pos)
		if self._comm is None:
			self._logger.error("select_file() _comm is None")
			return

		self._printAfterSelect = printAfterSelect
		self._posAfterSelect = pos
		# self._comm.selectFile("/" + path if sd else path, sd)
		# self._comm.selectFile(path, sd, printAfterSelect=printAfterSelect, pos=pos)
		self._comm.selectFile(path, sd)
		self._updateProgressData()
		# self._setCurrentZ(None)


	def pause_print(self, force=False, trigger=None):
		"""
		Pause the current printjob.
		"""
		if self._comm is None:
			return

		if not force and self._comm.isPaused():
			return

		self._comm.setPause(True, send_cmd=True, trigger=trigger)

	def cooling_start(self):
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

	def is_readyToLaser(self):
		return self._comm is not None and self._comm.isReadyToLaser()

	def _getStateFlags(self):
		flags = Printer._getStateFlags(self)
		flags.update({
			"locked": self.is_locked(),
			"flashing": self.is_flashing(),
			"readyToLaser": self.is_readyToLaser(),
		})
		return flags

	# position update callbacks
	def on_comm_pos_update(self, MPos, WPos):
		self._add_position_data(MPos, WPos)

	# progress update callbacks
	def on_comm_progress(self):
		self._updateProgressData(self._comm.getPrintProgress(), self._comm.getPrintFilepos(), self._comm.getPrintTime(), self._comm.getCleanedPrintTime())
		self._stateMonitor.trigger_progress_update()

	def _add_position_data(self, MPos, WPos):
		if MPos is None or WPos is None:
			MPos = WPos = [0, 0, 0]
		self._stateMonitor.setWorkPosition(WPos)
		self._stateMonitor.setMachinePosition(MPos)

	def _init_terminal(self):
		from collections import deque
		terminalMaxLines = _mrbeam_plugin_implementation._settings.get(['dev', 'terminalMaxLines'])
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
	def __init__(self, *args, **kwargs):
		StateMonitor.__init__(self, *args, **kwargs)
		self._machinePosition = None
		self._workPosition = None

	def setWorkPosition(self, workPosition):
		self._workPosition = workPosition
		self._change_event.set()

	def setMachinePosition(self, machinePosition):
		self._machinePosition = machinePosition
		self._change_event.set()

	def get_current_data(self):
		data = StateMonitor.get_current_data(self)
		data.update({
			"workPosition": self._workPosition,
			"machinePosition": self._machinePosition
		})
		return data
