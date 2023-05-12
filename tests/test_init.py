import pytest
from mock.mock import MagicMock


def test_get_navbar_label_stable_empty(mrbeam_plugin):
    # The default setting (get_settings_defaults) is software_tier=stable
    assert mrbeam_plugin.get_navbar_label() == ""


def test_get_navbar_label_beta_link(mrbeam_plugin, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.is_beta_channel", return_value=True)
    assert (
        mrbeam_plugin.get_navbar_label()
        == '<a href="https://mr-beam.freshdesk.com/support/solutions/articles/43000507827" target="_blank">BETA</a>'
    )


def test_get_navbar_label_alpha(mrbeam_plugin, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.is_alpha_channel", return_value=True)
    assert mrbeam_plugin.get_navbar_label() == "ALPHA"


def test_get_navbar_label_dev(mrbeam_plugin, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.is_develop_channel", return_value=True)
    assert mrbeam_plugin.get_navbar_label() == "DEV"


def test_get_navbar_label_combined(mrbeam_plugin, mocker):
    # Change settings to have an initial value in navbar_label
    initial_label = "abcde"

    mrbeam_plugin._settings.get = MagicMock(return_value=initial_label)

    mocker.patch("octoprint_mrbeam.MrBeamPlugin.is_alpha_channel", return_value=True)
    assert mrbeam_plugin.get_navbar_label() == initial_label + " | ALPHA"


def test_handle_temperature_warning_dismissal_warning(mrbeam_plugin):
    # Arrange
    data = {"level": 1}
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_warning = MagicMock()

    # Act
    mrbeam_plugin.handle_temperature_warning_dismissal(data)

    # Assert
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_warning.assert_called_once_with()


def test_handle_temperature_warning_dismissal_critical(mrbeam_plugin):
    # Arrange
    data = {"level": 2}
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_critical = MagicMock()

    # Act
    mrbeam_plugin.handle_temperature_warning_dismissal(data)

    # Assert
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_critical.assert_called_once_with()


@pytest.mark.parametrize("level", [0, None])
def test_handle_temperature_warning_dismissal_critical(level, mrbeam_plugin):
    # Arrange
    data = {"level": level}
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_critical = MagicMock()
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_warning = MagicMock()

    # Act
    mrbeam_plugin.handle_temperature_warning_dismissal(data)

    # Assert
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_critical.assert_not_called()
    mrbeam_plugin.temperature_manager.dismiss_high_temperature_warning.assert_not_called()
