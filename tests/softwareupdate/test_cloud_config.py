# coding=utf-8
from __future__ import absolute_import, division, print_function

import base64
import json
import os
import unittest
from os.path import dirname, realpath

import requests
import requests_mock
from copy import deepcopy
from mock import mock_open
from mock import patch
from octoprint.events import EventManager
from packaging import version
import yaml

from octoprint_mrbeam import (
    deviceInfo,
    IS_X86,
    mrb_logger,
    user_notification_system,
    MrBeamPlugin,
)
from octoprint_mrbeam.software_update_information import (
    _get_tier_by_id,
    get_update_information,
    SW_UPDATE_INFO_FILE_NAME,
    SW_UPDATE_TIERS,
)
from octoprint_mrbeam.user_notification_system import UserNotificationSystem
from octoprint_mrbeam.util import dict_merge
from octoprint_mrbeam.util.device_info import DeviceInfo

TMP_BASE_FOLDER_PATH = "/tmp/cloud_config_test/"


class SettingsDummy(object):
    tier = None

    def getBaseFolder(self, args, **kwargs):
        return TMP_BASE_FOLDER_PATH

    def get(self, list):
        return self.tier

    def set(self, tier):
        self.tier = tier

    def settings(self, init=False, basedir=None, configfile=None):
        return None


class DummyConnectivityChecker:
    online = True

    def check_immediately(self):
        return self.online


class PluginInfoDummy:
    _refresh_configured_checks = None
    _version_cache = None
    _version_cache_dirty = None


class PluginManagerDummy:
    version = "dummy"
    implementation = PluginInfoDummy()

    def send_plugin_message(self, *args):
        return True

    def get_plugin_info(self, module_id):
        return self


class MrBeamPluginDummy(MrBeamPlugin):
    _settings = SettingsDummy()
    _plugin_manager = PluginManagerDummy()
    _device_info = deviceInfo(use_dummy_values=IS_X86)
    _connectivity_checker = DummyConnectivityChecker()
    _plugin_version = "dummy"
    _event_bus = EventManager()
    _basefolder = "octoprint_mrbeam"

    @patch("octoprint.settings.settings")
    def __init__(self, settings_mock):
        settings_mock.return_value = None
        self._logger = mrb_logger("test.Plugindummy")
        self.user_notification_system = user_notification_system(self)


class SoftwareupdateConfigTestCase(unittest.TestCase):
    _softwareupdate_handler = None
    plugin = None

    def setUp(self):
        self.plugin = MrBeamPluginDummy()
        self.mock_major_tag_version = 1
        with open(
            os.path.join(dirname(realpath(__file__)), "target_octoprint_config.json")
        ) as json_file:
            self.target_octoprint_config = yaml.safe_load(json_file)
        with open(
            os.path.join(
                dirname(realpath(__file__)), "target_find_my_mr_beam_config.json"
            )
        ) as json_file:
            self.target_find_my_mr_beam_config = yaml.safe_load(json_file)
        with open(
            os.path.join(dirname(realpath(__file__)), "target_netconnectd_config.json")
        ) as json_file:
            self.target_netconnectd_config = yaml.safe_load(json_file)
        with open(
            os.path.join(
                dirname(realpath(__file__)), "target_netconnectd_config_legacy.json"
            )
        ) as json_file:
            self.target_netconnectd_config_legacy = yaml.safe_load(json_file)
        with open(
            os.path.join(dirname(realpath(__file__)), "target_mrbeam_config.json")
        ) as json_file:
            self.target_mrbeam_config = yaml.safe_load(json_file)
        with open(
            os.path.join(
                dirname(realpath(__file__)), "target_mrbeam_config_legacy.json"
            )
        ) as json_file:
            self.target_mrbeam_config_legacy = yaml.safe_load(json_file)
        with open(
            os.path.join(dirname(realpath(__file__)), "mock_config.json")
        ) as json_file:
            self.mock_config = yaml.safe_load(json_file)

    @patch.object(
        UserNotificationSystem,
        "show_notifications",
    )
    @patch.object(
        UserNotificationSystem,
        "get_notification",
    )
    def test_server_not_reachable(self, show_notifications_mock, get_notification_mock):
        """
        Testcase to test what happens if the server is not reachable

        Args:
            show_notifications_mock: mock of the notifications system show methode
            get_notification_mock: mock of the notifications system get methode

        Returns:
            None
        """
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            get_notification_mock.return_value = None
            plugin = self.plugin

            with requests_mock.Mocker() as rm:
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/tags",
                    json={"test": "test"},
                    status_code=404,
                )
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=vNone",
                    status_code=404,
                )
                update_config = get_update_information(plugin)
                assert update_config == {
                    "findmymrbeam": {
                        "displayName": "OctoPrint-FindMyMrBeam",
                        "displayVersion": "dummy",
                        "pip": "",
                        "repo": "",
                        "type": "github_commit",
                        "user": "",
                    },
                    "mrbeam": {
                        "displayName": " MrBeam Plugin",
                        "displayVersion": "dummy",
                        "pip": "",
                        "repo": "",
                        "type": "github_commit",
                        "user": "",
                    },
                    "netconnectd": {
                        "displayName": "OctoPrint-Netconnectd Plugin",
                        "displayVersion": "dummy",
                        "pip": "",
                        "repo": "",
                        "type": "github_commit",
                        "user": "",
                    },
                }
        show_notifications_mock.assert_called_with(
            notification_id="missing_updateinformation_info", replay=False
        )
        show_notifications_mock.assert_called_once()

    @patch.object(DeviceInfo, "get_beamos_version_number")
    def test_cloud_config_buster_online(self, device_info_mock):
        """
        Testcase to test the buster config with the online available cloud config

        Args:
            device_info_mock: mocks the device info to change the image version

        Returns:
            None
        """
        self.maxDiff = None
        self.check_if_githubapi_rate_limit_exceeded()
        self.maxDiff = None
        beamos_version_buster = "0.18.0"
        device_info_mock.return_value = beamos_version_buster
        plugin = self.plugin
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            # test for all tiers
            for tier in SW_UPDATE_TIERS:
                self.plugin._settings.set(tier)
                update_config = get_update_information(plugin)
                print("config {}".format(update_config))
                self.assertEquals(
                    update_config["octoprint"],
                    self.target_octoprint_config[_get_tier_by_id(tier)],
                )
                self.validate_mrbeam_module_config(
                    update_config["mrbeam"],
                    _get_tier_by_id(tier),
                    beamos_version_buster,
                )
                self.validate_findmymrbeam_module_config(
                    update_config["findmymrbeam"],
                    _get_tier_by_id(tier),
                    beamos_version_buster,
                )
                self.validate_netconnect_module_config(
                    update_config["netconnectd"],
                    _get_tier_by_id(tier),
                    beamos_version_buster,
                )

    @patch.object(DeviceInfo, "get_beamos_version_number")
    def test_cloud_confg_legacy_online(self, device_info_mock):
        """
        Testcase to test the leagcy image config with the online available cloud config

        Args:
            device_info_mock: mocks the device info to change the image version

        Returns:
            None
        """
        self.check_if_githubapi_rate_limit_exceeded()
        self.maxDiff = None
        beamos_version_legacy = "0.14.0"
        device_info_mock.return_value = beamos_version_legacy
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            plugin = self.plugin

            # test for all tiers
            for tier in SW_UPDATE_TIERS:
                self.plugin._settings.set(tier)
                update_config = get_update_information(plugin)
                print("config {}".format(update_config))
                self.assertEquals(
                    update_config["octoprint"],
                    self.target_octoprint_config[_get_tier_by_id(tier)],
                )
                self.validate_mrbeam_module_config(
                    update_config["mrbeam"],
                    _get_tier_by_id(tier),
                    beamos_version_legacy,
                )
                self.validate_findmymrbeam_module_config(
                    update_config["findmymrbeam"],
                    _get_tier_by_id(tier),
                    beamos_version_legacy,
                )
                self.validate_netconnect_module_config(
                    update_config["netconnectd"],
                    _get_tier_by_id(tier),
                    beamos_version_legacy,
                )

    @patch.object(DeviceInfo, "get_beamos_version_number")
    def test_cloud_confg_buster_mock(self, device_info_mock):
        """
        tests the update info with a mocked server response

        Args:
            device_info_mock: mocks the device info to change the image version

        Returns:
            None
        """
        beamos_version_buster = "0.18.0"
        device_info_mock.return_value = beamos_version_buster
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            with requests_mock.Mocker() as rm:
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/tags",
                    status_code=200,
                    json=[
                        {
                            "name": "v{}.0.2-mock".format(self.mock_major_tag_version),
                        }
                    ],
                )
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=v{}.0.2-mock".format(
                        self.mock_major_tag_version
                    ),
                    status_code=200,
                    json={
                        "content": base64.urlsafe_b64encode(
                            json.dumps(self.mock_config)
                        )
                    },
                )
                plugin = self.plugin

                # test for all tiers
                for tier in SW_UPDATE_TIERS:
                    self.plugin._settings.set(tier)
                    update_config = get_update_information(plugin)
                    self.maxDiff = None
                    self.assertEquals(
                        update_config["octoprint"],
                        self.target_octoprint_config[_get_tier_by_id(tier)],
                    )
                    self.validate_mrbeam_module_config(
                        update_config["mrbeam"],
                        _get_tier_by_id(tier),
                        beamos_version_buster,
                    )
                    self.validate_findmymrbeam_module_config(
                        update_config["findmymrbeam"],
                        _get_tier_by_id(tier),
                        beamos_version_buster,
                    )
                    self.validate_netconnect_module_config(
                        update_config["netconnectd"],
                        _get_tier_by_id(tier),
                        beamos_version_buster,
                    )
        mock_file.assert_called_with(
            TMP_BASE_FOLDER_PATH + SW_UPDATE_INFO_FILE_NAME, "w"
        )

    @patch.object(DeviceInfo, "get_beamos_version_number")
    def test_cloud_confg_legacy_mock(self, device_info_mock):
        """
        tests the updateinfo hook for the legacy image

        Args:
            device_info_mock: mocks the device info to change the image version

        Returns:
            None
        """
        beamos_version_legacy = "0.14.0"
        device_info_mock.return_value = beamos_version_legacy
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            with requests_mock.Mocker() as rm:
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/tags",
                    status_code=200,
                    json=[
                        {
                            "name": "v{}.0.2-mock".format(self.mock_major_tag_version),
                        }
                    ],
                )
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=v{}.0.2-mock".format(
                        self.mock_major_tag_version
                    ),
                    status_code=200,
                    json={
                        "content": base64.urlsafe_b64encode(
                            json.dumps(self.mock_config)
                        )
                    },
                )
                plugin = self.plugin

                # test for all tiers
                for tier in SW_UPDATE_TIERS:
                    self.plugin._settings.set(tier)
                    update_config = get_update_information(plugin)

                    print("config {}".format(update_config))
                    self.maxDiff = None
                    self.assertEquals(
                        update_config["octoprint"],
                        self.target_octoprint_config[_get_tier_by_id(tier)],
                    )
                    self.validate_mrbeam_module_config(
                        update_config["mrbeam"],
                        _get_tier_by_id(tier),
                        beamos_version_legacy,
                    )
                    self.validate_findmymrbeam_module_config(
                        update_config["findmymrbeam"],
                        _get_tier_by_id(tier),
                        beamos_version_legacy,
                    )
                    self.validate_netconnect_module_config(
                        update_config["netconnectd"],
                        _get_tier_by_id(tier),
                        beamos_version_legacy,
                    )
        mock_file.assert_called_with(
            TMP_BASE_FOLDER_PATH + SW_UPDATE_INFO_FILE_NAME, "w"
        )

    @patch.object(
        UserNotificationSystem,
        "show_notifications",
    )
    @patch.object(
        UserNotificationSystem,
        "get_notification",
    )
    def test_cloud_confg_fileerror(
        self,
        user_notification_system_show_mock,
        user_notification_system_get_mock,
    ):
        """
        Tests the update information hook with a fileerror

        Args:
            user_notification_system_show_mock: mock of the notification system show methode
            user_notification_system_get_mock: mock of the notification system get methode

        Returns:
            None
        """
        user_notification_system_get_mock.return_value = None
        with requests_mock.Mocker() as rm:
            rm.get(
                "https://api.github.com/repos/mrbeam/beamos_config/tags",
                status_code=200,
                json=[
                    {
                        "name": "v{}.0.2-mock".format(self.mock_major_tag_version),
                    }
                ],
            )
            rm.get(
                "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=v{}.0.2-mock".format(
                    self.mock_major_tag_version
                ),
                status_code=200,
                json={
                    "content": base64.urlsafe_b64encode(json.dumps(self.mock_config))
                },
            )
            plugin = self.plugin

            update_config = get_update_information(plugin)

            self.assertIsNone(update_config)
        user_notification_system_show_mock.assert_called_with(
            notification_id="write_error_update_info_file_err", replay=False
        )
        user_notification_system_show_mock.assert_called_once()

    def validate_mrbeam_module_config(self, update_config, tier, beamos_version):
        """
        validates the config of the mrbeam software module

        Args:
            update_config: update config
            tier: software tier
            beamos_version: version of the beamos image

        Returns:
            None
        """
        if beamos_version >= "0.18.0":
            target_config = self.target_mrbeam_config
        else:
            target_config = self.target_mrbeam_config_legacy
        self.validate_module_config(update_config, tier, target_config, beamos_version)

    def validate_findmymrbeam_module_config(self, update_config, tier, beamos_version):
        """
        validates the config of a the findmymrbeam software module

        Args:
            update_config: update config
            tier: software tier
            beamos_version: version of the beamos image

        Returns:
            None
        """
        self.validate_module_config(
            update_config, tier, self.target_find_my_mr_beam_config, beamos_version
        )

    def validate_netconnect_module_config(self, update_config, tier, beamos_version):
        """
        validates the config of a the netconnectd software module

        Args:
            update_config: update config
            tier: software tier
            beamos_version: version of the beamos image

        Returns:
            None
        """
        if beamos_version >= "0.18.0":
            target_config = self.target_netconnectd_config
        else:
            target_config = self.target_netconnectd_config_legacy

        self.validate_module_config(update_config, tier, target_config, beamos_version)

    def _set_tier_config(self, config, tier):
        """
        generates the updateinformation for a given software tier

        Args:
            config: update config
            tier: software tier to use

        Returns:
            updateinformation for the given tier
        """
        if "tiers" in config:
            config = dict_merge(config, config["tiers"][tier])
            config.pop("tiers")
        return config

    def validate_module_config(
        self, update_config, tier, target_module_config, beamos_version
    ):
        """
        validates the updateinfromation fot the given software module

        Args:
            update_config: update config
            tier: software tier
            target_module_config: software module to validate
            beamos_version: beamos image version

        Returns:
            None
        """
        copy_target_config = deepcopy(target_module_config)
        if "dependencies" in copy_target_config:
            for dependencie_name, dependencie_config in copy_target_config[
                "dependencies"
            ].items():
                dependencie_config = self._set_tier_config(dependencie_config, tier)
                copy_target_config["dependencies"][
                    dependencie_name
                ] = dependencie_config

        copy_target_config = self._set_tier_config(copy_target_config, tier)

        self.assertEquals(update_config, copy_target_config)

    def check_if_githubapi_rate_limit_exceeded(self):
        """
        checks if the githubapi rate limit is exeeded
        Returns:
            None
        """
        r = requests.get(
            "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json"
        )
        # check if rate limit exceeded
        r.raise_for_status()
