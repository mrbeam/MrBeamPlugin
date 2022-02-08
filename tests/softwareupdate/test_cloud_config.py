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
from datetime import date, datetime
from mock import mock_open
from ddt import ddt
from mock import patch
from octoprint.events import EventManager

from octoprint_mrbeam import (
    deviceInfo,
    IS_X86,
    mrb_logger,
    user_notification_system,
    MrBeamPlugin,
)
from octoprint_mrbeam.software_update_information import (
    SW_UPDATE_TIER_DEV,
    SW_UPDATE_TIER_ALPHA,
    SW_UPDATE_TIER_PROD,
    SW_UPDATE_TIER_BETA,
    _get_tier_by_id,
    get_update_information,
    SW_UPDATE_INFO_FILE_NAME,
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


class DummyConnectifityChecker:
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
    _connectivity_checker = DummyConnectifityChecker()
    _plugin_version = "dummy"
    _event_bus = EventManager()

    @patch("octoprint.settings.settings")
    def __init__(self, settings_mock):
        settings_mock.return_value = None
        self._logger = mrb_logger("test.Plugindummy")
        self.user_notification_system = user_notification_system(self)


@ddt
class SoftwareupdateConfigTestCase(unittest.TestCase):
    _softwareupdate_handler = None
    plugin = None

    def setUp(self):
        self.plugin = MrBeamPluginDummy()
        with open(
            os.path.join(dirname(realpath(__file__)), "target_octoprint_config.json")
        ) as json_file:
            self.target_octoprint_config = json.load(json_file)
        with open(
            os.path.join(
                dirname(realpath(__file__)), "target_find_my_mr_beam_config.json"
            )
        ) as json_file:
            self.target_find_my_mr_beam_config = json.load(json_file)
        with open(
            os.path.join(dirname(realpath(__file__)), "target_netconnectd_config.json")
        ) as json_file:
            self.target_netconnectd_config = json.load(json_file)
        with open(
            os.path.join(dirname(realpath(__file__)), "target_mrbeam_config.json")
        ) as json_file:
            self.target_mrbeam_config = json.load(json_file)
        with open(
            os.path.join(dirname(realpath(__file__)), "mock_config.json")
        ) as json_file:
            self.mock_config = json.load(json_file)

    @patch.object(
        UserNotificationSystem,
        "show_notifications",
    )
    @patch.object(
        UserNotificationSystem,
        "get_notification",
    )
    def test_server_not_reachable(self, show_notifications_mock, get_notification_mock):
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
                        "displayName": "OctoPrint-FindMyMrBeam offline2",
                        "displayVersion": "dummy",
                        "pip": "",
                        "repo": "",
                        "type": "github_commit",
                        "user": "",
                    },
                    "mrbeam": {
                        "displayName": " MrBeam Plugin offline2",
                        "displayVersion": "dummy",
                        "pip": "",
                        "repo": "",
                        "type": "github_commit",
                        "user": "",
                    },
                    "mrbeamdoc": {
                        "displayName": "Mr Beam Documentation offline2",
                        "displayVersion": "dummy",
                        "pip": "",
                        "repo": "",
                        "type": "github_commit",
                        "user": "",
                    },
                    "netconnectd": {
                        "displayName": "OctoPrint-Netconnectd Plugin offline2",
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

    @patch.object(DeviceInfo, "get_beamos_version")
    def test_cloud_config_buster_online(self, device_info_mock):
        self.check_if_githubapi_rate_limit_exceeded()
        beamos_date_buster = date(2021, 6, 11)
        device_info_mock.return_value = "PROD", beamos_date_buster
        plugin = self.plugin
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            tiers = [
                SW_UPDATE_TIER_DEV,
                SW_UPDATE_TIER_ALPHA,
                SW_UPDATE_TIER_BETA,
                SW_UPDATE_TIER_PROD,
            ]
            # test for all tiers
            for tier in tiers:
                self.plugin._settings.set(tier)
                update_config = get_update_information(plugin)
                print("config {}".format(update_config))
                self.assertEquals(
                    update_config["octoprint"],
                    self.target_octoprint_config[_get_tier_by_id(tier)],
                )
                self.validate_mrbeam_module_config(
                    update_config["mrbeam"], _get_tier_by_id(tier), beamos_date_buster
                )
                self.validate_findmymrbeam_module_config(
                    update_config["findmymrbeam"],
                    _get_tier_by_id(tier),
                    beamos_date_buster,
                )
                self.validate_netconnect_module_config(
                    update_config["netconnectd"],
                    _get_tier_by_id(tier),
                    beamos_date_buster,
                )

    @patch.object(DeviceInfo, "get_beamos_version")
    def test_cloud_confg_legacy_online(self, device_info_mock):
        self.check_if_githubapi_rate_limit_exceeded()

        beamos_date_legacy = date(2018, 1, 12)
        device_info_mock.return_value = "PROD", beamos_date_legacy
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            plugin = self.plugin

            tiers = [
                SW_UPDATE_TIER_DEV,
                SW_UPDATE_TIER_ALPHA,
                SW_UPDATE_TIER_BETA,
                SW_UPDATE_TIER_PROD,
            ]
            # test for all tiers
            for tier in tiers:
                self.plugin._settings.set(tier)
                update_config = get_update_information(plugin)
                print("config {}".format(update_config))
                self.assertEquals(
                    update_config["octoprint"],
                    self.target_octoprint_config[_get_tier_by_id(tier)],
                )
                self.validate_mrbeam_module_config(
                    update_config["mrbeam"], _get_tier_by_id(tier), beamos_date_legacy
                )
                self.validate_findmymrbeam_module_config(
                    update_config["findmymrbeam"],
                    _get_tier_by_id(tier),
                    beamos_date_legacy,
                )
                self.validate_netconnect_module_config(
                    update_config["netconnectd"],
                    _get_tier_by_id(tier),
                    beamos_date_legacy,
                )

    # TEST BUSTER [ALPHA; BETA; DEVELOP; STABLE]
    @patch.object(DeviceInfo, "get_beamos_version")
    def test_cloud_confg_buster_mock(self, device_info_mock):
        beamos_date_buster = date(2021, 6, 11)
        device_info_mock.return_value = "PROD", beamos_date_buster
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            with requests_mock.Mocker() as rm:
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/tags",
                    status_code=200,
                    json=[
                        {
                            "name": "v0.0.2-mock",
                        }
                    ],
                )
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=v0.0.2-mock",
                    status_code=200,
                    json={
                        "content": base64.urlsafe_b64encode(
                            json.dumps(self.mock_config)
                        )
                    },
                )
                plugin = self.plugin

                tiers = [
                    SW_UPDATE_TIER_DEV,
                    SW_UPDATE_TIER_ALPHA,
                    SW_UPDATE_TIER_BETA,
                    SW_UPDATE_TIER_PROD,
                ]
                # test for all tiers
                for tier in tiers:
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
                        beamos_date_buster,
                    )
                    self.validate_findmymrbeam_module_config(
                        update_config["findmymrbeam"],
                        _get_tier_by_id(tier),
                        beamos_date_buster,
                    )
                    self.validate_netconnect_module_config(
                        update_config["netconnectd"],
                        _get_tier_by_id(tier),
                        beamos_date_buster,
                    )
        mock_file.assert_called_with(
            TMP_BASE_FOLDER_PATH + SW_UPDATE_INFO_FILE_NAME, "w"
        )

    # TEST LEGACY [ALPHA; BETA; DEVELOP; STABLE]
    @patch.object(DeviceInfo, "get_beamos_version")
    def test_cloud_confg_legacy_mock(self, device_info_mock):
        beamos_date_legacy = date(2018, 1, 12)
        device_info_mock.return_value = "PROD", beamos_date_legacy
        with patch("__builtin__.open", mock_open(read_data="data")) as mock_file:
            with requests_mock.Mocker() as rm:
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/tags",
                    status_code=200,
                    json=[
                        {
                            "name": "v0.0.2-mock",
                        }
                    ],
                )
                rm.get(
                    "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=v0.0.2-mock",
                    status_code=200,
                    json={
                        "content": base64.urlsafe_b64encode(
                            json.dumps(self.mock_config)
                        )
                    },
                )
                plugin = self.plugin

                tiers = [
                    SW_UPDATE_TIER_DEV,
                    SW_UPDATE_TIER_ALPHA,
                    SW_UPDATE_TIER_BETA,
                    SW_UPDATE_TIER_PROD,
                ]
                # test for all tiers
                for tier in tiers:
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
                        beamos_date_legacy,
                    )
                    self.validate_findmymrbeam_module_config(
                        update_config["findmymrbeam"],
                        _get_tier_by_id(tier),
                        beamos_date_legacy,
                    )
                    self.validate_netconnect_module_config(
                        update_config["netconnectd"],
                        _get_tier_by_id(tier),
                        beamos_date_legacy,
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
        user_notification_system_get_mock.return_value = None
        with requests_mock.Mocker() as rm:
            rm.get(
                "https://api.github.com/repos/mrbeam/beamos_config/tags",
                status_code=200,
                json=[
                    {
                        "name": "v0.0.2-mock",
                    }
                ],
            )
            rm.get(
                "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json?ref=v0.0.2-mock",
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

    def validate_mrbeam_module_config(self, update_config, tier, beamos_date):
        self.validate_module_config(
            update_config, tier, self.target_mrbeam_config, beamos_date
        )

    def validate_findmymrbeam_module_config(self, update_config, tier, beamos_date):
        self.validate_module_config(
            update_config, tier, self.target_find_my_mr_beam_config, beamos_date
        )

    def validate_netconnect_module_config(self, update_config, tier, beamos_date):
        self.validate_module_config(
            update_config, tier, self.target_netconnectd_config, beamos_date=beamos_date
        )

    def _set_beamos_config(self, config, beamos_date=None):
        if "beamos_date" in config:
            for date, beamos_config in config["beamos_date"].items():
                if beamos_date >= datetime.strptime(date, "%Y-%m-%d").date():
                    config = dict_merge(config, beamos_config)
            config.pop("beamos_date")
        return config

    def _set_tier_config(self, config, tier):
        if "tiers" in config:
            config = dict_merge(config, config["tiers"][tier])
            config.pop("tiers")
        return config

    def validate_module_config(
        self, update_config, tier, target_module_config, beamos_date
    ):
        copy_target_config = deepcopy(target_module_config)
        self._set_beamos_config(copy_target_config, beamos_date)
        if "dependencies" in copy_target_config:
            for dependencie_name, dependencie_config in copy_target_config[
                "dependencies"
            ].items():
                dependencie_config = self._set_beamos_config(
                    dependencie_config, beamos_date
                )
                dependencie_config = self._set_tier_config(dependencie_config, tier)
                copy_target_config["dependencies"][
                    dependencie_name
                ] = dependencie_config

        copy_target_config = self._set_tier_config(copy_target_config, tier)

        self.assertEquals(update_config, copy_target_config)

    def check_if_githubapi_rate_limit_exceeded(self):
        r = requests.get(
            "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json"
        )
        # check if rate limit exceeded
        r.raise_for_status()
