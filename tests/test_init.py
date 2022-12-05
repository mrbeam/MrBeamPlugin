from tests.data.data import CONVERT_COMMAND, CONVERT_RESPONSE, CONVERT_TEST_QS, CONVERT_TEST_GCODE_AND_QS
from mock import patch


def test_get_navbar_label_stable_empty(mrbeam_plugin):
    # The default setting (get_settings_defaults) is software_tier=stable
    assert mrbeam_plugin.get_navbar_label() == ""


def test_get_navbar_label_beta_link(mrbeam_plugin, mocker):
    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_beta_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == \
           '<a href="https://mr-beam.freshdesk.com/support/solutions/articles/43000507827" target="_blank">BETA</a>'


def test_get_navbar_label_alpha(mrbeam_plugin, mocker):
    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_alpha_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == "ALPHA"


def test_get_navbar_label_dev(mrbeam_plugin, mocker):
    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_develop_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == "DEV"


def test_get_navbar_label_combined(mrbeam_plugin, mocker):
    # Change settings to have an initial value in navbar_label
    initial_label = "abcde"
    mrbeam_plugin._settings.set(["navbar_label"], initial_label, force=True)

    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_alpha_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == initial_label + " | ALPHA"


def test_gcode_convert_command_slicing_gcode_plus_svg(mocker, mrbeam_plugin, request_context, dummy_file_manager):
    mocker.patch(
        "octoprint_mrbeam.get_json_command_from_request",
        return_value=(CONVERT_COMMAND, CONVERT_TEST_GCODE_AND_QS["CONVERT_DATA"], CONVERT_RESPONSE)
    )

    with request_context():
        with patch.object(dummy_file_manager, 'slice') as mocked_slice:
            mrbeam_plugin.gcodeConvertCommand()

        args, kwargs = mocked_slice.call_args
        assert args == CONVERT_TEST_GCODE_AND_QS["SLICE_ARGS"]
        assert kwargs == CONVERT_TEST_GCODE_AND_QS["SLICE_KWARGS"]

        # The forth parameter of "callback_args" is "appendGcodeFiles", where the gcode data is
        assert len(kwargs["callback_args"][3]) != 0


def test_gcode_convert_command_slicing_no_gcode(mocker, mrbeam_plugin, request_context, dummy_file_manager):
    mocker.patch(
        "octoprint_mrbeam.get_json_command_from_request",
        return_value=(CONVERT_COMMAND, CONVERT_TEST_QS["CONVERT_DATA"], CONVERT_RESPONSE)
    )

    with request_context():
        with patch.object(dummy_file_manager, 'slice') as mocked_slice:
            mrbeam_plugin.gcodeConvertCommand()

        args, kwargs = mocked_slice.call_args
        assert args == CONVERT_TEST_QS["SLICE_ARGS"]
        assert kwargs == CONVERT_TEST_QS["SLICE_KWARGS"]

        # The forth parameter of "callback_args" is "appendGcodeFiles", 0 in this case
        assert len(kwargs["callback_args"][3]) == 0
