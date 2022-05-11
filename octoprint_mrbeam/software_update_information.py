import copy
import json
import operator
import os
from datetime import date

import pkg_resources
from enum import Enum

import semantic_version
import yaml
from octoprint.plugins.softwareupdate import exceptions as softwareupdate_exceptions
from requests import ConnectionError
from requests.adapters import HTTPAdapter, MaxRetryError
from semantic_version import Spec
from urllib3 import Retry

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util import dict_merge, logExceptions
from octoprint_mrbeam.util.github_api import get_file_of_repo_for_tag, REPO_URL
from util.pip_util import get_version_of_pip_module


class SWUpdateTier(Enum):
    STABLE = "PROD"
    BETA = "BETA"
    ALPHA = "ALPHA"
    DEV = "DEV"


SW_UPDATE_TIERS_DEV = [SWUpdateTier.ALPHA.value, SWUpdateTier.DEV.value]
SW_UPDATE_TIERS_PROD = [SWUpdateTier.STABLE.value, SWUpdateTier.BETA.value]
SW_UPDATE_TIERS = SW_UPDATE_TIERS_DEV + SW_UPDATE_TIERS_PROD

DEFAULT_REPO_BRANCH_ID = {
    SWUpdateTier.STABLE.value: "stable",
    SWUpdateTier.BETA.value: "beta",
    SWUpdateTier.ALPHA.value: "alpha",
    SWUpdateTier.DEV.value: "develop",
}
MAJOR_VERSION_CLOUD_CONFIG = 1
SW_UPDATE_INFO_FILE_NAME = "update_info.json"

_logger = mrb_logger("octoprint.plugins.mrbeam.software_update_information")

# Commented constants are kept in case we update more packages from the virtualenv
# GLOBAL_PY_BIN = "/usr/bin/python2.7"
# VENV_PY_BIN = sys.executable
GLOBAL_PIP_BIN = "/usr/local/bin/pip"
GLOBAL_PIP_COMMAND = (
    "sudo {}".format(GLOBAL_PIP_BIN) if os.path.isfile(GLOBAL_PIP_BIN) else None
)

BEAMOS_LEGACY_VERSION = "0.14.0"
BEAMOS_LEGACY_DATE = date(2018, 1, 12)  # still used in the migrations

FALLBACK_UPDATE_CONFIG = {
    "mrbeam": {
        "name": " MrBeam Plugin",
        "type": "github_commit",
        "user": "",
        "repo": "",
        "pip": "",
    },
    "netconnectd": {
        "name": "OctoPrint-Netconnectd Plugin",
        "type": "github_commit",
        "user": "",
        "repo": "",
        "pip": "",
    },
    "findmymrbeam": {
        "name": "OctoPrint-FindMyMrBeam",
        "type": "github_commit",
        "user": "",
        "repo": "",
        "pip": "",
    },
}


class UpdateFetchingInformationException(Exception):
    pass


def get_tag_of_github_repo(repo):
    """
    return the latest tag of a github repository
    Args:
        repo: repository name

    Returns:
        latest tag of the given majorversion <MAJOR_VERSION_CLOUD_CONFIG>
    """
    import requests
    import json

    try:
        url = "{repo_url}/tags".format(repo_url=REPO_URL.format(repo=repo))

        headers = {
            "Accept": "application/json",
        }

        s = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.3)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.keep_alive = False

        response = s.request("GET", url, headers=headers, timeout=3)
        response.raise_for_status()  # This will throw an exception if status is 4xx or 5xx
        if response:
            json_data = json.loads(response.text)
            versionlist = [
                semantic_version.Version(version.get("name")[1:])
                for version in json_data
            ]
            majorversion = Spec(
                "<{}.0.0".format(str(MAJOR_VERSION_CLOUD_CONFIG + 1))
            )  # simpleSpec("0.*.*")
            return "v{}".format(majorversion.select(versionlist))
        else:
            _logger.warning(
                "no valid response for the tag of the update_config file {}".format(
                    response
                )
            )
            return None
    except MaxRetryError:
        _logger.warning("timeout while trying to get the tag of the update_config file")
        return None
    except requests.HTTPError as e:
        _logger.warning("server error {}".format(e))
        return None
    except ConnectionError:
        _logger.warning(
            "connection error while trying to get the tag of the update_config file"
        )
        return None


def get_update_information(plugin):
    """
    Gets called from the octoprint.plugin.softwareupdate.check_config Hook from Octoprint
    Starts a thread to look online for a new config file
    sets the config for the Octoprint Softwareupdate Plugin with the data from the config file
    Args:
        plugin: Mr Beam Plugin

    Returns:
        the config for the Octoprint embedded softwareupdate Plugin
    """
    try:
        tier = plugin._settings.get(["dev", "software_tier"])
        beamos_version = plugin._device_info.get_beamos_version_number()
        _logger.info(
            "SoftwareUpdate using tier: {tier} {beamos_version}".format(
                tier=tier, beamos_version=beamos_version
            )
        )

        if plugin._connectivity_checker.check_immediately():
            config_tag = get_tag_of_github_repo("beamos_config")
            # if plugin._connectivity_checker.check_immediately():  # check if device online
            if config_tag:
                cloud_config = yaml.safe_load(
                    get_file_of_repo_for_tag(
                        repo="beamos_config",
                        file="docs/sw-update-conf.json",
                        tag=config_tag,
                    )
                )
                if cloud_config:
                    return _set_info_from_cloud_config(
                        plugin, tier, beamos_version, cloud_config
                    )
        else:
            _logger.warn("no internet connection")

        _logger.error("No information about available updates could be retrieved E-1000 explicit check:{}".format(
            plugin.explicit_update_check))
        software_update_notify(plugin, notification_id="missing_updateinformation_info")

        # mark update config as dirty
        sw_update_plugin = plugin._plugin_manager.get_plugin_info(
            "softwareupdate"
        ).implementation
        _clear_version_cache(sw_update_plugin)
    except Exception as e:
        _logger.exception(e)

    return _set_info_from_cloud_config(
        plugin,
        tier,
        beamos_version,
        {},
    )


def _clear_version_cache(sw_update_plugin):
    sw_update_plugin._version_cache = dict()
    sw_update_plugin._version_cache_dirty = True


def software_channels_available(plugin):
    """
    return the available software channels
    Args:
        plugin: Mr Beam Plugin

    Returns:
        list of available software channels
    """
    ret = copy.deepcopy(SW_UPDATE_TIERS_PROD)
    if plugin.is_dev_env():
        # fmt: off
        ret += SW_UPDATE_TIERS_DEV
        # fmt: on
    return ret


def switch_software_channel(plugin, channel):
    """
    Switches the Softwarechannel and triggers the reload of the config
    Args:
        plugin: Mr Beam Plugin
        channel: the channel where to switch to

    Returns:
        None
    """
    _logger.debug("switch_software_channel")
    old_channel = plugin._settings.get(["dev", "software_tier"])
    if channel in software_channels_available(plugin) and channel != old_channel:
        _logger.info("Switching software channel to: {channel}".format(channel=channel))
        plugin._settings.set(["dev", "software_tier"], channel)
        reload_update_info(plugin)


def reload_update_info(plugin, clicked_by_user=False):
    """
    clears the version cache and refires the get_update_info hook
    Args:
        plugin: Mr Beam Plugin

    Returns:
        None
    """
    if clicked_by_user:
        plugin.set_explicit_update_check()

    _logger.debug("Reload update info")

    # fmt: off
    sw_update_plugin = plugin._plugin_manager.get_plugin_info("softwareupdate").implementation
    # fmt: on
    sw_update_plugin._refresh_configured_checks = True
    _clear_version_cache(sw_update_plugin)


@logExceptions
def _set_info_from_cloud_config(plugin, tier, beamos_version, cloud_config):
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
                    "beamos_version": {
                        "X.X.X": {<beamos_settings>} # only supports major minor patch
                    }
                }
                "dependencies: {<module>}
            }
        }
    Args:
        plugin: Mr Beam Plugin
        tier: the software tier which should be used
        beamos_version: the version of the running beamos
        cloud_config: the update config from the cloud

    Returns:
        software update information or None
    """
    if cloud_config:
        sw_update_config = dict()
        _logger.debug("update_info {}".format(cloud_config))
        defaultsettings = cloud_config.get("default", None)
        modules = cloud_config["modules"]

        try:
            for module_id, module in modules.items():
                if tier in SW_UPDATE_TIERS:
                    sw_update_config[module_id] = {}

                    module = dict_merge(defaultsettings, module)

                    sw_update_config[module_id] = _generate_config_of_module(
                        module_id, module, defaultsettings, tier, beamos_version, plugin
                    )
        except softwareupdate_exceptions.ConfigurationInvalid as e:
            _logger.exception(
                "ConfigurationInvalid {}, will use fallback dummy instead E-1003 explicit check:{}".format(e,
                                                                                                           plugin.explicit_update_check))
            sw_update_config = FALLBACK_UPDATE_CONFIG
            software_update_notify(plugin, notification_id="update_fetching_information_err", err_msg=["E-1003"])
        except UpdateFetchingInformationException as e:
            _logger.exception(
                "UpdateFetchingInformationException {}, will use fallback dummy instead - explicit check:{}".format(e,
                                                                                                                    plugin.explicit_update_check))
            sw_update_config = FALLBACK_UPDATE_CONFIG

        _logger.debug("sw_update_config {}".format(sw_update_config))

        sw_update_file_path = os.path.join(
            plugin._settings.getBaseFolder("base"), SW_UPDATE_INFO_FILE_NAME
        )
        try:
            with open(sw_update_file_path, "w") as f:
                f.write(json.dumps(sw_update_config))
        except (IOError, TypeError):
            _logger.exception(
                "can't create update info file, will use fallback dummy instead E-1001 explicit check:{}".format(
                    plugin.explicit_update_check))
            sw_update_config = FALLBACK_UPDATE_CONFIG
            software_update_notify(plugin, notification_id="write_error_update_info_file_err")

    else:
        sw_update_config = FALLBACK_UPDATE_CONFIG

    plugin.clear_explicit_update_check()
    return sw_update_config


def software_update_notify(plugin, notification_id, err_msg=[]):
    if plugin.explicit_update_check:
        user_notification_system = plugin.user_notification_system
        user_notification_system.show_notifications(
            user_notification_system.get_notification(
                notification_id=notification_id, replay=False, err_msg=err_msg
            )
        )


def _generate_config_of_module(
    module_id, input_moduleconfig, defaultsettings, tier, beamos_version, plugin
):
    """
    generates the config of a software module <module_id>
    Args:
        module_id: the id of the software module
        input_moduleconfig: moduleconfig
        defaultsettings: default settings
        tier: software tier
        beamos_version: version of the beamos
        plugin: Mr Beam Plugin

    Returns:
        software update informations for the module
    """
    if tier in SW_UPDATE_TIERS:
        # merge default settings and input is master
        input_moduleconfig = dict_merge(defaultsettings, input_moduleconfig)

        # get update info for tier branch
        tierversion = _get_tier_by_id(tier)

        if tierversion in input_moduleconfig:
            input_moduleconfig = dict_merge(
                input_moduleconfig, input_moduleconfig[tierversion]
            )  # set tier config from default settings

        # have to be after the default config from file

        input_moduleconfig = dict_merge(
            input_moduleconfig,
            _generate_config_of_beamos(input_moduleconfig, beamos_version, tierversion),
        )

        if "branch" in input_moduleconfig and "{tier}" in input_moduleconfig["branch"]:
            input_moduleconfig["branch"] = input_moduleconfig["branch"].format(
                tier=_get_tier_by_id(tier)
            )

        if "update_script" in input_moduleconfig:
            if "update_script_relative_path" not in input_moduleconfig:
                raise softwareupdate_exceptions.ConfigurationInvalid(
                    "update_script_relative_path is missing in update config for {}".format(
                        module_id
                    )
                )
            try:
                if not os.path.isdir(input_moduleconfig["update_folder"]):
                    os.makedirs(input_moduleconfig["update_folder"])
            except (IOError, OSError) as e:
                software_update_notify(plugin, notification_id="update_fetching_information_err", err_msg=["E-1002"])
                raise UpdateFetchingInformationException("could not create folder {} E-1002 e:{}".format(
                    input_moduleconfig["update_folder"], e
                ))
            update_script_path = os.path.join(
                plugin._basefolder, input_moduleconfig["update_script_relative_path"]
            )
            input_moduleconfig["update_script"] = input_moduleconfig[
                "update_script"
            ].format(update_script=update_script_path)

        current_version = _get_curent_version(input_moduleconfig, module_id, plugin)

        if module_id != "octoprint":
            _logger.debug(
                "{module_id} current version: {current_version}".format(
                    module_id=module_id, current_version=current_version
                )
            )
            input_moduleconfig["displayVersion"] = (
                current_version if current_version else "-"
            )
        if "name" in input_moduleconfig:
            input_moduleconfig["displayName"] = input_moduleconfig["name"]

        input_moduleconfig = _clean_update_config(input_moduleconfig)

        if "dependencies" in input_moduleconfig:
            for dependencie_name, dependencie_config in input_moduleconfig[
                "dependencies"
            ].items():
                input_moduleconfig["dependencies"][
                    dependencie_name
                ] = _generate_config_of_module(
                    dependencie_name,
                    dependencie_config,
                    {},
                    tier,
                    beamos_version,
                    plugin,
                )
        return input_moduleconfig


def _get_curent_version(input_moduleconfig, module_id, plugin):
    """
    returns the version of the given module

    Args:
        input_moduleconfig (dict): module to get the version for
        module_id (str): id of the module
        plugin (:obj:`OctoPrint Plugin`): Mr Beam Plugin

    Returns:
        version of the module or None
    """
    # get version number
    current_version = None
    if (
        "global_pip_command" in input_moduleconfig
        and "pip_command" not in input_moduleconfig
    ):
        input_moduleconfig["pip_command"] = GLOBAL_PIP_COMMAND
    if "pip_command" in input_moduleconfig:
        # get version number of pip modules
        pip_command = input_moduleconfig["pip_command"]
        # if global_pip_command is set module is installed outside of our virtualenv therefor we can't use default pip command.
        # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
        # pip_command = GLOBAL_PIP_COMMAND
        package_name = (
            input_moduleconfig["package_name"]
            if "package_name" in input_moduleconfig
            else module_id
        )

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
    return current_version


class VersionComperator:
    """
    Version Comperator class to compare two versions with the compare method
    """

    def __init__(self, identifier, priority, compare):
        self.identifier = identifier
        self.priority = priority
        self.compare = compare

    @staticmethod
    def get_comperator(comparision_string, comparision_options):
        """
        returns the comperator of the given list of VersionComperator with the matching identifier

        Args:
            comparision_string (str): identifier to search for
            comparision_options (list): list of VersionComperator objects

        Returns:
            object: matching VersionComperator object
        """
        for item in comparision_options:
            if item.identifier == comparision_string:
                return item


def _generate_config_of_beamos(moduleconfig, beamos_version, tierversion):
    """
    generates the config for the given beamos_version of the tierversion

    Args:
        moduleconfig (dict): update config of the module
        beamos_version (str): version of the beamos
        tierversion (str): software tier

    Returns:
        dict: beamos config of the tierversion
    """
    if "beamos_version" not in moduleconfig:
        _logger.debug("no beamos_version set in moduleconfig")
        return {}

    config_for_beamos_versions = moduleconfig.get("beamos_version")

    comparision_options = [
        VersionComperator("__eq__", 5, operator.eq),
        VersionComperator("__le__", 4, operator.le),
        VersionComperator("__lt__", 3, operator.lt),
        VersionComperator("__ge__", 2, operator.ge),
        VersionComperator("__gt__", 1, operator.gt),
    ]

    sorted_config_for_beamos_versions = sorted(
        config_for_beamos_versions.items(),
        key=lambda com: VersionComperator.get_comperator(
            com[0], comparision_options
        ).priority,
    )

    config_for_beamos = get_config_for_version(
        beamos_version, sorted_config_for_beamos_versions, comparision_options
    )

    if tierversion in config_for_beamos:
        beamos_config_module_tier = config_for_beamos.get(tierversion)
        config_for_beamos = dict_merge(
            config_for_beamos, beamos_config_module_tier
        )  # override tier config from tiers set in config_file

    return config_for_beamos


def get_config_for_version(target_version, config, comparision_options):
    config_to_be_updated = {}
    for comperator, version_config_items in config:
        # sort the version config items by the version
        sorted_version_config_items = sorted(
            version_config_items.items(),
            key=lambda version_config_tuple: pkg_resources.parse_version(
                version_config_tuple[0]
            ),
        )

        for check_version, version_config in sorted_version_config_items:
            if VersionComperator.get_comperator(
                comperator, comparision_options
            ).compare(target_version, check_version):
                config_to_be_updated = dict_merge(config_to_be_updated, version_config)
    return config_to_be_updated


def _clean_update_config(update_config):
    """
    removes working parameters from the given config
    Args:
        update_config: update config information

    Returns:
        cleaned version of the update config
    """
    pop_list = ["alpha", "beta", "stable", "develop", "beamos_version", "name"]
    for key in set(update_config).intersection(pop_list):
        del update_config[key]
    return update_config


def _get_tier_by_id(tier):
    """
    returns the tier name with the given id
    Args:
        tier: id of the software tier

    Returns:
        softwaretier name
    """
    return DEFAULT_REPO_BRANCH_ID.get(tier, tier)
