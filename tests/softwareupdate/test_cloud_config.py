# coding=utf-8
from __future__ import absolute_import, division, print_function


import unittest
from datetime import date

import requests_mock
from ddt import ddt

from octoprint_mrbeam import deviceInfo, IS_X86
from octoprint_mrbeam.software_update_information import (
    get_config_of_tag,
    _set_info_from_cloud_config,
    get_tag_of_github_repo,
)
from octoprint_mrbeam.util import dict_merge


class SettingsDummy(object):
    tier = None

    def getBaseFolder(self, args, **kwargs):
        return "/tmp/cloud_config_test/"

    def get(self, list):
        return self.tier

    def set(self, tier):
        self.tier = tier


class DummyConnectifityChecker:
    online = True


class PluginInfoDummy:
    _refresh_configured_checks = None
    _version_cache = None
    _version_cache_dirty = None


class PluginManagerDummy:
    version = "dummy"
    implementation = PluginInfoDummy()

    def get_plugin_info(self, module_id):
        return self

    # sw_update_plugin = self._plugin._plugin_manager.get_plugin_info(
    #     "softwareupdate"
    # ).implementation
    # sw_update_plugin._refresh_configured_checks = True
    # sw_update_plugin._version_cache = dict()
    # sw_update_plugin._version_cache_dirty = True


class MrBeamPluginDummy:
    _settings = SettingsDummy()
    _plugin_manager = PluginManagerDummy()
    _device_info = deviceInfo(use_dummy_values=IS_X86)


target_octoprint_config = {
    "develop": {
        "type": "github_commit",
        "restart": "environment",
        "user": "mrbeam",
        "branch": "develop",
        "branch_default": "develop",
    },
    "beta": {
        "type": "github_release",
        "prerelease_channel": "mrbeam2-beta",
        "prerelease": True,
        "restart": "environment",
        "user": "mrbeam",
        "branch": "mrbeam2-beta",
        "branch_default": "mrbeam2-beta",
    },
    "alpha": {
        "type": "github_release",
        "prerelease_channel": "mrbeam2-alpha",
        "prerelease": True,
        "restart": "environment",
        "user": "mrbeam",
        "branch": "mrbeam2-alpha",
        "branch_default": "mrbeam2-alpha",
    },
    "stable": {
        "type": "github_release",
        "restart": "environment",
        "user": "mrbeam",
        "branch": "mrbeam2-stable",
        "branch_default": "mrbeam2-stable",
    },
}
target_mrbeam_config = {
    "displayName": " MrBeam Plugin",
    "repo": "MrBeamPlugin",
    "restart": "octoprint",
    "pip": "https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
    "type": "github_commit",
    "user": "mrbeam",
    "dependencies": {
        "mrbeam-ledstrips": {
            "name": "MrBeam LED Strips",
            "repo": "MrBeamLedStrips",
            "pip": "https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
            "global_pip_command": True,
            "beamos_date": {
                "2021-06-11": {
                    "pip_command": "sudo /usr/local/mrbeam_ledstrips/venv/bin/pip"
                }
            },
        },
        "iobeam": {
            "name": "iobeam",
            "type": "bitbucket_commit",
            "repo": "iobeam",
            "pip": "git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target_version}",
            "global_pip_command": True,
            "api_user": "MrBeamDev",
            "api_password": "v2T5pFkmdgDqbFBJAqrt",
            "beamos_date": {
                "2021-06-11": {"pip_command": "sudo /usr/local/iobeam/venv/bin/pip"}
            },
        },
        "mrb_hw_info": {
            "name": "mrb_hw_info",
            "type": "bitbucket_commit",
            "repo": "mrb_hw_info",
            "pip": "git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target_version}",
            "global_pip_command": True,
            "package_name": "mrb-hw-info",
            "api_user": "MrBeamDev",
            "api_password": "v2T5pFkmdgDqbFBJAqrt",
            "beamos_date": {
                "2021-06-11": {"pip_command": "sudo /usr/local/iobeam/venv/bin/pip"}
            },
        },
    },
    "tiers": {
        "develop": {"branch": "develop", "branch_default": "develop"},
        "beta": {"branch": "mrbeam2-beta", "branch_default": "mrbeam2-beta"},
        "alpha": {"branch": "mrbeam2-alpha", "branch_default": "mrbeam2-alpha"},
        "stable": {"branch": "mrbeam2-stable", "branch_default": "mrbeam2-stable"},
    },
    "displayVersion": "dummy",
}


@ddt
class SettingsTestCase(unittest.TestCase):
    _softwareupdate_handler = None
    plugin = None

    def setUp(self):
        self.plugin = MrBeamPluginDummy()

    def test_server_not_reachable(self):
        plugin = self.plugin
        tier = "DEV"
        beamos_date = date(2018, 1, 12)
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
            tag_of_github_repo = get_tag_of_github_repo("beamos_config")
            assert tag_of_github_repo == None
            cloud_config = get_config_of_tag(tag_of_github_repo)
            assert cloud_config == None
            self.plugin._settings.set(tier)
            update_config = _set_info_from_cloud_config(
                plugin, tier, beamos_date, cloud_config
            )
            assert update_config == None

    def test_cloud_confg_dev(self):
        plugin = self.plugin
        tier = "DEV"
        self.plugin._settings.set(tier)
        beamos_date = date(2018, 1, 12)
        cloud_config = get_config_of_tag(get_tag_of_github_repo("beamos_config"))
        update_config = _set_info_from_cloud_config(
            plugin, tier, beamos_date, cloud_config
        )
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "develop"
        assert update_config["octoprint"] == target_octoprint_config["develop"]
        self.validate_module_config(update_config["mrbeam"], "develop")

    def test_cloud_confg_alpha(self):
        plugin = self.plugin
        tier = "ALPHA"
        beamos_date = date(2018, 1, 12)
        cloud_config = get_config_of_tag(get_tag_of_github_repo("beamos_config"))
        self.plugin._settings.set(tier)
        update_config = _set_info_from_cloud_config(
            plugin, tier, beamos_date, cloud_config
        )
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "mrbeam2-alpha"
        assert update_config["octoprint"] == target_octoprint_config["alpha"]
        self.validate_module_config(update_config["mrbeam"], "alpha")

    def test_cloud_confg_beta(self):
        plugin = self.plugin
        tier = "BETA"
        beamos_date = date(2018, 1, 12)
        cloud_config = get_config_of_tag(get_tag_of_github_repo("beamos_config"))
        self.plugin._settings.set(tier)
        update_config = _set_info_from_cloud_config(
            plugin, tier, beamos_date, cloud_config
        )
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "mrbeam2-beta"
        assert update_config["octoprint"] == target_octoprint_config["beta"]
        self.validate_module_config(update_config["mrbeam"], "beta")

    def test_cloud_confg_prod(self):
        plugin = self.plugin
        tier = "PROD"
        beamos_date = date(2018, 1, 12)
        cloud_config = get_config_of_tag(get_tag_of_github_repo("beamos_config"))
        update_config = _set_info_from_cloud_config(
            plugin, tier, beamos_date, cloud_config
        )
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "mrbeam2-stable"
        assert update_config["octoprint"] == target_octoprint_config["stable"]
        self.validate_module_config(update_config["mrbeam"], "stable")

    def validate_module_config(self, update_config, tier):
        target_config = dict_merge(
            target_mrbeam_config, target_mrbeam_config["tiers"][tier]
        )
        target_config.pop("tiers")
        assert update_config == target_config
