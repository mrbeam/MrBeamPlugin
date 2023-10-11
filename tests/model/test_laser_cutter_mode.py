import pytest

from octoprint_mrbeam import LaserCutterModeModel


@pytest.fixture
def laser_cutter_mode():
    laser_cutter_mode = LaserCutterModeModel()

    yield laser_cutter_mode


def test_constructor_when_valid_id_then_mode_used():
    laser_cutter_mode = LaserCutterModeModel(1)
    assert laser_cutter_mode.id == 1
    assert laser_cutter_mode.name == "rotary"


def test_constructor_when_invalid_id_then_default_mode_used():
    laser_cutter_mode = LaserCutterModeModel(2)
    assert laser_cutter_mode.id == 0
    assert laser_cutter_mode.name == "default"


def test_id_setter_when_valid_id_then_name_also_changed(laser_cutter_mode):
    laser_cutter_mode.id = 1
    assert laser_cutter_mode.id == 1
    assert laser_cutter_mode.name == "rotary"


def test_id_setter_when_invalid_id_then_default_id_and_name(laser_cutter_mode):
    laser_cutter_mode.id = 2
    assert laser_cutter_mode.id == 0
    assert laser_cutter_mode.name == "default"


def test_name_setter_when_valid_name_then_id_also_changed(laser_cutter_mode):
    laser_cutter_mode.name = "rotary"
    assert laser_cutter_mode.id == 1
    assert laser_cutter_mode.name == "rotary"


def test_name_setter_when_invalid_name_then_default_id_and_name(laser_cutter_mode):
    laser_cutter_mode.name = "invalid_mode"
    assert laser_cutter_mode.id == 0
    assert laser_cutter_mode.name == "default"


def test_get_mode_key_when_invalid_mo():
    laser_cutter_mode = LaserCutterModeModel()

    mode_key = laser_cutter_mode._get_mode_key("rotary")
    assert mode_key == 1

    mode_key = laser_cutter_mode._get_mode_key("invalid_mode")  # Invalid mode name
    assert mode_key == 0  # Should fall back to default id
