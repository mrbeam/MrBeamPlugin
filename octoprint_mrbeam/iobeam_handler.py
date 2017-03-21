import socket
import os
import threading
import time
import logging


# singleton
_instance = None

def ioBeamHandler(mrbeamPlugin):
	global _instance
	if _instance is None:
		_instance = IoBeamHandler(mrbeamPlugin)
	return _instance


class IoBeamEvents(object):
	CONNECT = "iobeam.connect"
	DISCONNECT = "iobeam.disconnect"
	ONEBUTTON_PUSHED = "iobeam.onebutton.pushed"
	ONEBUTTON_RELEASED = "iobeam.onebutton.released"


class IoBeamHandler(object):

	SOCKET_FILE = "/tmp/mrbeamEventSocket"
	SOCKET_COMAMND_LENGTH_MAX = 1024
	SOCKET_COMAMND_NEWLINE= "\n"


	def __init__(self, eventBusOct):
		self._eventBusOct = eventBusOct
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam")
		self._logger.debug("initializing EventManagerMrb")

		self._shutdown_signaled = False
		self._isConnected = False

		self._subscribeEvents()
		self._initWorker()

	def isRunning(self):
		return self._worker.is_alive()

	def isConnected(self):
		return self._isConnected

	def shutdown(self):
		global _instance
		_instance = None
		self._logger.debug("shutdown()")
		self._shutdown_signaled = True

	def _initWorker(self):
		self._logger.debug("initializing worker thread")
		self._worker = threading.Thread(target=self._work)
		self._worker.daemon = True
		self._worker.start()


	def _subscribeEvents(self):
		self._eventBusOct.subscribe(IoBeamEvents.ONEBUTTON_PUSHED, self._onEvent)
		self._eventBusOct.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self._onEvent)


	def _onEvent(self, event, payload):
		self._logger.info("_onEvent() event:%s, payload:%s", event, payload)
		self._logger.info("_onEvent() going to sleeeeeep")
		time.sleep(1)
		self._logger.info("_onEvent() aaaaand wakeup!")


	def _work(self):
		self._logger.debug("Worker thread starting...")

		while not self._shutdown_signaled:
			mySocket = None
			try:
				mySocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				mySocket.settimeout(3)
				self._logger.debug("Connecting to socket...")
				mySocket.connect(self.SOCKET_FILE)
			except socket.error as e:
				self._isConnected = False
				self._logger.warn("EventManagerMrb no able to connect to socket %s, reason: %s. Trying again...", self.SOCKET_FILE, e)
				time.sleep(1)
				continue

			self._isConnected = True
			self._logger.debug("Socket connected")
			self._fireEvent(IoBeamEvents.CONNECT)

			while not self._shutdown_signaled:
				try:
					data = mySocket.recv(self.SOCKET_COMAMND_LENGTH_MAX)
				except Exception as e:
					self._logger.warn("Exception while sockect.recv(): %s - Resetting connection...", e)
					break

				if not data:
					self._logger.warn("Connection ended from other side. Closing connection...")
					break

				# here we see what's in the data...
				valid = self._handleData(data)
				if not valid:
					self._logger.warn("Received invalid data from socket. Resetting connection...")
					break

			if mySocket is not None:
				self._logger.debug("Closing socket...")
				# mySocket.shutdown(SHUT_RDWR)
				mySocket.close()

			self._isConnected = False
			self._fireEvent(IoBeamEvents.DISCONNECT)

			if not self._shutdown_signaled:
				self._logger.debug("Sleeping for a sec before reconnecting...")
				time.sleep(1)

		self._logger.debug("Worker thread stopped.")

	# handles incoming data from the socket.
	# @return bool False if data is (partially) invalid and connection needs to be reset, true otherwise
	def _handleData(self, data):
		if not data: return False

		chunks = data.split(self.SOCKET_COMAMND_NEWLINE)
		if len(chunks) <= 0: return False

		for value in chunks:
			if not value:
				continue
			elif value[:2] == "UP":
				self._logger.debug("_handleData: UP (value:%s)", value)
				continue
			elif value[:2] == "PR":
				self._logger.debug("_handleData: PR (value:%s)", value)
				continue
			elif value[:2] == "DN":
				self._logger.debug("_handleData: DN (value:%s)", value)
				continue
			elif value[:2] == "RL":
				duration = -1
				try:
					duration = int(value[2:])
				except:
					self._logger.warn("Invalid value of 'RL' received from socket: %s; resetting connection...", value)
					return False
				self._logger.debug("_handleData: RL duration: %s (value:%s)", duration, value)
				self._fireEvent(IoBeamEvents.ONEBUTTON_RELEASED, duration)
				continue
			else:
				self._logger.warn("Unknown command received from socket: '%s' resetting connection...", value)
				return False


			# intValue = -1
			# try:
			# 	intValue = int(value)
			# except:
			# 	return False
            #
			# if intValue == 5:
			# 	self._fireEvent(self.EVENT_BUTTON_PUSHED)

		return True


	def _fireEvent(self, event, payload=None):
		self._logger.info("_fireEvent() event:%s, payload:%s", event, payload)
		self._eventBusOct.fire(event, payload)


class OneButtonHandler(object):


	def __init__(self, eventBusOct):
		self._eventBusOct = eventBusOct

		self.pushedTs = -1

		self._subscribe()


	def _subscribe(self):
		self._eventBusOct.subscribe(IoBeamEvents.ONEBUTTON_PUSHED, self.onEvent)
		self._eventBusOct.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
		self._eventBusOct.subscribe(IoBeamEvents.DISCONNECT, self.onEvent)

	def onEvent(self, event, payload):
		if event == IoBeamEvents.ONEBUTTON_PUSHED:
			self.pushedTs = time.time()
		elif event == IoBeamEvents.ONEBUTTON_RELEASED:
			self.pushedTs = -1
		elif event == IoBeamEvents.DISCONNECT:
			self.pushedTs = -1








