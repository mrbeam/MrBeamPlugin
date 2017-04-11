import socket
import os
import threading
import time
import logging

from octoprint_mrbeam.led_events import MrBeamEvents
from octoprint.events import Events as OctoPrintEvents
from octoprint.filemanager import valid_file_type



# singleton
_instance = None

def ioBeamHandler(eventBusOct, socket_file=None):
	global _instance
	if _instance is None:
		_instance = IoBeamHandler(eventBusOct, socket_file)
	return _instance


class IoBeamEvents(object):
	CONNECT =            "iobeam.connect"
	DISCONNECT =         "iobeam.disconnect"
	ONEBUTTON_PRESSED =  "iobeam.onebutton.pressed"
	ONEBUTTON_DOWN =     "iobeam.onebutton.down"
	ONEBUTTON_RELEASED = "iobeam.onebutton.released"
	INTERLOCK_OPEN =     "iobeam.interlock.open"
	INTERLOCK_CLOSED =   "iobeam.interlock.closed"


class IoBeamHandler(object):

	# > onebtn:pr
	# > onebtn:dn:< time >
	# > onebtn:rl:< time >
	# > onebtn:error	?
	# > lid:pr
	# > lid:dn:< time >
	# > lid:rl:< time >
	# > intlk:0:op
	# > intlk:0:cl
	# > intlk:1:op
	# > intlk:1:cl
	# > intlk:2:op
	# > intlk:2:cl
	# > intlk:3:op
	# > intlk:3:cl
	# > steprun:en
	# > steprun:di

	# < fan:on:< value0 - 100 >
	# > fan:on:ok
	# < fan:off
	# > fan:off:ok
	# < fan:auto
	# > fan:auto:ok
	# < fan:factor:< factor >
	# > fan:factor:ok
	# < fan:version
	# > fan:version:<version-string>
	# < fan:dust
	# > fan:dust:<dust value 0.3>
	# < fan:rpm
	# > fan:rpm:<rpm value>

	# < laser:temp
	# > laser:temp:< temperatur >
	# > laser:temp:error:<error type or message>


	SOCKET_FILE = "/var/run/mrbeam_iobeam.sock"
	MAX_ERRORS = 10

	MESSAGE_LENGTH_MAX = 1024
	MESSAGE_NEWLINE = "\n"
	MESSAGE_SEPARATOR = ":"
	MESSAGE_ERROR = "error"

	MESSAGE_DEVICE_ONEBUTTON =          "onebtn"
	MESSAGE_DEVICE_LID =   		        "lid"
	MESSAGE_DEVICE_INTERLOCK =          "intlk"
	MESSAGE_DEVICE_STEPRUN =            "steprun"
	MESSAGE_DEVICE_FAN =	            "fan"
	MESSAGE_DEVICE_LASER =	            "laser"

	MESSAGE_ACTION_ONEBUTTON_PRESSED =  "pr"
	MESSAGE_ACTION_ONEBUTTON_DOWN =     "dn"
	MESSAGE_ACTION_ONEBUTTON_RELEASED = "rl"

	MESSAGE_ACTION_INTERLOCK_OPEN =     "op"
	MESSAGE_ACTION_INTERLOCK_CLOSED =   "cl"


	def __init__(self, event_bus, socket_file=None):
		self._event_bus = event_bus
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam")

		self._shutdown_signaled = False
		self._isConnected = False
		self._errors = 0

		self._connectionException = None
		self._interlocks = dict()

		self._initWorker(socket_file)

	def isRunning(self):
		return self._worker.is_alive()

	def isConnected(self):
		return self._isConnected

	def shutdown(self):
		global _instance
		_instance = None
		self._logger.debug("shutdown()")
		self._shutdown_signaled = True

	def is_interlock_closed(self):
		return len(self._interlocks.keys()) == 0

	def open_interlocks(self):
		return self._interlocks.keys()

	def _initWorker(self, socket_file=None):
		self._logger.debug("initializing worker thread")

		# this is needed for unit tests
		if socket_file is not None:
			self.SOCKET_FILE = socket_file

		self._worker = threading.Thread(target=self._work)
		self._worker.daemon = True
		self._worker.start()


	def _work(self):
		self._logger.debug("Worker thread starting, connecting to socket: %s %s", self.SOCKET_FILE, ("MRBEAM_DEBUG" if MRBEAM_DEBUG else ""))

		while not self._shutdown_signaled:
			mySocket = None
			try:
				mySocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				mySocket.settimeout(3)
				# self._logger.debug("Connecting to socket...")
				mySocket.connect(self.SOCKET_FILE)
			except socket.error as e:
				self._isConnected = False
				if not self._connectionException == str(e):
					self._logger.warn("IoBeamHandler not able to connect to socket %s, reason: %s. I'll keept trying but I won't log further failures.", self.SOCKET_FILE, e)
					self._connectionException = str(e)
				time.sleep(1)
				continue

			self._isConnected = True
			self._errors = 0
			self._connectionException = None
			self._logger.debug("Socket connected")
			self._fireEvent(IoBeamEvents.CONNECT)

			while not self._shutdown_signaled:
				try:
					data = mySocket.recv(self.MESSAGE_LENGTH_MAX)
				except Exception as e:
					if MRBEAM_DEBUG and e.message == "timed out":
						self._logger.warn("Connection stale but MRBEAM_DEBUG enabled. Continuing....")
						continue
					else:
						self._logger.warn("Exception while sockect.recv(): %s - Resetting connection...", e)
						break


				if not data:
					self._logger.warn("Connection ended from other side. Closing connection...")
					break

				# here we see what's in the data...
				valid = self._handleMessages(data)
				if not valid:
					self._errors += 1
					if self._errors >= self.MAX_ERRORS:
						self._logger.warn("Received invalid message, error_count=%s, Resetting connection...", self._errors)
						break
					else:
						self._logger.warn("Received invalid message, error_count=%s", self._errors)


			if mySocket is not None:
				self._logger.debug("Closing socket...")
				mySocket.close()

			self._isConnected = False
			self._fireEvent(IoBeamEvents.DISCONNECT)

			if not self._shutdown_signaled:
				self._logger.debug("Sleeping for a sec before reconnecting...")
				time.sleep(1)

		self._logger.debug("Worker thread stopped.")


	# handles incoming data from the socket.
	# @return bool False if data is (partially) invalid and connection needs to be reset, true otherwise
	def _handleMessages(self, data):
		if not data: return False

		message_list = data.split(self.MESSAGE_NEWLINE)
		for message in message_list:
			if not message: continue

			self._logger.debug("_handleMessages() handling message: %s", message)

			tokens = message.split(self.MESSAGE_SEPARATOR)
			if len(tokens) <=1: return self._handle_invalid_message(message)

			device = tokens.pop(0)
			if device == self.MESSAGE_DEVICE_ONEBUTTON:
				return self._handle_onebutton_message(message, tokens)
			elif device == self.MESSAGE_DEVICE_LID:
				return self._handle_lid_message(message, tokens)
			elif device == self.MESSAGE_DEVICE_INTERLOCK:
				return self._handle_interlock_message(message, tokens)
			elif device == self.MESSAGE_DEVICE_STEPRUN:
				return self._handle_steprun_message(message, tokens)
			elif device == self.MESSAGE_DEVICE_FAN:
				return self._handle_fan_message(message, tokens)
			elif device == self.MESSAGE_DEVICE_LASER:
				return self._handle_laser_message(message, tokens)

		return True



	def _handle_invalid_message(self, message):
		self._logger.warn("Received invalid message: '%s'", message)
		return False


	def _handle_onebutton_message(self, message, token):
		action = token[0] if len(token)>0 else None
		payload = self._as_number(token[1]) if len(token)>1 else None
		self._logger.debug("_handle_onebutton_message() message: %s, action: %s, payload: %s", message, action, payload)

		if action == self.MESSAGE_ACTION_ONEBUTTON_PRESSED:
			self._fireEvent(IoBeamEvents.ONEBUTTON_PRESSED)
		elif action == self.MESSAGE_ACTION_ONEBUTTON_DOWN and payload is not None:
			self._fireEvent(IoBeamEvents.ONEBUTTON_DOWN, payload)
		elif action == self.MESSAGE_ACTION_ONEBUTTON_RELEASED and payload is not None:
			self._fireEvent(IoBeamEvents.ONEBUTTON_RELEASED, payload)
		elif action == self.MESSAGE_ERROR:
			raise Exception("iobeam received OneButton error: %s", message)
		else:
			return self._handle_invalid_message(message)
		return True


	def _handle_interlock_message(self, message, tokens):
		lock_num = tokens[0] if len(tokens) > 0 else None
		lock_state = tokens[1] if len(tokens) > 1 else None
		before_state = self.open_interlocks()
		self._logger.debug("_handle_interlock_message() message: %s, lock_num: %s, lock_state: %s, before_state: %s", message, lock_num, lock_state, before_state)

		if lock_num is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_OPEN:
			self._interlocks[lock_num] = True
		elif lock_num is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_CLOSED:
			self._interlocks.pop(lock_num, None)
		elif self.MESSAGE_ERROR in message:
			raise Exception("iobeam received InterLock error: %s", message)
		else:
			return self._handle_invalid_message(message)

		now_state = self.open_interlocks()
		if now_state != before_state:
			if self.is_interlock_closed():
				self._fireEvent(IoBeamEvents.INTERLOCK_CLOSED)
			else:
				self._fireEvent(IoBeamEvents.INTERLOCK_OPEN, now_state)

		return True


	def _handle_lid_message(self, message, tokens):
		return True

	def _handle_steprun_message(self, message, tokens):
		return True

	def _handle_fan_message(self, message, tokens):
		return True

	def _handle_laser_message(self, message, tokens):
		return True


	def _fireEvent(self, event, payload=None):
		self._logger.info("_fireEvent() event:%s, payload:%s", event, payload)
		self._event_bus.fire(event, payload)


	def _as_number(self, str):
		if str is None: return None
		try:
			return float(str)
		except:
			return None


# This guy handles OneButton Events.
# it basically also handles the ReadyToLaser state
class ReadyToLaserStateManager(object):

	PRINTER_STATE_PRINTING = "PRINTING"
	READY_TO_PRINT_MAX_WAITING_TIME = 120
	READY_TO_PRINT_CHECK_INTERVAL = 10

	def __init__(self, event_bus, plugin_manager, file_manager, printer):
		self._event_bus = event_bus
		self._plugin_manager = plugin_manager
		self._file_manager = file_manager
		self._printer = printer
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.readytolaserman")
		self._subscribe()

		self.ready_to_laser_ts = -1
		self.ready_to_laser_file = None
		self.ready_to_laser_timer = None

	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_PRESSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_CLOSED, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.ONEBUTTON_PRESSED:
			if self._printer.get_state_id() == self.PRINTER_STATE_PRINTING:
				self._printer.pause_print()
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
		self._event_bus.fire(MrBeamEvents.READY_TO_LASER_START)
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
			self._event_bus.fire(MrBeamEvents.READY_TO_LASER_CANCELED)

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









