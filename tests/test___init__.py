import pytest
from mock.mock import patch, MagicMock

from octoprint_mrbeam.enums.laser_cutter_mode import LaserCutterModeEnum
from octoprint_mrbeam.enums.device_series import DeviceSeriesEnum
from octoprint_mrbeam.constant.profile import laser_cutter as laser_cutter_profiles

def test_update_laser_cutter_profile_when_profile_and_id_are_valid(mrbeam_plugin):
    # Arrange
    sample_profile = {'id': "default_profile", 'name': 'Default Profile'}

    # Act
    mrbeam_plugin.update_laser_cutter_profile(sample_profile)

    # Assert that the save method was called with the correct arguments
    mrbeam_plugin.laser_cutter_profile_service.save.assert_called_once_with(
        sample_profile, allow_overwrite=True, make_default=True
    )

    # Assert that the select method was called with the correct argument
    mrbeam_plugin.laser_cutter_profile_service.select.assert_called_once_with(sample_profile['id'])

def test_update_laser_cutter_profile_when_profile_is_invalid(mrbeam_plugin):
    # Arrange
    sample_profile = "not_a_dict"

    # Act and Assert
    with pytest.raises(TypeError):
            mrbeam_plugin.update_laser_cutter_profile(sample_profile)

    # Act and Assert
    with pytest.raises(TypeError):
            mrbeam_plugin.update_laser_cutter_profile()

def test_update_laser_cutter_profile_when_id_is_invalid(mrbeam_plugin):
    # Arrange
    sample_profile_1 = {'id': 1, 'name': 'Default Profile'}
    sample_profile_2 = {'name': 'Default Profile'}

    # Act and Assert
    with pytest.raises(ValueError):
            mrbeam_plugin.update_laser_cutter_profile(sample_profile_1)

    # Act and Assert
    with pytest.raises(ValueError):
            mrbeam_plugin.update_laser_cutter_profile(sample_profile_2)

@pytest.mark.parametrize("laser_cutter_mode, device_series, expected_profile", [
    # Test case 1: Default mode, Series non-C
    (LaserCutterModeEnum.DEFAULT.value, None, laser_cutter_profiles.default_profile),
    # Test case 2: Default mode, Series C
    (LaserCutterModeEnum.DEFAULT.value, DeviceSeriesEnum.C.value , laser_cutter_profiles.series_2c_profile),
    # Test case 3: Rotary mode, Series non-C
    (LaserCutterModeEnum.ROTARY.value, None, laser_cutter_profiles.rotary_profile),
    # Test case 4: Rotary mode, Series C
    (LaserCutterModeEnum.ROTARY.value, DeviceSeriesEnum.C.value, laser_cutter_profiles.series_2c_rotary_profile),
    # Test case 5: No mode, No series
    (None, None, laser_cutter_profiles.default_profile),
],)
def test_get_laser_cutter_profile_for_current_configuration(laser_cutter_mode, device_series, expected_profile, mocker, mrbeam_plugin):
    # Arrange
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_series",
        return_value=device_series,
    ):
        mocker.patch("octoprint_mrbeam.MrBeamPlugin.get_laser_cutter_mode", return_value=laser_cutter_mode)

        # Act
        result_profile = mrbeam_plugin.get_laser_cutter_profile_for_current_configuration()

        # Assert
        assert result_profile == expected_profile
