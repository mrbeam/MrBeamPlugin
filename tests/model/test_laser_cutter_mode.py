import pytest

from octoprint_mrbeam import LaserCutterModeModel
from octoprint_mrbeam.enums.laser_cutter_mode import LaserCutterModeEnum


@pytest.fixture
def laser_cutter_mode():
    laser_cutter_mode = LaserCutterModeModel()

    yield laser_cutter_mode


def test_constructor_when_valid_id_then_mode_used():
    laser_cutter_mode = LaserCutterModeModel(LaserCutterModeEnum.ROTARY.value)
    assert laser_cutter_mode.id == LaserCutterModeEnum.ROTARY.value


def test_constructor_when_invalid_id_then_default_mode_used():
    laser_cutter_mode = LaserCutterModeModel("invalid_id")
    assert laser_cutter_mode.id == LaserCutterModeEnum.DEFAULT.value


def test_id_setter_when_valid_id_then_id_is_set(laser_cutter_mode):
    laser_cutter_mode.id = LaserCutterModeEnum.ROTARY.value
    assert laser_cutter_mode.id == LaserCutterModeEnum.ROTARY.value


def test_id_setter_when_invalid_id_then_default_id_is_set(laser_cutter_mode):
    laser_cutter_mode.id = "invalid_id"
    assert laser_cutter_mode.id == LaserCutterModeEnum.DEFAULT.value
