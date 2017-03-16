import socket
import os
import threading
import time
import logging


# class SocketServerThread(threading.Thread):
#
# 	SOCKET_FILE = "/tmp/mrbeamEventSocket"
#
# 	def __init__(self):
# 		super(SocketClientThread, self).__init__()
# 		self.alive = threading.Event()
# 		self.alive.set()
#
# 		self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
#
# 	def run(self):
# 		try:
# 			os.remove(self.SOCKET_FILE)
# 		except OSError:
# 			pass
# 		self.socket.bind(self.SOCKET_FILE)
#
# 		while self.alive.isSet():
# 			self.socket.listen(0)
# 			conn, addr = self.socket.accept()
#
# 			while self.alive.isSet():
# 				data = conn.recv(1024)
# 				if not data: break
# 				print(repr(data))
#
# 			conn.close()
#
# 	def join(self, timeout=None):
# 		self.alive.clear()
# 		threading.Thread.join(self, timeout)

# singleton
_instance = None

def eventManagerMrb(mrbeamPlugin):
	global _instance
	if _instance is None:
		_instance = EventManagerMrb(mrbeamPlugin)
	return _instance


class EventManagerMrb(object):

	SOCKET_FILE = "/tmp/mrbeamEventSocket"
	SOCKET_COMAMND_LENGTH_MAX = 1024
	SOCKET_COMAMND_NEWLINE= "\n"

	EVENT_BUTTON_PUSHED = "mrbeam.ButtonPushed"
	EVENT_BUTTON_RELEASED = "mrbeam.ButtonReleased"


	def __init__(self, mrbeamPlugin):
		self._mrbeamPlugin = mrbeamPlugin
		self._eventBusOct = self._mrbeamPlugin._event_bus
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.events")
		self._logger.debug("initializing EventManagerMrb")

		self._shutdown_signaled = False

		self._subscribeEvents()
		self._initWorker()


	def _initWorker(self):
		self._logger.debug("initializing worker thread")
		self._worker = threading.Thread(target=self._work)
		self._worker.daemon = True
		self._worker.start()


	def _subscribeEvents(self):
		self._eventBusOct.subscribe(self.EVENT_BUTTON_PUSHED, self._onEvent)
		self._eventBusOct.subscribe(self.EVENT_BUTTON_RELEASED, self._onEvent)


	def _onEvent(self, event, payload):
		self._logger.info("_onEvent() event:%s, payload:%s", event, payload)
		self._logger.info("_onEvent() going to sleeeeeep")
		time.sleep(5)
		self._logger.info("_onEvent() aaaaand wakeup!")


	def _work(self):
		self._logger.debug("Worker thread starting...")

		while not self._shutdown_signaled:
			mySocket = None
			try:
				mySocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				mySocket.settimeout(5)
				self._logger.debug("Connecting to socket...")
				mySocket.connect(self.SOCKET_FILE)
				self._logger.debug("Socket connected")
			except socket.error as e:
				self._logger.warn("EventManagerMrb no able to connect to socket %s, reason: %s. Trying again...", self.SOCKET_FILE, e)
				time.sleep(2)
				continue

			while not self._shutdown_signaled:
				try:
					data = mySocket.recv(self.SOCKET_COMAMND_LENGTH_MAX)
				except Exception as e:
					self._logger.warn("Exception while sockect.recv(): %s - Resetting connection...", e)
					break

				valid = self._handleData(data)
				if not valid:
					self._logger.warn("Received invalid data from socket. Resetting connection...")
					break

			if mySocket is not None:
				self._logger.debug("Closing socket...")
				mySocket.close()
			time.sleep(2)


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
				self._fireEvent(self.EVENT_BUTTON_RELEASED, duration)
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
