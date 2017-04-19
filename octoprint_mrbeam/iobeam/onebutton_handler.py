import logging
import threading
import time

from octoprint.events import Events as OctoPrintEvents
from octoprint.settings import settings
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents

# singleton
_instance = None

def oneButtonHandler(plugin):
	global _instance
	if _instance is None:
		_instance = OneButtonHandler(plugin._event_bus,
									 plugin._plugin_manager,
									 plugin._file_manager,
									 plugin._printer)
	return _instance

# This guy handles OneButton Events.
# it basically also handles the ReadyToLaser state
class OneButtonHandler(object):

	PRINTER_STATE_PRINTING = "PRINTING"
	READY_TO_PRINT_MAX_WAITING_TIME = 120
	READY_TO_PRINT_CHECK_INTERVAL = 10

	PRESS_TIME_SHUTDOWN_PREPARE = 1.0 #seconds
	PRESS_TIME_SHUTDOWN_DOIT    = 5.0 #seconds

	SHUTDOWN_STATE_NONE       = 0
	SHUTDOWN_STATE_PREPARE    = 1
	SHUTDOWN_STATE_GOING_DOWN = 2

	def __init__(self, event_bus, plugin_manager, file_manager, printer):
		self._event_bus = event_bus
		self._plugin_manager = plugin_manager
		self._file_manager = file_manager
		self._printer = printer
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.onebutton_handler")
		self._subscribe()

		self.ready_to_laser_ts = -1
		self.ready_to_laser_file = None
		self.ready_to_laser_timer = None

		self.shutdown_command = self._get_shutdown_command()
		self.shutdown_state = self.SHUTDOWN_STATE_NONE

	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_DOWN, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_PRESSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_CLOSED, self.onEvent)

	def onEvent(self, event, payload):
		self._logger.debug("onEvent() event: %s, payload: %s, : self.shutdown_state: %s", event, payload, self.shutdown_state)
		if event == IoBeamEvents.ONEBUTTON_PRESSED:
			if self._printer.get_state_id() == self.PRINTER_STATE_PRINTING:
				self._printer.pause_print()
		elif event == IoBeamEvents.ONEBUTTON_DOWN:
			if self.shutdown_state == self.SHUTDOWN_STATE_NONE and float(payload) >= self.PRESS_TIME_SHUTDOWN_PREPARE:
				self.shutdown_state = self.SHUTDOWN_STATE_PREPARE
				self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE)
		elif event == IoBeamEvents.ONEBUTTON_RELEASED:
			if self.shutdown_state == self.SHUTDOWN_STATE_PREPARE and float(payload) >= self.PRESS_TIME_SHUTDOWN_DOIT:
				self.shutdown_state = self.SHUTDOWN_STATE_GOING_DOWN
				# shutdown the system
				self._shutdown()
			else:
				self.shutdown_state = self.SHUTDOWN_STATE_NONE
		elif event == OctoPrintEvents.CLIENT_CLOSED:
			self.ready_to_laser_ts = -1
			self._check_if_still_ready_to_laser()
		elif event == IoBeamEvents.ONEBUTTON_RELEASED:
			if self._printer.is_operational() and self.ready_to_laser_ts > 0:
				self._start_laser()


	def set_ready_to_laser(self, gcode_file):
		self._test_conditions(gcode_file)
		self.ready_to_laser_file = gcode_file
		self.ready_to_laser_ts = time.time()
		self._fireEvent(MrBeamEvents.READY_TO_LASER_START)
		self._plugin_manager.send_plugin_message("mrbeam", dict(ready_to_laser="start"))
		self._check_if_still_ready_to_laser()

	def unset_ready_to_laser(self, lasering=False):
		self._logger.debug("unset_ready_to_laser()")
		self._cancel_timer()
		self.ready_to_laser_ts = -1
		self.ready_to_laser_file = None
		if lasering:
			self._plugin_manager.send_plugin_message("mrbeam", dict(ready_to_laser="end_lasering"))
		else:
			self._plugin_manager.send_plugin_message("mrbeam", dict(ready_to_laser="end_canceled"))
			self._fireEvent(MrBeamEvents.READY_TO_LASER_CANCELED)

	def _check_if_still_ready_to_laser(self):
		if self.ready_to_laser_ts> 0 and time.time() - self.ready_to_laser_ts < self.READY_TO_PRINT_MAX_WAITING_TIME:
			self._logger.debug("_check_if_still_ready_to_laser() still ready")
			self._start_timer()
		else:
			self.unset_ready_to_laser(False)

	def _start_laser(self):
		self._logger.debug("_start_laser() ...shall we laser file %s ?", self.ready_to_laser_file)
		if self.ready_to_laser_ts <= 0 or time.time() - self.ready_to_laser_ts > self.READY_TO_PRINT_MAX_WAITING_TIME:
			self._logger.warn("_start_laser() READY_TO_PRINT_MAX_WAITING_TIME exceeded.")
			return

		self._test_conditions(self.ready_to_laser_file)

		self._logger.debug("_start_laser() LET'S LASER BABY!!! it's file %s", self.ready_to_laser_file)
		myFile = self._file_manager.path_on_disk("local", self.ready_to_laser_file)
		result = self._printer.select_file(myFile, False, True)

		self.unset_ready_to_laser(True)


	def _test_conditions(self, file):
		self._logger.debug("_test_conditions() laser file %s, printer state: %s", file, self._printer.get_state_id())

		if file is None:
			raise Exception("ReadyToLaser: file is None")
		if not self._file_manager.file_exists("local", file):
			raise Exception("ReadyToLaser: file not found '%s'" % file)
		if not valid_file_type(file, type="machinecode"):
			raise Exception("ReadyToLaser: file is not of type machine code")
		if not self._printer.is_operational() or not self._printer.get_state_id() == "OPERATIONAL":
			raise Exception("ReadyToLaser: printer is not ready. printer state is: %s" % self._printer.get_state_id())

	def _start_timer(self):
		self.ready_to_laser_timer = threading.Timer(self.READY_TO_PRINT_CHECK_INTERVAL,
													self._check_if_still_ready_to_laser).start()

	def _cancel_timer(self):
		if self.ready_to_laser_timer is not None:
			self.ready_to_laser_timer.cancel()
			self.ready_to_laser_timer = None

	def _get_shutdown_command(self):
		c = settings().get(["server", "commands", "systemShutdownCommand"])
		if c is None:
			self._logger.warn("No shutdown command in settings. Can't shut down system per OneButton.")
		return c

	def _shutdown(self):
		self._logger.info("Shutting system down...")
		if self.shutdown_command is not None:
			try:
				output = check_output(self.shutdown_command, shell=True)
			except Exception as e:
				self._logger.warn("Exception during OneButton shutdown: %s", e)
				pass
		else:
			self._logger.warn("No shutdown command in settings. Can't shut down system per OneButton.")


	def _fireEvent(self, event, payload=None):
		self._logger.info("_fireEvent() event:%s, payload:%s", event, payload)
		self._event_bus.fire(event, payload)
