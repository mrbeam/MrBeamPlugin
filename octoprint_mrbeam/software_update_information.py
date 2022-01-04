import base64
import json
import os
import shutil
import threading
from datetime import date
from datetime import datetime
from os.path import dirname, realpath
from os.path import join
from shutil import copy

import requests
import semantic_version
import yaml
from octoprint.plugins.softwareupdate import SoftwareUpdatePlugin
from requests import ConnectionError
from requests.adapters import HTTPAdapter
from semantic_version import Spec
from urllib3 import Retry

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util import get_thread, dict_merge, logme, logExceptions
from util.pip_util import get_version_of_pip_module

SW_UPDATE_TIER_PROD = "PROD"
SW_UPDATE_TIER_BETA = "BETA"
SW_UPDATE_TIER_ALPHA = "ALPHA"
SW_UPDATE_TIER_DEV = "DEV"
DEFAULT_REPO_BRANCH_ID = {
    SW_UPDATE_TIER_PROD: "stable",
    SW_UPDATE_TIER_BETA: "beta",
    SW_UPDATE_TIER_ALPHA: "alpha",
    SW_UPDATE_TIER_DEV: "develop",
}
MAJOR_VERSION_CLOUD_CONFIG = 0

_logger = mrb_logger("octoprint.plugins.mrbeam.software_update_information")

# Commented constants are kept in case we update more packages from the virtualenv
# GLOBAL_PY_BIN = "/usr/bin/python2.7"
# VENV_PY_BIN = sys.executable
GLOBAL_PIP_BIN = "/usr/local/bin/pip"
GLOBAL_PIP_COMMAND = (
    "sudo {}".format(GLOBAL_PIP_BIN) if os.path.isfile(GLOBAL_PIP_BIN) else None
)

BEAMOS_LEGACY_DATE = date(2018, 1, 12)

"""this is used to lock the config file loading from server and using it as update information"""
config_file_lock = threading.Lock()


def get_tag_of_github_repo(repo):
    import requests
    import json

    try:
        url = "https://api.github.com/repos/mrbeam/" + repo + "/tags"

        headers = {
            "Accept": "application/json",
        }

        s = requests.Session()
        retry = Retry(connect=5, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.keep_alive = False

        response = s.request("GET", url, headers=headers, timeout=3)
        if response:
            json_data = json.loads(response.text)
            versionlist = [
                semantic_version.Version(version.get("name")[1:])
                for version in json_data
            ]
            majorversion = Spec(
                "<" + str(MAJOR_VERSION_CLOUD_CONFIG + 1) + ".0.0"
            )  # simpleSpec("0.*.*")
            print(versionlist)
            return majorversion.select(versionlist)
        else:
            _logger.warning("no valid response for the tag of the update_config file")
            return None
    except requests.ReadTimeout:
        _logger.warning("timeout while trying to get the tag of the update_config file")
        return None
    except ConnectionError:
        _logger.warning(
            "connection error while trying to get the tag of the update_config file"
        )
        return None


def get_config_of_tag(tag):
    import requests
    import json

    try:
        url = (
            "https://api.github.com/repos/mrbeam/beamos_config/contents/docs/sw-update-conf.json"
            + "?ref=v"
            + str(tag)
        )

        headers = {
            "Accept": "application/json",
        }

        s = requests.Session()
        retry = Retry(connect=5, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.keep_alive = False

        response = s.request("GET", url, headers=headers)
    except requests.ReadTimeout:
        _logger.warning("timeout while trying to get the update_config file")
        return None
    except ConnectionError:
        _logger.warning("connection error while trying to get the update_config file")
        return None

    if response:
        json_data = json.loads(response.text)
        yaml_file = base64.b64decode(json_data["content"])

        return yaml.safe_load(yaml_file)
    else:
        _logger.warning("no valid response for the update_config file")
        return None


def on_event(self, event, payload):
    from octoprint.events import Events

    if (
        event != Events.CONNECTIVITY_CHANGED
        or not payload
        or not payload.get("new", False)
    ):
        return

    _logger.info("Connectifiy changed, update plugin test")
    thread = threading.Thread(target=self.get_current_versions, kwargs=dict(force=True))
    thread.daemon = True
    thread.start()


class SoftwareUpdatePluginMrBeam(SoftwareUpdatePlugin):
    def on_event(self, event, payload):
        from octoprint.events import Events

        if (
            event != Events.CONNECTIVITY_CHANGED
            or not payload
            or not payload.get("new", False)
        ):
            return
        self._logger.info("Connectifiy changed, update plugin test")

        thread = threading.Thread(
            target=self.get_current_versions, kwargs=dict(force=True)
        )
        thread.daemon = True
        thread.start()


def get_update_information(plugin):
    """
    Gets called from the octoprint.plugin.softwareupdate.check_config Hook from Octoprint
    Starts a thread to look online for a new config file
    sets the config for the Octoprint Softwareupdate Plugin with the data from the config file
    @param plugin: calling plugin
    @return: the config for the Octoprint embedded softwareupdate Plugin
    """
    tier = plugin._settings.get(["dev", "software_tier"])
    beamos_tier, beamos_date = plugin._device_info.get_beamos_version()
    _logger.info("SoftwareUpdate using tier: %s %s", tier, beamos_date)

    # todo if offline start thread that will wait till online

    if plugin._connectivity_checker.check_immediately():
        config_tag = get_tag_of_github_repo("beamos_config")
        _logger.warn("online")
        # if plugin._connectivity_checker.check_immediately():  # check if device online
        if config_tag:
            cloud_config = get_config_of_tag(get_tag_of_github_repo("beamos_config"))
            if cloud_config:
                print("cloud config", cloud_config)
                return _set_info_from_cloud_config(
                    plugin, tier, beamos_date, cloud_config
                )
    else:
        _logger.warn("no internet connection")

    user_notification_system = plugin.user_notification_system
    user_notification_system.show_notifications(
        user_notification_system.get_notification(
            notification_id="missing_updateinformation_info", replay=False
        )
    )

    sw_update_plugin = plugin._plugin_manager.get_plugin_info(
        "softwareupdate"
    ).implementation

    sw_update_plugin._version_cache = dict()
    sw_update_plugin._version_cache_dirty = True
    return _set_info_from_cloud_config(
        plugin,
        tier,
        beamos_date,
        {
            "default": {},
            "modules": {
                "mrbeam": {
                    "name": " MrBeam Plugin offline2",
                    "type": "github_commit",
                    "user": "",
                    "repo": "",
                    "pip": "",
                },
                "mrbeamdoc": {
                    "name": "Mr Beam Documentation offline2",
                    "type": "github_commit",
                    "user": "",
                    "repo": "",
                    "pip": "",
                },
                "netconnectd": {
                    "name": "OctoPrint-Netconnectd Plugin offline2",
                    "type": "github_commit",
                    "user": "",
                    "repo": "",
                    "pip": "",
                },
                "findmymrbeam": {
                    "name": "OctoPrint-FindMyMrBeam offline2",
                    "type": "github_commit",
                    "user": "",
                    "repo": "",
                    "pip": "",
                },
            },
        },
    )


def software_channels_available(plugin):
    ret = [SW_UPDATE_TIER_PROD, SW_UPDATE_TIER_BETA]
    if plugin.is_dev_env():
        # fmt: off
        ret.extend([SW_UPDATE_TIER_ALPHA, SW_UPDATE_TIER_DEV, ])
        # fmt: on
    return ret


def switch_software_channel(plugin, channel):
    """
    Switches the Softwarechannel and triggers the reload of the config
    @param plugin: the calling plugin
    @param channel: the channel where to switch to
    @return:
    """
    old_channel = plugin._settings.get(["dev", "software_tier"])
    if channel in software_channels_available(plugin) and channel != old_channel:
        _logger.info("Switching software channel to: %s", channel)
        plugin._settings.set(["dev", "software_tier"], channel)
        # fmt: off
        sw_update_plugin = plugin._plugin_manager.get_plugin_info("softwareupdate").implementation
        # fmt: on
        sw_update_plugin._refresh_configured_checks = True
        sw_update_plugin._version_cache = dict()
        sw_update_plugin._version_cache_dirty = True
        plugin.analytics_handler.add_software_channel_switch_event(old_channel, channel)


def reload_update_info(plugin):
    """
    clears the version cache and refires the get_update_info hook
    @param plugin: MrBeamPlugin
    @return:
    """

    _logger.debug("Reload update info")

    # fmt: off
    sw_update_plugin = plugin._plugin_manager.get_plugin_info("softwareupdate").implementation
    # fmt: on
    sw_update_plugin._refresh_configured_checks = True
    sw_update_plugin._version_cache = dict()
    sw_update_plugin._version_cache_dirty = True


@logExceptions
def _set_info_from_cloud_config(plugin, tier, beamos_date, cloud_config):
    """
    loads update info from the update_info.json file
    the override order: default_settings->module_settings->tier_settings->beamos_settings
    and if there are update_settings set in the config.yaml they will replace all of the module
    the json file should look like:
        {
            "default": {<default_settings>}
            "modules": {
                <module_id>: {
                    <module_settings>,
                    <tier>:{<tier_settings>},
                    "beamos_date": {
                        <YYYY-MM-DD>: {<beamos_settings>}
                    }
                }
                "dependencies: {<module>}
            }
        }

    @param plugin: the plugin from which it was started (mrbeam)
    @param tier: the software tier which should be used
    @param beamos_date: the image creation date of the running beamos
    @param _softwareupdate_handler: the handler class to look for a new config file online
    """
    if cloud_config:
        sw_update_config = dict()
        _logger.debug("update_info {}".format(cloud_config))
        defaultsettings = cloud_config.get("default", None)
        modules = cloud_config["modules"]

        # TODO maybe drop the higher levels of the config so the output will be more tidy
        for module_id, module in modules.items():
            if tier in [
                SW_UPDATE_TIER_BETA,
                SW_UPDATE_TIER_DEV,
                SW_UPDATE_TIER_PROD,
                SW_UPDATE_TIER_ALPHA,
            ]:
                sw_update_config[module_id] = {}
                moduleconfig = sw_update_config[module_id]
                moduleconfig.update(defaultsettings)
                print("defaultsettings", defaultsettings)
                print("moduleconfig", moduleconfig)

                # get update info for tier branch
                tierversion = get_tier_by_id(tier)

                if tierversion in moduleconfig:
                    moduleconfig = dict_merge(
                        moduleconfig, moduleconfig[tierversion]
                    )  # set tier config from default settings

                moduleconfig = dict_merge(
                    moduleconfig, module
                )  # set default config from file for module

                if tierversion in module:
                    moduleconfig = dict_merge(
                        moduleconfig, module[tierversion]
                    )  # override tier config from tiers set in config_file

                # have to be after the default config from file
                if "beamos_date" in module:
                    beamos_date_config = module["beamos_date"]
                    for date, beamos_config in beamos_date_config.items():
                        _logger.debug(
                            "date compare %s >= %s -> %s",
                            beamos_date,
                            datetime.strptime(date, "%Y-%m-%d").date(),
                            beamos_config,
                        )
                        if beamos_date >= datetime.strptime(date, "%Y-%m-%d").date():
                            if tierversion in beamos_config:
                                beamos_config_module_tier = beamos_config[tierversion]
                                moduleconfig = dict_merge(
                                    beamos_config, beamos_config_module_tier
                                )  # override tier config from tiers set in config_file
                            moduleconfig = dict_merge(moduleconfig, beamos_config)

                if "branch" in moduleconfig and "{tier}" in moduleconfig["branch"]:
                    moduleconfig["branch"] = moduleconfig["branch"].format(
                        tier=get_tier_by_id(tier)
                    )

                # get version number
                current_version = "-"
                _logger.debug(
                    "pip command check %s %s - %s",
                    module,
                    moduleconfig,
                    "pip_command" not in moduleconfig,
                )
                if "global_pip_command" in module and "pip_command" not in moduleconfig:
                    moduleconfig["pip_command"] = GLOBAL_PIP_COMMAND
                if "pip_command" in moduleconfig:
                    # get version number of pip modules
                    pip_command = moduleconfig["pip_command"]
                    # if global_pip_command is set module is installed outside of our virtualenv therefor we can't use default pip command.
                    # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
                    # pip_command = GLOBAL_PIP_COMMAND
                    package_name = (
                        module["package_name"]
                        if "package_name" in module
                        else module_id
                    )
                    _logger.debug("get version %s %s", package_name, pip_command)

                    current_version_global_pip = get_version_of_pip_module(
                        package_name, pip_command
                    )
                    if current_version_global_pip is not None:
                        current_version = current_version_global_pip

                else:
                    # get versionnumber of octoprint plugin
                    pluginInfo = plugin._plugin_manager.get_plugin_info(module_id)
                    if pluginInfo is not None:
                        current_version = pluginInfo.version

                if module_id != "octoprint":
                    _logger.debug("%s current version: %s", module_id, current_version)
                    moduleconfig.update(
                        {
                            "displayVersion": current_version,
                        }
                    )
                if "name" in module:
                    moduleconfig["displayName"] = module["name"]

                moduleconfig = clean_update_config(moduleconfig)
                sw_update_config[module_id] = moduleconfig

        _logger.debug("sw_update_config {}".format(sw_update_config))
        return sw_update_config
    else:
        return None


def clean_update_config(update_config):
    pop_list = ["alpha", "beta", "stable", "develop", "beamos_date", "name"]
    for key in set(update_config).intersection(pop_list):
        del update_config[key]
    return update_config


def get_tier_by_id(tier):
    """
    returns the tier name with the given id
    @param tier: id of the softwaretier
    @return: softwaretier name
    """
    return DEFAULT_REPO_BRANCH_ID.get(tier, tier)
