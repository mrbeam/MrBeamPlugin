import pytest
from octoprint_mrbeam.services.laser_cutter_mode import LaserCutterModeService


@pytest.fixture
def laser_cutter_mode_service(mrbeam_plugin):
    laser_cutter_mode_service = LaserCutterModeService(mrbeam_plugin)

    yield laser_cutter_mode_service


def test_get_mode_when_default_settings_then_default_mode(laser_cutter_mode_service):
    mode = laser_cutter_mode_service.get_mode()
    assert mode == {"id": 0, "name": "default"}


def test_get_mode_id_when_default_settings_then_default_mode_id(laser_cutter_mode_service):
    mode_id = laser_cutter_mode_service.get_mode_id()
    assert mode_id == 0


def test_get_mode_name_when_default_settings_then_default_mode_name(laser_cutter_mode_service):
    mode_name = laser_cutter_mode_service.get_mode_name()
    assert mode_name == "default"


def test_change_mode_by_id_when_valid_id_then_change(laser_cutter_mode_service):
    laser_cutter_mode_service.change_mode_by_id(1)
    assert laser_cutter_mode_service.get_mode_id() == 1


def test_change_mode_by_id_when_invalid_id_change_to_default(laser_cutter_mode_service):
    laser_cutter_mode_service.change_mode_by_id(2)
    assert laser_cutter_mode_service.get_mode_id() == 0


def test_change_mode_by_name_when_valid_name_then_change(laser_cutter_mode_service):
    laser_cutter_mode_service.change_mode_by_name("rotary")
    assert laser_cutter_mode_service.get_mode_name() == "rotary"


def test_change_mode_by_name_when_invalid_name_then_change_to_default(laser_cutter_mode_service):
    laser_cutter_mode_service.change_mode_by_name("invalid name")
    assert laser_cutter_mode_service.get_mode_name() == "default"
