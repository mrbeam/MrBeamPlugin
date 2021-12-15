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
import yaml

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

SW_UPDATE_FILE = "update_info.json"
SW_UPDATE_CLOUD_PATH = "https://mr-beam.org/beamos/config/sw-update-conf"

_logger = mrb_logger("octoprint.plugins.mrbeam.software_update_information")

# sw_update_config = dict()

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


class MrBeamSoftwareupdateHandler:
    CLOUD_FILE = 1
    LOCAL_FILE = 2
    REPO_FILE = 3

    def __init__(self, plugin):
        self._plugin = plugin

    # @get_thread(daemon=False)
    @logExceptions
    def load_update_file_from_cloud(self, localfilemissing=False):
        """
        overrides the local update config file if there is a newer one on the server
        """
        with config_file_lock:
            newfile = False
            servererror = False
            serverfile_request = None
            returncode = 0

            # load file from server
            try:
                serverfile_request = requests.get(
                    SW_UPDATE_CLOUD_PATH,
                    timeout=3,
                )
            except requests.ReadTimeout:
                _logger.error("timeout while trying to get the update_config file")
                servererror = True
            except IOError as e:
                servererror = True
                _logger.error(
                    "There was an error on the server - error:%s",
                    e,
                )

            # check if valid
            if serverfile_request:
                try:
                    serverfile_info = json.loads(serverfile_request.content)
                    serverfile_verson = serverfile_info["version"]
                except ValueError as e:
                    servererror = True
                    _logger.error(
                        "there is a wrong configured config file on the server - cancel loading of new file"
                    )
                    _logger.debug("error %s - %s", e, serverfile_request.content)

            # check if local file exists valid
            if not os.path.exists(get_sw_update_file_path(self._plugin)):
                localfilemissing = True

            # if both valid compare and override
            if not servererror and serverfile_request:
                if localfilemissing:  # create new file
                    readwriteoption = "w+"
                    newfile = True
                else:  # checks if the file is available otherwise it will be created
                    readwriteoption = "r+"
                with open(
                    get_sw_update_file_path(self._plugin),
                    readwriteoption,
                ) as f:
                    try:
                        update_info = json.load(f)
                        _logger.debug("serverfile_info %s", serverfile_info)
                        _logger.debug(
                            "version compare %s - %s",
                            serverfile_verson,
                            update_info["version"],
                        )
                        if serverfile_verson > update_info["version"]:
                            newfile = True
                            _logger.info(
                                "update local file from server - %s -> %s",
                                serverfile_verson,
                                update_info["version"],
                            )

                    except ValueError:
                        newfile = True
                        _logger.error(
                            "there is a wrong configured local config file - override local file with server file"
                        )
                    except KeyError:
                        localfilemissing = True
                        _logger.exception("there is a keyerror in the local file")

                    # if local config file invalid override by server
                    if newfile or localfilemissing:
                        _logger.debug("override local file")
                        # override local file
                        f.seek(0)
                        f.write(serverfile_request.content)
                        f.truncate()
                        returncode = self.CLOUD_FILE

            # if server invalid use local file
            if not serverfile_request:
                servererror = True
                returncode = self.LOCAL_FILE

            # if both invalid use repo file
            if servererror and localfilemissing:
                _logger.info(
                    "fallback use local default config file /files/software_update/update_info.json"
                )
                try:
                    shutil.copy(
                        join(
                            dirname(realpath(__file__)),
                            "files/software_update/update_info.json",
                        ),
                        get_sw_update_file_path(self._plugin),
                    )
                    newfile = True
                    returncode = self.REPO_FILE
                except IOError as e:
                    _logger.error(
                        "not even fallback version available: %s",
                        e,
                    )

            # if file changed, reload update info
            if newfile:
                _logger.info("new file => set info")

                # inform SoftwareUpdate Pluging about new config
                sw_update_plugin = self._plugin._plugin_manager.get_plugin_info(
                    "softwareupdate"
                ).implementation
                sw_update_plugin._refresh_configured_checks = True
                sw_update_plugin._version_cache = dict()
                sw_update_plugin._version_cache_dirty = True
            return returncode


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

    _softwareupdate_handler = MrBeamSoftwareupdateHandler(plugin)
    _softwareupdate_handler.load_update_file_from_cloud()
    return _set_info_from_file(
        get_sw_update_file_path(plugin), tier, beamos_date, _softwareupdate_handler
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


def get_sw_update_file_path(plugin):
    """
    returns the path to the sw update file
    @param plugin:
    @return: path to file
    """
    return join(plugin._settings.getBaseFolder("base"), SW_UPDATE_FILE)


@logExceptions
def _set_info_from_file(plugin, tier, beamos_date, _softwareupdate_handler):
    """
    loads update info from the update_info.json file
    the override order: default_settings->module_settings->tier_settings->beamos_settings
    and if there are update_settings set in the config.yaml they will replace all of the module
    the json file should look like:
        {
            "version": <version_of_file>
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
    with config_file_lock:
        sw_update_file_path = get_sw_update_file_path(plugin)
        sw_update_config = dict()
        try:
            with open(sw_update_file_path) as f:
                update_info = yaml.safe_load(f)
        except IOError as e:
            _logger.exception(
                "could not find file %s - error: %s",
                sw_update_file_path,
                e,
            )
            loadfilethread = _softwareupdate_handler.load_update_file_from_cloud(
                localfilemissing=True
            )
            loadfilethread.join()
        except ValueError as e:
            _logger.exception(
                "there is a wrong configured config file local - try to load from server"
            )
            _logger.debug("error %s - %s", e, f)
            loadfilethread = _softwareupdate_handler.load_update_file_from_cloud()
            loadfilethread.join()
        else:
            _logger.debug("update_info {}".format(update_info))
            fileversion = update_info["version"]
            _logger.info("Software update file version: %s", fileversion)
            defaultsettings = update_info["default"]
            modules = update_info["modules"]

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
                            if (
                                beamos_date
                                >= datetime.strptime(date, "%Y-%m-%d").date()
                            ):
                                if tierversion in beamos_config:
                                    beamos_config_module_tier = beamos_config[
                                        tierversion
                                    ]
                                    moduleconfig = dict_merge(
                                        beamos_config, beamos_config_module_tier
                                    )  # override tier config from tiers set in config_file
                                moduleconfig = dict_merge(moduleconfig, beamos_config)

                    if "{tier}" in moduleconfig["branch"]:
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
                    if (
                        "global_pip_command" in module
                        and "pip_command" not in moduleconfig
                    ):
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
                        _logger.debug(
                            "%s current version: %s", module_id, current_version
                        )
                        moduleconfig.update(
                            {
                                "displayVersion": current_version,
                            }
                        )
                    if "name" in module:
                        moduleconfig["displayName"] = module["name"]
                    # sw_update_config.update(moduleconfig)
                    moduleconfig = clean_update_config(moduleconfig)
                    sw_update_config[module_id] = moduleconfig

            _logger.debug("sw_update_config {}".format(sw_update_config))
            return sw_update_config


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
