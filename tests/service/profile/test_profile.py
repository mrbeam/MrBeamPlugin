import mock
import os
import pytest
import yaml
from mock.mock import MagicMock, patch
import json
from mock import mock_open

from octoprint.settings import settings

from octoprint_mrbeam.constant.profile import laser_cutter as laser_cutter_profiles
from octoprint_mrbeam.service.profile.laser_cutter_profile import laser_cutter_profile_service, \
	LaserCutterProfileService
from octoprint_mrbeam.service.profile.profile import ProfileService


def test_profile_when_class_instantiation_without_method_implementation():
	with pytest.raises(NotImplementedError):
		ProfileService("profile_service_test_id", laser_cutter_profiles.default_profile)

class ProfileServiceImplementation(ProfileService):

	def __init__(self, profile_service_id, current_profile):
		super(ProfileServiceImplementation, self).__init__(profile_service_id, current_profile)

	def _migrate_profile(self, profile):
		return False

	def _ensure_valid_profile(self, profile):
		return profile

@pytest.mark.parametrize("profile, identifier, profile_file_exists, exists",
						 [
							 # Test case 1: Default profile, profile setting exists, profile file exists
							 (laser_cutter_profiles.default_profile, laser_cutter_profiles.default_profile["id"], True,
							  True),
							 # Test case 2: Rotary profile, profile setting exists, profile file exists
							 (laser_cutter_profiles.rotary_profile, laser_cutter_profiles.rotary_profile["id"], True,
							  True),
							 # Test case 3: Series 2C profile, profile setting exists, profile file exists
							 (
									 laser_cutter_profiles.series_2c_profile,
									 laser_cutter_profiles.default_profile["id"], True,
									 True),
							 # Test case 4: Series 2C Rotary profile, profile setting exists, profile file exists
							 (laser_cutter_profiles.series_2c_rotary_profile,
							  laser_cutter_profiles.default_profile["id"], True, True),
							 # Test case 5: Default profile, profile setting does not exist, profile file does not exist
							 (laser_cutter_profiles.default_profile, laser_cutter_profiles.default_profile["id"], False,
							  False),
							 # Test case 6: Rotary profile, profile setting does not exist, profile file does not exist
							 (laser_cutter_profiles.rotary_profile, laser_cutter_profiles.rotary_profile["id"], False,
							  False),
							 # Test case 7: Series 2C profile, profile setting exists, profile file does not exist
							 (laser_cutter_profiles.series_2c_profile, laser_cutter_profiles.series_2c_profile["id"],
							  False, False),
							 # Test case 8: Series 2C Rotary profile, profile setting exists, profile default_profile does not exist
							 (laser_cutter_profiles.series_2c_rotary_profile,
							  laser_cutter_profiles.default_profile["id"], False, False),
						 ],
						 ids=["Test case 1: Default profile, profile setting exists, profile file exists",
							  "Test case 2: Rotary profile, profile setting exists, profile file exists",
							  "Test case 3: Series 2C profile, profile setting exists, profile file exists",
							  "Test case 4: Series 2C Rotary profile, profile setting exists, profile file exists",
							  "Test case 5: Default profile, profile setting does not exist, profile file does not exist",
							  "Test case 6: Rotary profile, profile setting does not exist, profile file does not exist",
							  "Test case 7: Series 2C profile, profile setting exists, profile file does not exist",
							  "Test case 8: Series 2C Rotary profile, profile setting exists, profile file does not exist"
							  ]
						 )
def test_exists_when_profile_is_initiated(profile, identifier, profile_file_exists, exists):
	profile_service_instance = ProfileServiceImplementation("profile_service_test_id", profile)

	with patch("os.path.exists", return_value=profile_file_exists), patch("os.path.isfile",
																		  return_value=profile_file_exists):
		# Assert
		assert profile_service_instance.exists(identifier) == exists

@pytest.mark.parametrize("profile, profile_file_exists, expected_profile",
						 [
							 (laser_cutter_profiles.default_profile, True, laser_cutter_profiles.default_profile),
							 (laser_cutter_profiles.rotary_profile, True, laser_cutter_profiles.rotary_profile),
							 (laser_cutter_profiles.series_2c_profile, True, laser_cutter_profiles.series_2c_profile),
							 (laser_cutter_profiles.series_2c_rotary_profile, True, laser_cutter_profiles.series_2c_rotary_profile),
							 (laser_cutter_profiles.default_profile, False, None),
							 (laser_cutter_profiles.rotary_profile, False, None),
							 (laser_cutter_profiles.series_2c_profile, False, None),
							 (laser_cutter_profiles.series_2c_rotary_profile, False, None),
						 ],
						 ids=[
							 "Test case 1: Default profile, profile file exists",
							 "Test case 2: Rotary profile, profile file exists",
							 "Test case 3: Series 2C profile, profile file exists",
							 "Test case 4: Series 2C Rotary profile, profile file exists",
							 "Test case 5: Default profile, profile file does not exist",
							 "Test case 6: Rotary profile, profile file does not exist",
							 "Test case 7: Series 2C profile, profile file does not exist",
							 "Test case 8: Series 2C Rotary profile, profile file does not exist"]
						 )
def test_get_when_profile_is_initiated(profile, profile_file_exists, expected_profile, mocker):
	profile_service_instance = ProfileServiceImplementation("profile_service_test_id", profile)

	with patch("os.path.exists", return_value=profile_file_exists), patch("os.path.isfile",
	    return_value=profile_file_exists), patch(
		"os.path.exists",
		return_value=profile_file_exists), patch(
		"os.path.isfile", return_value=profile_file_exists), patch("__builtin__.open",
	    mock_open(read_data=json.dumps(profile))), patch(
		"yaml.safe_load", return_value=profile):
			# Assert
			assert profile_service_instance.get(profile["id"]) == expected_profile

@pytest.mark.parametrize("profile, profile_setting, profile_file_exists, expected_profile",
						 [
							 (laser_cutter_profiles.default_profile, laser_cutter_profiles.default_profile["id"], True,
							  laser_cutter_profiles.default_profile),
							 (laser_cutter_profiles.rotary_profile, laser_cutter_profiles.rotary_profile["id"], True,
							  laser_cutter_profiles.rotary_profile),
							 (laser_cutter_profiles.series_2c_profile, laser_cutter_profiles.series_2c_profile["id"],
							  True, laser_cutter_profiles.series_2c_profile),
							 (laser_cutter_profiles.series_2c_rotary_profile,
							  laser_cutter_profiles.series_2c_rotary_profile["id"], True,
							  laser_cutter_profiles.series_2c_rotary_profile),
							 (laser_cutter_profiles.default_profile, None, False,
									 laser_cutter_profiles.default_profile),
							 (laser_cutter_profiles.rotary_profile, None, False, laser_cutter_profiles.rotary_profile),
							 (laser_cutter_profiles.series_2c_profile, laser_cutter_profiles.series_2c_profile["id"],
							  False, laser_cutter_profiles.series_2c_profile),
							 (laser_cutter_profiles.series_2c_rotary_profile,
							  laser_cutter_profiles.series_2c_rotary_profile["id"], False,
							  laser_cutter_profiles.series_2c_rotary_profile),
						 ],
						 ids=["Test case 1: Default profile, profile setting exists, profile file exists",
							  "Test case 2: Rotary profile, profile setting exists, profile file exists",
							  "Test case 3: Series 2C profile, profile setting exists, profile file exists",
							  "Test case 4: Series 2C Rotary profile, profile setting exists, profile file exists",
							  "Test case 5: Default profile, profile setting does not exist, profile file does not exist",
							  "Test case 6: Rotary profile, profile setting does not exist, profile file does not exist",
							  "Test case 7: Series 2C profile, profile setting exists, profile file does not exist",
							  "Test case 8: Series 2C Rotary profile, profile setting exists, profile file does not exist"]
						 )
def test_get_default_when_profile_is_initiated(profile, profile_setting, profile_file_exists, expected_profile):
	profile_service_instance = ProfileServiceImplementation("profile_service_test_id", profile)

	patch.object(settings(), "get", return_value=profile_setting)
	with patch("os.path.exists", return_value=profile_file_exists), patch("os.path.isfile",
																		  return_value=profile_file_exists), patch(
		"os.path.exists",
		return_value=profile_file_exists), patch(
		"os.path.isfile", return_value=profile_file_exists), patch("__builtin__.open",
	    mock_open(read_data=json.dumps(profile))), patch(
		"yaml.safe_load", return_value=profile):
		# Assert
		assert profile_service_instance.get_default() == expected_profile
