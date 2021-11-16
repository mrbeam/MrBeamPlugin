# coding=utf-8
from __future__ import absolute_import, division, print_function

# __author__ = "Gina Häußge <osd@foosel.net>"
# __license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
# __copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"


import unittest
from datetime import date

import mock
import warnings

import requests_mock
from ddt import ddt, unpack, data

import octoprint.plugin
import octoprint.settings

from octoprint_mrbeam import MrBeamPlugin
from octoprint_mrbeam.software_update_information import _set_info_from_file, MrBeamSoftwareupdateHandler, \
    SW_UPDATE_CLOUD_PATH
from octoprint_mrbeam.util import dict_merge


class SettingsDummy(object):
    def getBaseFolder(self, args, **kwargs):
        return "/tmp/cloud_config_test/"

class PluginInfoDummy():
    _refresh_configured_checks = None
    _version_cache = None
    _version_cache_dirty = None
class PluginManagerDummy():
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


class MrBeamPluginDummy():
    _settings = SettingsDummy()
    _plugin_manager = PluginManagerDummy()


# def _settings.getBaseFolder():
# 	"base")
target_octoprint_config = {
    "develop": {
        "type": "github_commit",
        "restart": "environment",
        "user": "mrbeam",
        "displayVersion": "dummy",
        "branch": "develop"
    },
    "beta": {
        "type": "github_release",
        "prerelease_channel": "mrbeam2-beta",
        "prerelease": True,
        "restart": "environment",
        "user": "mrbeam",
        "displayVersion": "dummy",
        "branch": "mrbeam2-beta"
    },
    "alpha": {
        "type": "github_release",
        "prerelease_channel": "mrbeam2-alpha",
        "prerelease": True,
        "restart": "environment",
        "user": "mrbeam",
        "displayVersion": "dummy",
        "branch": "mrbeam2-alpha"
    },
    "stable": {
        "type": "github_release",
        "restart": "environment",
        "user": "mrbeam",
        "displayVersion": "dummy",
        "branch": "mrbeam2-stable"
    }
}
target_mrbeam_config = {
    "displayName": " MrBeam Plugin",
    "repo": "MrBeamPlugin",
    "restart": "octoprint",
    "pip": "https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
    'type': 'github_commit',
    'user': 'mrbeam',
    'displayVersion': 'dummy',
    "dependencies": {
        "mrbeam-ledstrips": {
            "name": "MrBeam LED Strips",
            "repo": "MrBeamLedStrips",
            "pip": "https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
            "global_pip_command": True
        },
        "iobeam": {
            "name": "iobeam",
            "type": "bitbucket_commit",
            "repo": "iobeam",
            "pip": "git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target_version}",
            "global_pip_command": True,
            "api_user": "MrBeamDev",
            "api_password": "v2T5pFkmdgDqbFBJAqrt"
        },
        "mrb_hw_info": {
            "name": "mrb_hw_info",
            "type": "bitbucket_commit",
            "repo": "mrb_hw_info",
            "pip": "git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target_version}",
            "global_pip_command": True,
            "package_name": "mrb-hw-info",
            "api_user": "MrBeamDev",
            "api_password": "v2T5pFkmdgDqbFBJAqrt"
        }
    },
    "tiers": {
        "develop": {
            "branch": "develop"
        },
        "beta": {
            "branch": "mrbeam2-beta"
        },
        "alpha": {
            "branch": "mrbeam2-alpha"
        },
        "stable": {
            "branch": "mrbeam2-stable"
        }
    }
}


@ddt
class SettingsTestCase(unittest.TestCase):
    _softwareupdate_handler = None
    plugin = None

    def setUp(self):
        self.plugin = MrBeamPluginDummy()
        if self._softwareupdate_handler is None:
            self._softwareupdate_handler = MrBeamSoftwareupdateHandler(self.plugin)
            self._softwareupdate_handler.load_update_file_from_cloud()

    def test_file_fallback(self):
        with requests_mock.Mocker() as rm:
            rm.get(SW_UPDATE_CLOUD_PATH, json={"test":"test"}, status_code=404)
            assert self._softwareupdate_handler.load_update_file_from_cloud() == self._softwareupdate_handler.LOCAL_FILE

            #if localfile not available and servererror
            assert self._softwareupdate_handler.load_update_file_from_cloud(localfilemissing=True) == self._softwareupdate_handler.REPO_FILE
            # assert self._softwareupdate_handler.returncode == 404
            # self.assertEqual(response, 'Weather data subscribed successfully!')
            # requests_mock.get(SW_UPDATE_CLOUD_PATH, json={'name': 'awesome-mock'})
        #if file online reachable use this
        #if file online not reachable use local file
        #if local file has errors use mrbeam config file
        mock_open = mock.mock_open()
        with mock.patch('__builtin__.open', mock_open):
            assert self._softwareupdate_handler.load_update_file_from_cloud() == self._softwareupdate_handler.CLOUD_FILE

            with requests_mock.Mocker() as rm:
                rm.get(SW_UPDATE_CLOUD_PATH, json={"test": "test"}, status_code=404)
                assert self._softwareupdate_handler.load_update_file_from_cloud() == self._softwareupdate_handler.CLOUD_FILE
        return True

    def test_cloud_confg_dev(self):
        plugin = self.plugin
        tier = "DEV"
        beamos_date = date(2018, 1, 12)
        update_config = _set_info_from_file(plugin, tier, beamos_date, self._softwareupdate_handler)
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "develop"
        assert update_config["octoprint"] == target_octoprint_config["develop"]
        self.validate_module_config(update_config["mrbeam"], 'develop')

    def test_cloud_confg_alpha(self):
        plugin = self.plugin
        tier = "ALPHA"
        beamos_date = date(2018, 1, 12)
        update_config = _set_info_from_file(plugin, tier, beamos_date, self._softwareupdate_handler)
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "mrbeam2-alpha"
        assert update_config["octoprint"] == target_octoprint_config["alpha"]
        self.validate_module_config(update_config["mrbeam"], 'alpha')

    def test_cloud_confg_beta(self):
        plugin = self.plugin
        tier = "BETA"
        beamos_date = date(2018, 1, 12)
        update_config = _set_info_from_file(plugin, tier, beamos_date, self._softwareupdate_handler)
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "mrbeam2-beta"
        assert update_config["octoprint"] == target_octoprint_config["beta"]
        self.validate_module_config(update_config["mrbeam"], 'beta')

    def test_cloud_confg_prod(self):
        plugin = self.plugin
        tier = "PROD"
        beamos_date = date(2018, 1, 12)
        update_config = _set_info_from_file(plugin, tier, beamos_date, self._softwareupdate_handler)
        print("config {}".format(update_config))
        assert update_config["mrbeam"]["branch"] == "mrbeam2-stable"
        assert update_config["octoprint"] == target_octoprint_config["stable"]
        self.validate_module_config(update_config["mrbeam"], 'stable')

    def validate_module_config(self, update_config, tier):
        target_config = dict_merge(target_mrbeam_config, target_mrbeam_config['tiers'][tier])
        target_config.pop('tiers')
        assert update_config == target_config