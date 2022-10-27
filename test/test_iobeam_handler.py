import logging
import os
import socket
import threading
import time
import unittest

import ddt
import mock

from octoprint_mrbeam.iobeam.iobeam_handler import ioBeamHandler, IoBeamEvents
from octoprint_mrbeam.iobeam.onebutton_handler import OneButtonHandler
from octoprint_mrbeam.iobeam.interlock_handler import InterLockHandler
from octoprint_mrbeam.mrbeam_events import MrBeamEvents


# hint: to get the output with timestamps:
# > nosetests --with-doctest --logging-format="%(asctime)s %(name)s: %(levelname)s: %(message)s" --debug=octoprint.plugins.mrbeam,test.mrbeam.serverthread


@ddt.ddt
class IoBeamHandlerTestCase(unittest.TestCase):

    SOCKET_FILE = "/tmp/mrbeam_iobeam.sock"

    def setUp(self):
        self._logger = logging.getLogger(
            "test." + self.__module__ + "." + self.__class__.__name__
        )
        self._logger.debug("setUp() START")

        # init test thread; socket server, actually a mock for the real ioBeam
        self.testThreadServer = ServerThread(self.SOCKET_FILE)
        self.testThreadServer.start()
        time.sleep(0.01)

        # init ioBeamHandler
        self.event_bus_mock = mock.MagicMock(name="event_bus_mock")
        self.ioBeamHandler = ioBeamHandler(self.event_bus_mock, self.SOCKET_FILE)
        time.sleep(0.01)

        # init OneButtonHandler
        self._plugin_manager_mock = mock.MagicMock(name="_plugin_manager_mock")
        self._file_manager_mock = mock.MagicMock(name="_file_manager_mock")
        self._file_manager_mock.path_on_disk.return_value("someFileName")
        self._settings_mock = mock.MagicMock(name="_settings_mock")
        self._settings_mock.global_get.return_value(None)
        self._printer_mock = mock.MagicMock(name="_printer_mock")
        self._oneButtonHandler = OneButtonHandler(
            self.ioBeamHandler,
            self.event_bus_mock,
            self._plugin_manager_mock,
            self._file_manager_mock,
            self._settings_mock,
            self._printer_mock,
        )

        self.event_bus_mock.reset_mock()
        self._logger.debug("setUp() DONE --------------------")

    def tearDown(self):
        self._logger.debug("tearDown() START ----------------")
        self.ioBeamHandler.shutdown()
        self.testThreadServer.join()
        time.sleep(0.01)
        self._logger.debug("tearDown() DONE")

    @ddt.data(
        # ( [list of mesages to send], [ list of tuples (event, payload)] )
        (["onebtn:pr"], [(IoBeamEvents.ONEBUTTON_PRESSED, None)]),
        (["onebtn:dn:0.8"], [(IoBeamEvents.ONEBUTTON_DOWN, 0.8)]),
        (["onebtn:rl:1.2"], [(IoBeamEvents.ONEBUTTON_RELEASED, 1.2)]),
        (
            ["onebtn:pr", "onebtn:dn:0.2", "onebtn:dn:0.5", "onebtn:rl:1.0"],
            [
                (IoBeamEvents.ONEBUTTON_PRESSED, None),
                (IoBeamEvents.ONEBUTTON_DOWN, 0.2),
                (IoBeamEvents.ONEBUTTON_DOWN, 0.5),
                (IoBeamEvents.ONEBUTTON_RELEASED, 1.0),
            ],
        ),
        # (["onebtn:pr", "onebtn:dn:0.2", "onebtn:dn:1.2", "onebtn:dn:4.7", "onebtn:rl:5.3"],
        #  [(IoBeamEvents.ONEBUTTON_PRESSED, None),
        #   (IoBeamEvents.ONEBUTTON_DOWN, 0.2),
        #   (IoBeamEvents.ONEBUTTON_DOWN, 1.2),
        #   (MrBeamEvents.SHUTDOWN_PREPARE_START, None),
        #   (IoBeamEvents.ONEBUTTON_DOWN, 4.7),
        #   (IoBeamEvents.ONEBUTTON_RELEASED, 5.3),
        #   (MrBeamEvents.SHUTDOWN_PREPARE_SUCCESS, None)
        #   ]),
    )
    @ddt.unpack
    def test_onebutton(self, messages, expectations):
        self._logger.debug(
            "test_onebutton() messages: %s, expectations: %s", messages, expectations
        )
        self._send_messages_and_evaluate(messages, expectations)

    @ddt.data(
        # ( [list of mesages to send], [ list of tuples (event, payload)] )
        (["intlk:op:0"], [(IoBeamEvents.INTERLOCK_OPEN, ["0"])], False),
        (["intlk:cl:2"], [], True),
        (
            ["intlk:op:0", "intlk:cl:2", "intlk:cl:1"],
            [(IoBeamEvents.INTERLOCK_OPEN, ["0"])],
            False,
        ),
        (
            ["intlk:op:0", "intlk:cl:2", "intlk:cl:0"],
            [
                (IoBeamEvents.INTERLOCK_OPEN, ["0"]),
                (IoBeamEvents.INTERLOCK_CLOSED, None),
            ],
            True,
        ),
    )
    @ddt.unpack
    def test_interlocks(self, messages, expectations, expectation_closed_in_the_end):
        self._logger.debug(
            "test_interlocks() messages: %s, expectations: %s, expectation_closed_in_the_end: %s",
            messages,
            expectations,
            expectation_closed_in_the_end,
        )
        self._send_messages_and_evaluate(messages, expectations)
        self.assertEqual(
            self.ioBeamHandler.is_interlock_closed(),
            expectation_closed_in_the_end,
            "is_interlock_closed() did not return %s in the end as expected."
            % expectation_closed_in_the_end,
        )

    def test_reconnect_on_error(self):
        for i in range(0, 3):
            self.testThreadServer.sendCommand("some BS %s" % i)
            time.sleep(0.01)
        time.sleep(
            1.1
        )  # eventBusMrb sleeps for 1 sec after closing connection to avoid busy loops

        expected = [
            mock.call.fire(IoBeamEvents.DISCONNECT, None),
            mock.call.fire(IoBeamEvents.CONNECT, None),
        ]
        assert self.event_bus_mock.mock_calls == expected, (
            "Events fired by IoBeamHandler.\n"
            "Expected calls: %s\n"
            "Actual calls:   %s" % (expected, self.event_bus_mock.mock_calls)
        )

    def _send_messages_and_evaluate(self, messages, expectations):
        for msg in messages:
            self.testThreadServer.sendCommand(msg)
            time.sleep(0.01)

        expected = []
        for exp in expectations:
            expected.append(mock.call.fire(exp[0], exp[1]))
        assert self.event_bus_mock.mock_calls == expected, (
            "Events fired by IoBeamHandler.\n"
            "Expected calls: %s\n"
            "Actual calls:   %s" % (expected, self.event_bus_mock.mock_calls)
        )


class ServerThread(threading.Thread):
    SOCKET_NEWLINE = "\n"

    def __init__(self, socket_file):
        super(ServerThread, self).__init__()
        self.daemon = True
        self.alive = threading.Event()
        self.alive.set()
        self.conn = None

        self._socket_file = socket_file

        self._logger = logging.getLogger(
            "test." + self.__module__ + "." + self.__class__.__name__
        )
        self._logger.info(self.__class__.__name__ + " initialized")

    def run(self):
        self._logger.info("Worker thread started.")
        try:
            os.remove(self._socket_file)
        except OSError:
            pass

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self._socket_file)

        while self.alive.is_set():
            self._logger.info(
                "Listening for incoming connections on " + self._socket_file
            )
            self.socket.setblocking(1)
            self.socket.settimeout(3)
            self.socket.listen(0)
            self.conn, addr = self.socket.accept()
            self._logger.info("Client connected.")

            while self.alive.is_set():
                self.socket.settimeout(3)
                try:
                    data = self.conn.recv(1024)
                    if not data:
                        break
                except Exception as e:
                    if str(e) == "[Errno 35] Resource temporarily unavailable":
                        pass
                        # self._logger.warn(str(e))
                    else:
                        self._logger.warn("Exception while waiting: %s - %s", str(e))
                        break

            self._logger.info("  Disconnecting client...")
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
