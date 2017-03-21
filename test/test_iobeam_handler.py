import unittest
import mock
import logging
import socket
import os
import sys
import threading
import time
from octoprint_mrbeam.iobeam_handler import ioBeamHandler, IoBeamEvents


# hint: to get the output with timestamps:
# > nosetests --with-doctest --logging-format="%(asctime)s %(name)s: %(levelname)s: %(message)s" --debug=octoprint.plugins.mrbeam,test.mrbeam.serverthread

class IoBeamHandlerTestCase(unittest.TestCase):

	def setUp(self):
		self._logger = logging.getLogger("test." + self.__module__ + "." + self.__class__.__name__)
		self._logger.debug("setUp() START")

		self.testThreadServer = ServerThread()
		self.testThreadServer.start()
		time.sleep(.01)

		self.mock = mock.MagicMock(name="EventManagerOctMock")
		self.eventBusMrb = ioBeamHandler(self.mock)
		time.sleep(.01)

		self.mock.reset_mock()
		self._logger.debug("setUp() DONE --------------------")

	def tearDown(self):
		self._logger.debug("tearDown() START ----------------")
		self.eventBusMrb.shutdown()
		self.testThreadServer.join()
		time.sleep(.01)
		self._logger.debug("tearDown() DONE")


	def test_recv_RL(self):
		self.testThreadServer.sendCommand("RL42")
		time.sleep(.01)

		self.mock.fire.assert_called_once_with(IoBeamEvents.ONEBUTTON_RELEASED, 42)

	def test_reconnect_on_error(self):
		self.testThreadServer.sendCommand("some BS")
		time.sleep(1.01) # eventBusMrb sleeps for 1 sec after closing connection to avoid busy loops

		expected = [mock.call.fire(IoBeamEvents.DISCONNECT, None),
					mock.call.fire(IoBeamEvents.CONNECT, None)]
		assert (self.mock.mock_calls == expected), \
			("Events fired by IoBeamHandler. Expected calls: %s\nActual calls: %s" % (expected, self.mock.mock_calls))


class ServerThread(threading.Thread):
	SOCKET_FILE = "/tmp/mrbeamEventSocket"
	SOCKET_NEWLINE = "\n"

	def __init__(self):
		super(ServerThread, self).__init__()
		self.daemon = True
		self.alive = threading.Event()
		self.alive.set()
		self.conn = None

		self._logger = logging.getLogger("test." + self.__module__ + "." + self.__class__.__name__)
		self._logger.info( self.__class__.__name__ + " initialized")

	def run(self):
		self._logger.info("Worker thread started.")
		try:
			os.remove(self.SOCKET_FILE)
		except OSError:
			pass

		self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.socket.bind(self.SOCKET_FILE)

		while self.alive.isSet():
			self._logger.info("Listening for incoming connections on " + self.SOCKET_FILE)
			self.socket.setblocking(1)
			self.socket.settimeout(3)
			self.socket.listen(0)
			self.conn, addr = self.socket.accept()
			self._logger.info("Client connected.")

			while self.alive.isSet():
				self.socket.settimeout(3)
				try:
					data = self.conn.recv(1024)
					if not data: break
				except Exception as e:
					if str(e) == "[Errno 35] Resource temporarily unavailable":
						pass
						# self._logger.warn(str(e))
					else:
						self._logger.warn("Exception while waiting: %s - %s", str(e))
						break

			self._logger.info ("  Disconnecting client...")
			self.conn.close()
			self.conn = None

		self._logger.info("Worker thread stopped.")

	def sendCommand(self, command):
		self._send(command)

	def _send(self, payload):
		if self.conn is not None:
			self._logger.info("  --> " + payload)
			self.conn.send(payload + self.SOCKET_NEWLINE)
		else:
			raise Exception("No Connection, not able to write on socket")

	def join(self, timeout=None):
		self.alive.clear()
		threading.Thread.join(self, timeout)
