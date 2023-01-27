import pytest
from mock.mock import patch, MagicMock

from octoprint_mrbeam.printing.comm_acc2 import MachineCom


@pytest.mark.parametrize(
    "intensity_input,expected",
    [
        (700, 700),
        (1300, 1300),
        (1400, 1300),
    ],
    ids=[
        "normal value",
        "max value",
        "over limit value",
    ],
)
def test_send_command_correct_limit_intensity_input(
    intensity_input, expected, mrbeam_plugin
):
    """
    The intensity input value should be limited to 1300 [profile.laser.intensity_limit]
    """
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1400,
            current_laserhead_max_correction_factor=1,
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()

            # Act
            machineCom._sendCommand("G1 X1 F5000 S{}".format(intensity_input))

            # Assert
            machineCom._serial.write.assert_called_with(
                "G1 X1 F5000 S{}".format(expected)
            )


def test_send_command_limit_correction_factor(mrbeam_plugin):
    # Arrange
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1500,
            current_laserhead_max_correction_factor=1.15,  # limit of the correction factor
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()
            machineCom._current_lh_data = {
                "correction_factor": 2
            }  # current correction factor

            # Act
            machineCom._sendCommand("G1 X1 F5000 S1300")

            # Assert
            machineCom._serial.write.assert_called_with("G1 X1 F5000 S1495")


def test_send_command_correct_intensity_under_max_intenstity(mrbeam_plugin):
    # Arrange
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1500,
            current_laserhead_max_correction_factor=2,  # use very high correction factor to go over max intensity
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()
            machineCom._current_lh_data = {"correction_factor": 1.5}

            # Act
            machineCom._sendCommand("G1 X1 F5000 S1300")

            # Assert
            machineCom._serial.write.assert_called_with("G1 X1 F5000 S1500")


def test_send_command_correct_intensity_correction_under_1(mrbeam_plugin):
    # Arrange
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1500,
            current_laserhead_max_correction_factor=1.15,  # use very high correction factor to go over max intensity
            get_correction_settings=MagicMock(
                return_value={
                    "correction_enabled": True,
                    "correction_factor_override": None,
                }
            ),
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()
            machineCom._current_lh_data = {
                "correction_factor": 0.1
            }  # use a value lower as min limit of 1

            # Act
            machineCom._sendCommand("G1 X1 F5000 S1300")

            # Assert
            machineCom._serial.write.assert_called_with("G1 X1 F5000 S1300")


def test_send_command_correction_factor_override(mrbeam_plugin):
    # Arrange
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1800,
            current_laserhead_max_correction_factor=1.4,  # use very high correction factor to go over max intensity
            get_correction_settings=MagicMock(
                return_value={
                    "correction_enabled": True,
                    "correction_factor_override": 1.3,  # override the correction factor
                }
            ),
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()
            machineCom._current_lh_data = {
                "correction_factor": 1.4
            }  # this value should be ignored and the correction_factor_override used instead

            # Act
            machineCom._sendCommand("G1 X1 F5000 S1300")

            # Assert
            machineCom._serial.write.assert_called_with("G1 X1 F5000 S1690")


def test_send_command_correction_disabled_factor_override(mrbeam_plugin):
    # Arrange
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1800,
            current_laserhead_max_correction_factor=1.4,  # use very high correction factor to go over max intensity
            get_correction_settings=MagicMock(
                return_value={
                    "correction_enabled": False,  # correction disabled
                    "correction_factor_override": 1.3,  # this factor should not be used as it is disabled
                }
            ),
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()

            # Act
            machineCom._sendCommand("G1 X1 F5000 S1300")

            # Assert
            machineCom._serial.write.assert_called_with("G1 X1 F5000 S1300")


def test_send_command_correction_disabled_factor_override(mrbeam_plugin):
    # Arrange
    with patch(
        "__builtin__._mrbeam_plugin_implementation", return_value=mrbeam_plugin
    ) as mrbeam_plugin_mock:
        mrbeam_plugin_mock.laserhead_handler = MagicMock(
            current_laserhead_max_intensity_including_correction=1800,
            current_laserhead_max_correction_factor=1.4,  # use very high correction factor to go over max intensity
            get_correction_settings=MagicMock(
                return_value={
                    "correction_enabled": False,  # correction disabled
                    "correction_factor_override": None,  # Don't override
                }
            ),
        )
        with patch("octoprint.plugin.plugin_manager", return_value=MagicMock()):
            machineCom = MachineCom()
            machineCom._serial = MagicMock()
            machineCom._current_lh_data = {
                "correction_factor": 1.4
            }  # this factor should not be used as it is disabled

            # Act
            machineCom._sendCommand("G1 X1 F5000 S1300")

            # Assert
            machineCom._serial.write.assert_called_with("G1 X1 F5000 S1300")
