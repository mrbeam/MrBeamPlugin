import socket
import os
import threading
import time
import logging


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


	def __init__(self, eventBusOct, socket_file=None):
		self._eventBusOct = eventBusOct
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam")
		self._logger.debug("initializing EventManagerMrb")

		self._oneButtonHandler = OneButtonHandler(self._eventBusOct)

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


	def _initWorker(self, socket_file=None):
		self._logger.debug("initializing worker thread")

		# this is needed for unit tests
		if socket_file is not None:
			self.SOCKET_FILE = socket_file

		self._worker = threading.Thread(target=self._work)
		self._worker.daemon = True
		self._worker.start()


	def _work(self):
		self._logger.debug("Worker thread starting, connecting to socket: %s", self.SOCKET_FILE)

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
		before_state = self.is_interlock_closed()
		self._logger.debug("_handle_interlock_message() message: %s, lock_num: %s, lock_state: %s, before_state: %s", message, lock_num, lock_state, before_state)

		if lock_num is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_OPEN:
			self._interlocks[lock_num] = True
		elif lock_num is not None and lock_state == self.MESSAGE_ACTION_INTERLOCK_CLOSED:
			self._interlocks.pop(lock_num, None)
		elif self.MESSAGE_ERROR in message:
			raise Exception("iobeam received InterLock error: %s", message)
		else:
			return self._handle_invalid_message(message)

		now_state = self.is_interlock_closed()
		if now_state != before_state:
			if now_state:
				self._fireEvent(IoBeamEvents.INTERLOCK_CLOSED)
			else:
				self._fireEvent(IoBeamEvents.INTERLOCK_OPEN)

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
		self._eventBusOct.fire(event, payload)


	def _as_number(self, str):
		if str is None: return None
		try:
			return float(str)
		except:
			return None


class OneButtonHandler(object):

	def __init__(self, eventBusOct):
		self._eventBusOct = eventBusOct
		self.pushedTs = -1
		self._subscribe()


	def _subscribe(self):
		self._eventBusOct.subscribe(IoBeamEvents.ONEBUTTON_PRESSED, self.onEvent)
		self._eventBusOct.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
		self._eventBusOct.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.ONEBUTTON_PRESSED:
			self.pushedTs = time.time()
		elif event == IoBeamEvents.ONEBUTTON_RELEASED:
			self.pushedTs = -1
		elif event == IoBeamEvents.DISCONNECT:
			self.pushedTs = -1








