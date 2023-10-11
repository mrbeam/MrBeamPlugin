import pytest

from octoprint_mrbeam.enums.laser_cutter_mode import LaserCutterModeEnum
from octoprint_mrbeam.services.laser_cutter_mode import LaserCutterModeService


@pytest.fixture
def laser_cutter_mode_service(mrbeam_plugin):
    laser_cutter_mode_service = LaserCutterModeService(mrbeam_plugin)

    yield laser_cutter_mode_service


def test_get_mode_id_when_default_settings_then_default_mode_id(laser_cutter_mode_service):
    mode_id = laser_cutter_mode_service.get_mode_id()
    assert mode_id == LaserCutterModeEnum.DEFAULT.value


def test_change_mode_by_id_when_valid_id_then_change(laser_cutter_mode_service):
    laser_cutter_mode_service.change_mode_by_id(LaserCutterModeEnum.ROTARY.value)
    assert laser_cutter_mode_service.get_mode_id() == LaserCutterModeEnum.ROTARY.value


def test_change_mode_by_id_when_invalid_id_change_to_default(laser_cutter_mode_service):
    laser_cutter_mode_service.change_mode_by_id("invalid id")
    assert laser_cutter_mode_service.get_mode_id() == LaserCutterModeEnum.DEFAULT.value
