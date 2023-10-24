import pytest
from mock.mock import MagicMock

from octoprint_mrbeam.iobeam.hw_malfunction_handler import (
    HwMalfunctionHandler,
    HwMalfunction,
)


@pytest.fixture
def hw_malfunction_handler(mrbeam_plugin):
    # Create an instance of MyClass with a mock user_notification_system
    return HwMalfunctionHandler(mrbeam_plugin)


def test_show_hw_malfunction_notification(hw_malfunction_handler):
    # Arrange
    # Create some mock data for the messages_to_show dictionary
    messages_to_show = {
        "malfunction_id1": HwMalfunction(
            "malfunction_id1",
            "Malfunction 1",
            {},
            priority=1,
            error_code=123,
        ),
    }
    hw_malfunction_handler._messages_to_show = messages_to_show
    hw_malfunction_handler._user_notification_system.show_notifications = MagicMock()
    mock_notification = dict(
        notification_id="notification_id",
        err_msg="err_msg",
        err_code="err_code",
        replay=False,
    )
    hw_malfunction_handler._user_notification_system.get_notification = MagicMock(
        return_value=mock_notification
    )
    expected_notifications = [mock_notification]

    # Act
    hw_malfunction_handler.show_hw_malfunction_notification()

    # Assert
    hw_malfunction_handler._user_notification_system.get_notification.assert_called_with(
        notification_id="err_unknown_malfunction",
        replay=True,
        err_msg=["123"],
    )

    hw_malfunction_handler._plugin.user_notification_system.show_notifications.assert_called_with(
        expected_notifications
    )
    # Assert that the messages_to_show dictionary was updated correctly
    assert "malfunction_id1" not in hw_malfunction_handler._messages_to_show


@pytest.mark.parametrize(
    "malfunction_id, expected_notification_id",
    [
        (
            HwMalfunctionHandler.PCF_ANOMALY,
            HwMalfunctionHandler.HARDWARE_MALFUNCTION_NON_I2C,
        ),
        (
            HwMalfunctionHandler.I2C_DEVICE_MISSING,
            HwMalfunctionHandler.I2C_BUS_MALFUNCTION,
        ),
    ],
)
def test_show_hw_malfunction_notification_known(
    malfunction_id, expected_notification_id, hw_malfunction_handler
):
    # Arrange
    messages_to_show = {
        malfunction_id: HwMalfunction(
            malfunction_id,
            "Malfunction 1",
            {},
            priority=1,
            error_code="123",
        ),
    }
    hw_malfunction_handler._messages_to_show = messages_to_show

    # Act
    hw_malfunction_handler.show_hw_malfunction_notification()

    # Assert
    hw_malfunction_handler._user_notification_system.get_notification.assert_called_with(
        notification_id=expected_notification_id,
        replay=True,
        err_code="123",
    )


@pytest.mark.parametrize(
    "malfunction_id",
    [
        (HwMalfunctionHandler.MALFUNCTION_ID_BOTTOM_OPEN),
        (HwMalfunctionHandler.MALFUNCTION_ID_LASERHEADUNIT_MISSING),
        (HwMalfunctionHandler.HW_MANIPULATION),
        (HwMalfunctionHandler.FAN_NOT_SPINNING),
        (HwMalfunctionHandler.COMPRESSOR_MALFUNCTION),
        (HwMalfunctionHandler.ONEBUTTON_NOT_INITIALIZED),
        (HwMalfunctionHandler.I2C_BUS_MALFUNCTION),
    ],
)
def test_show_hw_malfunction_notification_known_same_id(
    malfunction_id, hw_malfunction_handler
):
    # Arrange
    messages_to_show = {
        malfunction_id: HwMalfunction(
            malfunction_id,
            "Malfunction 1",
            {},
            priority=1,
            error_code="123",
        ),
    }
    hw_malfunction_handler._messages_to_show = messages_to_show

    # Act
    hw_malfunction_handler.show_hw_malfunction_notification()

    # Assert
    hw_malfunction_handler._user_notification_system.get_notification.assert_called_with(
        notification_id=malfunction_id,
        replay=True,
        err_code="123",
    )


@pytest.mark.parametrize(
    "malfunction_id, expected_notification_id",
    [
        (None, "err_unknown_malfunction"),
        ("unknown", "err_unknown_malfunction"),
    ],
)
def test_show_hw_malfunction_notification_unknown(
    malfunction_id, expected_notification_id, hw_malfunction_handler
):
    # Arrange
    messages_to_show = {
        malfunction_id: HwMalfunction(
            malfunction_id,
            "Malfunction 1",
            {},
            priority=1,
            error_code="123",
        ),
    }
    hw_malfunction_handler._messages_to_show = messages_to_show

    # Act
    hw_malfunction_handler.show_hw_malfunction_notification()

    # Assert
    hw_malfunction_handler._user_notification_system.get_notification.assert_called_with(
        notification_id=expected_notification_id,
        replay=True,
        err_msg=["123"],
    )
