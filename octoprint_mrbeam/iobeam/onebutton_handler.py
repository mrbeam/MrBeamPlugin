import logging
import threading
import time
from subprocess import check_output

from octoprint.events import Events as OctoPrintEvents
from octoprint.filemanager import valid_file_type
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents

# singleton
_instance = None

def oneButtonHandler(plugin):
	global _instance
	if _instance is None:
		_instance = OneButtonHandler(plugin._ioBeam,
									 plugin._event_bus,
									 plugin._plugin_manager,
									 plugin._file_manager,
									 plugin._settings,
									 plugin._printer)
	return _instance

# This guy handles OneButton Events and many more... It's more a Hydra now... :-/
# it basically also handles the ReadyToLaser state
class OneButtonHandler(object):

	PRINTER_STATE_PRINTING = "PRINTING"
	PRINTER_STATE_PAUSED = "PAUSED"

	CLIENT_RTL_STATE_START =        "start"
	CLIENT_RTL_STATE_START_PAUSE =  "start_pause"
	CLIENT_RTL_STATE_END_LASERING = "end_lasering"
	CLIENT_RTL_STATE_END_CANCELED = "end_canceled"
	CLIENT_RTL_STATE_END_RESUMED =  "end_resumed"

	READY_TO_PRINT_MAX_WAITING_TIME = 1200 #20min
	READY_TO_PRINT_CHECK_INTERVAL = 10
	LASER_PAUSE_WAITING_TIME = 3

	PRESS_TIME_SHUTDOWN_PREPARE = 1.0 #seconds
	PRESS_TIME_SHUTDOWN_DOIT    = 5.0 #seconds

	SHUTDOWN_STATE_NONE       = 0
	SHUTDOWN_STATE_PREPARE    = 1
	SHUTDOWN_STATE_GOING_DOWN = 2

	def __init__(self, iobeam, event_bus, plugin_manager, file_manager, settings, printer):
		self._iobeam = iobeam
		self._event_bus = event_bus
		self._plugin_manager = plugin_manager
		self._file_manager = file_manager
		self._settings = settings
		self._printer = printer
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.onebutton_handler")
		self._subscribe()

		self.ready_to_laser_ts = -1
		self.ready_to_laser_file = None
		self.ready_to_laser_timer = None

		self.pause_laser_ts = -1;
		self.pause_need_to_release = False
		self.pause_safety_timeout_timer = None

		self.shutdown_command = self._get_shutdown_command()
		self.shutdown_state = self.SHUTDOWN_STATE_NONE

	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_DOWN, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_PRESSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_OPEN, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_CLOSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_CLOSED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_PAUSED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self.onEvent)

	def onEvent(self, event, payload):
		self._logger.debug("onEvent() event:%s, payload:%s, : self.shutdown_state:%s, pause_laser_ts:%s, pause_need_to_release:%s",
						   event, payload, self.shutdown_state, self.pause_laser_ts, self.pause_need_to_release)

		if event == IoBeamEvents.ONEBUTTON_PRESSED:
			if self._printer.get_state_id() == self.PRINTER_STATE_PRINTING:
				self._logger.debug("onEvent() ONEBUTTON_PRESSED: self.pause_laser()")
				self.pause_laser()
			elif self.pause_need_to_release and self._is_during_pause_waiting_time():
				self._logger.debug("onEvent() ONEBUTTON_PRESSED: timeout block")
				self.pause_need_to_release = True
				self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_BLOCK)

		elif event == IoBeamEvents.ONEBUTTON_DOWN:
			# shutdown prepare
			if self.shutdown_state == self.SHUTDOWN_STATE_NONE and float(payload) >= self.PRESS_TIME_SHUTDOWN_PREPARE:
				self._logger.debug("onEvent() ONEBUTTON_DOWN: ShutdownPrepareStart")
				self.shutdown_state = self.SHUTDOWN_STATE_PREPARE
				self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE_START)
				# shutdown
			elif self.shutdown_state == self.SHUTDOWN_STATE_PREPARE and float(payload) >= self.PRESS_TIME_SHUTDOWN_DOIT:
				self._logger.debug("onEvent() ONEBUTTON_DOWN: shutdown!")
				self.shutdown_state = self.SHUTDOWN_STATE_GOING_DOWN
				self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE_SUCCESS)
				self._shutdown()
			elif not self.pause_need_to_release and self._is_during_pause_waiting_time():
				self._logger.debug("onEvent() ONEBUTTON_DOWN: timeout block")
				self.pause_need_to_release = True
				self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_BLOCK)

		elif event == IoBeamEvents.ONEBUTTON_RELEASED:
			if self.pause_need_to_release:
				self._logger.debug("onEvent() ONEBUTTON_RELEASED: set pause_need_to_release = false")
				self.pause_need_to_release = False
				return
			# end shutdown prepare
			if self.shutdown_state == self.SHUTDOWN_STATE_PREPARE:
				self._logger.debug("onEvent() ONEBUTTON_RELEASED: shutdown cancel")
				self.shutdown_state = self.SHUTDOWN_STATE_NONE
				self._fireEvent(MrBeamEvents.SHUTDOWN_PREPARE_CANCEL)
			# start laser
			elif self._printer.is_operational() and self.ready_to_laser_ts > 0 and self._iobeam.is_interlock_closed():
				self._logger.debug("onEvent() ONEBUTTON_RELEASED: start laser")
				self._start_laser()
			elif self._printer.get_state_id() == self.PRINTER_STATE_PAUSED:
				if self._is_during_pause_waiting_time():
					self._logger.debug("onEvent() ONEBUTTON_RELEASED: timeout block")
					self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_BLOCK)
				elif self._iobeam.is_interlock_closed():
				# else:
					self._logger.debug("onEvent() ONEBUTTON_RELEASED: resume_laser_if_waitingtime_is_over")
					self.resume_laser_if_waitingtime_is_over()

		elif event == IoBeamEvents.INTERLOCK_OPEN:
			if self._printer.get_state_id() == self.PRINTER_STATE_PRINTING:
				self._logger.debug("onEvent() INTERLOCK_OPEN: pausing laser")
				self.pause_laser(need_to_release=False)
			else:
				self._logger.debug("onEvent() INTERLOCK_OPEN: not printing, nothing to do. printer state is: %s", self._printer.get_state_id())

		# elif event == IoBeamEvents.INTERLOCK_CLOSED:
		elif event == OctoPrintEvents.PRINT_PAUSED:
			# Webinterface / OctoPrint caused the pause state
			if self.pause_laser_ts <= 0:
				self.pause_laser(need_to_release=False)

		elif event == OctoPrintEvents.PRINT_RESUMED:
			# Webinterface / OctoPrint caused the resume
			self._logger.debug("onEvent() PRINT_RESUMED")
			self._set_resumed()


		elif event == OctoPrintEvents.CLIENT_CLOSED:
			self.unset_ready_to_laser()


	def set_ready_to_laser(self, gcode_file):
		self._test_conditions(gcode_file)
		self.ready_to_laser_file = gcode_file
		self.ready_to_laser_ts = time.time()
		self._fireEvent(MrBeamEvents.READY_TO_LASER_START)
		self._send_frontend_ready_to_laser_state(self.CLIENT_RTL_STATE_START)
		self._check_if_still_ready_to_laser()

	def unset_ready_to_laser(self, lasering=False):
		self._logger.debug("unset_ready_to_laser()")
		self._cancel_ready_to_laser_timer()
		was_ready_to_laser = (self.ready_to_laser_ts > 0)
		self.ready_to_laser_ts = -1
		self.ready_to_laser_file = None

		self.pause_laser_ts = -1;
		self.pause_need_to_release = False
		self.pause_safety_timeout_timer = None
		self._cancel_pause_safety_timeout_timer()

		if lasering and was_ready_to_laser:
			self._send_frontend_ready_to_laser_state(self.CLIENT_RTL_STATE_END_LASERING)
		elif was_ready_to_laser:
			self._send_frontend_ready_to_laser_state(self.CLIENT_RTL_STATE_END_CANCELED)
			self._fireEvent(MrBeamEvents.READY_TO_LASER_CANCELED)

	def _check_if_still_ready_to_laser(self):
		if self.ready_to_laser_ts> 0 and time.time() - self.ready_to_laser_ts < self.READY_TO_PRINT_MAX_WAITING_TIME:
			self._start_ready_to_laser_timer()
		else:
			self.unset_ready_to_laser(False)

	def _start_laser(self):
		self._logger.debug("_start_laser() ...shall we laser file %s ?", self.ready_to_laser_file)
		if not (self._printer.is_operational() and self.ready_to_laser_ts > 0 and self._iobeam.is_interlock_closed()):
			self._logger.warn("_start_laser() Preconditions not met. Triggered per dev-start_button?")
			return
		if self.ready_to_laser_ts <= 0 or time.time() - self.ready_to_laser_ts > self.READY_TO_PRINT_MAX_WAITING_TIME:
			self._logger.warn("_start_laser() READY_TO_PRINT_MAX_WAITING_TIME exceeded.")
			return

		self._test_conditions(self.ready_to_laser_file)

		self._logger.debug("_start_laser() LET'S LASER BABY!!! it's file %s", self.ready_to_laser_file)
		myFile = self._file_manager.path_on_disk("local", self.ready_to_laser_file)
		result = self._printer.select_file(myFile, False, True)

		self.unset_ready_to_laser(True)


	# We raise these exceptions because these are all things we can't fix/handle here...
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

	def _start_ready_to_laser_timer(self):
		self.ready_to_laser_timer = threading.Timer(self.READY_TO_PRINT_CHECK_INTERVAL, self._check_if_still_ready_to_laser)
		self.ready_to_laser_timer.start()

	def _cancel_ready_to_laser_timer(self):
		if self.ready_to_laser_timer is not None:
			self.ready_to_laser_timer.cancel()
			self.ready_to_laser_timer = None

	def _start_pause_safety_timeout_timer(self):
		self.pause_safety_timeout_timer = threading.Timer(self.LASER_PAUSE_WAITING_TIME, self._end_pause_safety_timeout)
		self.pause_safety_timeout_timer.start()

	def _end_pause_safety_timeout(self):
		self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_END)

	def _cancel_pause_safety_timeout_timer(self):
		if self.pause_safety_timeout_timer is not None:
			self.pause_safety_timeout_timer.cancel()
			self.pause_safety_timeout_timer = None

	def pause_laser(self, need_to_release=True):
		self.pause_laser_ts = time.time()
		self.pause_need_to_release = need_to_release;
		self._printer.pause_print()
		self._fireEvent(MrBeamEvents.LASER_PAUSE_SAFTEY_TIMEOUT_START)
		self._send_frontend_ready_to_laser_state(self.CLIENT_RTL_STATE_START_PAUSE)
		self._start_pause_safety_timeout_timer()

	def _is_during_pause_waiting_time(self):
		return self.pause_laser_ts > 0 and time.time() - self.pause_laser_ts <= self.LASER_PAUSE_WAITING_TIME

	def resume_laser_if_waitingtime_is_over(self):
		if self._iobeam.is_interlock_closed():
			if self.pause_laser_ts > 0 and time.time() - self.pause_laser_ts > self.LASER_PAUSE_WAITING_TIME:
				self._printer.resume_print()
				self._send_frontend_ready_to_laser_state(self.CLIENT_RTL_STATE_END_RESUMED)
				self.pause_laser_ts = -1
				self._logger.debug("Resuming laser job...")
			else:
				self._logger.info("Not resuming laser job, still in waiting time.")

	def _set_resumed(self):
		self.pause_laser_ts = -1
		self._cancel_pause_safety_timeout_timer()

	def _send_frontend_ready_to_laser_state(self, state):
		self._logger.debug("_send_frontend_ready_to_laser_state() state: %s", state)
		self._plugin_manager.send_plugin_message("mrbeam", dict(ready_to_laser=state))

	def _get_shutdown_command(self):
		c = self._settings.global_get(["server", "commands", "systemShutdownCommand"])
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
