from flask import Flask
import pytest as pytest
from mock.mock import MagicMock, patch

from octoprint_mrbeam.util.device_info import (
    MODEL_MRBEAM_2_DC_X,
    MODEL_MRBEAM_2_DC,
    MODEL_MRBEAM_2_DC_S,
    MODEL_MRBEAM_2,
)
from octoprint_mrbeam.util.material_csv_parser import (
    LASER_MODEL_X,
    LASER_MODEL_S,
    DEFAULT_LASER_MODEL,
)


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


@pytest.mark.parametrize(
    "laserhead, devide_model, expected_feedrate, expected_intensity",
    [
        (
            DEFAULT_LASER_MODEL,
            MODEL_MRBEAM_2,
            "F450",
            "S390",
        ),  # cardboard setting mrbeam2
        (
            DEFAULT_LASER_MODEL,
            MODEL_MRBEAM_2_DC,
            "F1500",
            "S1105",
        ),  # cardboard setting DC
        (
            DEFAULT_LASER_MODEL,
            MODEL_MRBEAM_2_DC_S,
            "F1500",
            "S1105",
        ),  # cardboard setting DC
        (
            DEFAULT_LASER_MODEL,
            MODEL_MRBEAM_2_DC_X,
            "F1500",
            "S1105",
        ),  # cardboard setting DC
        (LASER_MODEL_S, MODEL_MRBEAM_2_DC, "F1500", "S910"),  # cardboard setting S
        (LASER_MODEL_S, MODEL_MRBEAM_2_DC_S, "F1500", "S910"),  # cardboard setting S
        (LASER_MODEL_X, MODEL_MRBEAM_2_DC, "F2000", "S650"),  # cardboard setting x
        (LASER_MODEL_X, MODEL_MRBEAM_2_DC_S, "F2000", "S650"),  # cardboard setting x
        (LASER_MODEL_X, MODEL_MRBEAM_2_DC_X, "F2000", "S650"),  # cardboard setting x
    ],
)
def test_generate_backlash_compenation_pattern_gcode(
    laserhead,
    devide_model,
    expected_feedrate,
    expected_intensity,
    mrbeam_plugin,
):
    # Arrange
    mrbeam_plugin.laserhead_handler = MagicMock()
    mrbeam_plugin.mrb_file_manager = MagicMock()
    with patch.object(mrbeam_plugin, "get_model_id", return_value=devide_model):
        with patch.object(
            mrbeam_plugin.laserhead_handler,
            "get_current_used_lh_model_id",
            return_value=laserhead,
        ):
            with patch.object(
                mrbeam_plugin.mrb_file_manager, "add_file_to_design_library"
            ) as add_file_to_design_library:
                app = Flask(__name__)
                with app.test_request_context():
                    # Act
                    mrbeam_plugin.generate_backlash_compenation_pattern_gcode(None)

                    # Assert
                    assert any(
                        call_args
                        for call_args in add_file_to_design_library.call_args_list
                        if expected_feedrate in str(call_args)
                    )
                    assert any(
                        call_args
                        for call_args in add_file_to_design_library.call_args_list
                        if expected_intensity in str(call_args)
                    )
