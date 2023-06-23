import pytest
from mock.mock import MagicMock, call, patch


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

    def mock_settings_navbar_label(*args, **kwargs):
        if args == (["navbar_label"],):
            return initial_label
        return ""

    mrbeam_plugin._settings.get = MagicMock(side_effect=mock_settings_navbar_label)

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


@pytest.mark.parametrize("key", ["testkey", ("testkey",), ["testkey"]])
def test_setUserSetting_when_text_or_tuple_or_list_then_convert_into_tuple(
    key, mrbeam_plugin
):
    # Arrange
    username = "testuser"
    value = "testvalue"
    expectedkey = "testkey"
    timestamp = 1234567890.123
    mrbeam_plugin._user_manager.change_user_settings = MagicMock()
    # Act
    with patch("time.time", return_value=timestamp):
        mrbeam_plugin.setUserSetting(username, key, value)
    # Assert
    assert mrbeam_plugin._user_manager.change_user_settings.call_args_list == [
        call(
            username,
            {
                (
                    "mrbeam",
                    expectedkey,
                ): value
            },
        ),
        call(username, {("mrbeam", "ts"): timestamp}),
        call(username, {("mrbeam", "version"): "2.0.0dev0"}),
    ]


def test_support_mode_when_enabled_by_settings_then_true(mrbeam_plugin):
    # Arrange
    def mock_settings_support(*args, **kwargs):
        if args[0] == ["dev", "support_mode"]:
            return True
        else:
            return False

    mrbeam_plugin._settings.get = MagicMock(side_effect=mock_settings_support)
    # Act
    result = mrbeam_plugin.support_mode
    # Assert
    assert result is True


def test_support_mode_when_nothing_then_false(mrbeam_plugin):
    # Arrange
    # Act
    result = mrbeam_plugin.support_mode
    # Assert
    assert result is False
