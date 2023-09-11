import __builtin__

import pytest
from mock.mock import MagicMock, patch
from octoprint.events import EventManager

from octoprint_mrbeam.printing.printer import Laser


@pytest.fixture
def laser(mocker):
    def mock_parent_init(self, fileManager, analysisQueue, printerProfileManager):
        self._logger = MagicMock()

        self._analysisQueue = analysisQueue
        self._fileManager = fileManager
        self._printerProfileManager = printerProfileManager

        self._temp = None
        self._bedTemp = None
        self._targetTemp = None
        self._targetBedTemp = None
        self._temps = MagicMock()
        self._tempBacklog = []

        self._messages = MagicMock()
        self._messageBacklog = []

        self._log = MagicMock()
        self._logBacklog = []

        self._state = None

        self._currentZ = None

        self._printAfterSelect = False
        self._posAfterSelect = None

        self._sdPrinting = False
        self._sdStreaming = False
        self._sdFilelistAvailable = MagicMock()
        self._streamingFinishedCallback = None
        self._streamingFailedCallback = None

        self._selectedFileMutex = MagicMock()
        self._selectedFile = None
        self._timeEstimationData = None
        self._timeEstimationStatsWeighingUntil = MagicMock()
        self._timeEstimationValidityRange = MagicMock()
        self._timeEstimationForceDumbFromPercent = MagicMock()
        self._timeEstimationForceDumbAfterMin = MagicMock()

        # comm
        self._comm = MagicMock()

        # callbacks
        self._callbacks = []

        # progress plugins
        self._lastProgressReport = None
        self._progressPlugins = MagicMock()

        self._stateMonitor = MagicMock()

    mocker.patch(
        "octoprint.printer.standard.Printer.__init__",
        side_effect=mock_parent_init,
    )
    mocker.patch(
        "octoprint.printer.standard.Printer._getStateFlags",
        retuirn_value=MagicMock(),
    )
    mocker.patch(
        "octoprint.printer.standard.Printer.get_state_string",
        retuirn_value=MagicMock(),
    )
    event_manager = EventManager()
    printer = Laser(MagicMock(), MagicMock(), MagicMock())
    printer._event_bus = event_manager
    printer.refresh = MagicMock()
    printer.RESET_WAIT_TIME = 0
    __builtin__._mrbeam_plugin_implementation = MagicMock()
    return printer


def test_register_user_notification_system(laser, mrbeam_plugin):
    # Arrange
    mocked_user_notification_system = MagicMock()
    # Act
    laser.register_user_notification_system(mocked_user_notification_system)

    # Assert
    assert laser._user_notification_system == mocked_user_notification_system


def test_fail_print(laser):
    # Arrange
    laser._user_notification_system = MagicMock()
    laser._user_notification_system.get_notification = MagicMock(
        return_value="mocked_notification"
    )

    # Act
    with patch.object(laser, "home") as mocked_home, patch.object(
        laser._comm, "cancelPrint"
    ) as mocked_cancelPrint, patch.object(
        EventManager,
        "fire",
        return_value=MagicMock(),
    ) as mocked_event_fire:

        laser.fail_print("test_fail_print")

        # Assert
        laser._user_notification_system.show_notifications.assert_called_once_with(
            "mocked_notification"
        )
        mocked_home.assert_called_once()
        mocked_cancelPrint.assert_called_once()
        mocked_event_fire.assert_called_once_with(
            "PrintCancelingDone",
        )


def test_fail_print_comm_none(laser):
    # Arrange
    laser._comm = None
    laser._user_notification_system = MagicMock()
    laser._user_notification_system.get_notification = MagicMock(
        return_value="mocked_notification"
    )

    # Act
    laser.fail_print("test_fail_print")

    # Assert
    laser._user_notification_system.show_notifications.assert_not_called()
