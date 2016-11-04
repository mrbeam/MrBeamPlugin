from octoprint.printer.standard import Printer, StateMonitor, PrinterInterface
from octoprint.settings import settings
from . import comm_acc2 as comm

class Laser(Printer):

	def __init__(self, fileManager, analysisQueue, printerProfileManager):
		Printer.__init__(self, fileManager, analysisQueue, printerProfileManager)
		self._stateMonitor = LaserStateMonitor(
			interval=0.5,
			on_update=self._sendCurrentDataCallbacks,
			on_add_temperature=self._sendAddTemperatureCallbacks,
			on_add_log=self._sendAddLogCallbacks,
			on_add_message=self._sendAddMessageCallbacks
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
		if self._comm is not None:
			self._comm.close()
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
		self.commands(["$H", "G92X500Y400Z0", "G90", "G21"])

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


	# extend flags
	def is_locked(self):
		return self._comm is not None and self._comm.isLocked()

	def is_flashing(self):
		return self._comm is not None and self._comm.isFlashing()

	def _getStateFlags(self):
		flags = Printer._getStateFlags(self)
		flags.update({
			"locked": self.is_locked(),
			"flashing": self.is_flashing(),
		})
		return flags

	# position update callbacks
	def on_comm_pos_update(self, MPos, WPos):
		self._add_position_data(MPos, WPos)

	# progress update callbacks
	def on_comm_progress(self):
		self._setProgressData(self._comm.getPrintProgress(), self._comm.getPrintFilepos(), self._comm.getPrintTime(), self._comm.getCleanedPrintTime())

	def _add_position_data(self, MPos, WPos):
		if MPos is None or WPos is None:
			MPos = WPos = [0, 0, 0]
		self._stateMonitor.setWorkPosition(WPos)
		self._stateMonitor.setMachinePosition(MPos)


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
