import json
import os, sys
import threading
from datetime import date, datetime
from os.path import join

import requests

from octoprint_mrbeam import MrBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.log import logme
from util.pip_util import get_version_of_pip_module

SW_UPDATE_TIER_PROD = "PROD"
SW_UPDATE_TIER_DEV = "DEV"
SW_UPDATE_TIER_BETA = "BETA"
DEFAULT_REPO_BRANCH_ID = {
    SW_UPDATE_TIER_PROD: "stable",
    SW_UPDATE_TIER_BETA: "beta",
    SW_UPDATE_TIER_DEV: "develop",
}

SW_UPDATE_FILE = "update_info.json"
SW_UPDATE_CLOUD_PATH = "http://192.168.1.48/plugin/mrbeam/static/updates/update_info.json"  # TODO fix link to cloud config

# add to the display name to modules that should be shown at the top of the list
SORT_UP_PREFIX = " "

_logger = mrb_logger("octoprint.plugins.mrbeam.software_update_information")

sw_update_config = dict()

# Commented constants are kept in case we update more packages from the virtualenv
# GLOBAL_PY_BIN = "/usr/bin/python2.7"
# VENV_PY_BIN = sys.executable
GLOBAL_PIP_BIN = "/usr/local/bin/pip"
GLOBAL_PIP_COMMAND = (
    "sudo {}".format(GLOBAL_PIP_BIN) if os.path.isfile(GLOBAL_PIP_BIN) else None
)

BEAMOS_LEGACY_DATE = date(2018, 1, 12)

_softwareupdate_handler = None


def get_modules():
    return sw_update_config


class MrBeamSoftwareupdateHandler:
    def __init__(self, plugin, tier, beamos_date):
        self._plugin = plugin
        self._tier = tier
        self._beamos_date = beamos_date

    def look_for_new_config_file(self):
        """
        starts a thread to look online for a new config file
        """
        th = threading.Thread(target=self._load_update_file_from_cloud)
        th.setName("MrBeamSoftwareupdateHandler:_load_update_file_from_cloud")
        th.daemon = True
        th.start()
        th.join()

    def _load_update_file_from_cloud(self):
        """
        overrides the local update config file if there is a newer one on the server
        """
        _logger.debug("load update file")
        newfile = False
        try:
            r = requests.get(
                SW_UPDATE_CLOUD_PATH,
                timeout=3,
            )
            if os.path.exists(
                join(self._plugin._settings.getBaseFolder("base"), SW_UPDATE_FILE)
            ):  # checks if the file is available otherwise it will be created
                readwriteoption = "r+"
            else:
                readwriteoption = "w+"
                newfile = True
            with open(
                join(self._plugin._settings.getBaseFolder("base"), SW_UPDATE_FILE),
                readwriteoption,
            ) as f:
                try:
                    serverfile_info = json.loads(r.content)
                except ValueError as e:
                    newfile = False
                    _logger.error(
                        "there is a wrong configured config file on the server - cancel loading of new file"
                    )
                    _logger.debug("error %s - %s", e, r.content)
                else:
                    try:
                        update_info = json.load(f)
                        _logger.debug("serverfile_info %s", serverfile_info)
                        _logger.debug(
                            "version compare %s - %s",
                            serverfile_info["version"],
                            update_info["version"],
                        )
                        if serverfile_info["version"] > update_info["version"]:
                            newfile = True
                            _logger.info(
                                "update local file from server - %s -> %s",
                                serverfile_info["version"],
                                update_info["version"],
                            )

                    except ValueError:
                        newfile = True
                        _logger.error(
                            "there is a wrong configured config local file - override local file with server file"
                        )
                    finally:
                        # override local file
                        f.seek(0)
                        f.write(r.content)
                        f.truncate()

        except requests.ReadTimeout:
            _logger.error("timeout while trying to get the update_config file")
        except IOError as e:
            _logger.error(
                "couldn't find/open the file %s %s",
                join(self._plugin._settings.getBaseFolder("base"), SW_UPDATE_FILE),
                e,
            )

        if newfile:
            _logger.info("new file => set info")

            # inform SoftwareUpdate Pluging about new config
            sw_update_plugin = self._plugin._plugin_manager.get_plugin_info(
                "softwareupdate"
            ).implementation
            sw_update_plugin._refresh_configured_checks = True
            sw_update_plugin._version_cache = dict()
            sw_update_plugin._version_cache_dirty = True


@logme(False, True)
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
    global _softwareupdate_handler
    if _softwareupdate_handler is None:
        _softwareupdate_handler = MrBeamSoftwareupdateHandler(plugin, tier, beamos_date)
        _softwareupdate_handler.look_for_new_config_file()

    _set_info_from_file(plugin, tier, beamos_date, _softwareupdate_handler)

    # _logger.debug(
    #     "MrBeam Plugin provides this config (might be overridden by settings!):\n%s",
    #     yaml.dump(sw_update_config, width=50000).strip(),
    # )
    return sw_update_config


def software_channels_available(plugin):
    """
    Returns the avilable softwarechannels
    @param plugin: the calling plugin
    @return: the available softwarechannels
    """
    res = [SW_UPDATE_TIER_PROD, SW_UPDATE_TIER_BETA]
    try:
        if plugin.is_dev_env():
            res.append(SW_UPDATE_TIER_DEV)
    except:
        pass
    return res


def switch_software_channel(plugin, channel):
    """
    Switches the Softwarechannel and triggers the reload of the config
    @param plugin: the calling plugin
    @param channel: the channel where to switch to
    @return:
    """
    old_channel = plugin._settings.get(["dev", "software_tier"])

    if (
        channel in software_channels_available(plugin)
        or (plugin.is_dev_env() and channel == SW_UPDATE_TIER_DEV)
    ) and not channel == old_channel:
        _logger.info("Switching software channel to: %s", channel)
        plugin._settings.set(["dev", "software_tier"], channel)

        try:
            sw_update_plugin = plugin._plugin_manager.get_plugin_info(
                "softwareupdate"
            ).implementation
            sw_update_plugin._refresh_configured_checks = True

            sw_update_plugin._version_cache = dict()

            sw_update_plugin._version_cache_dirty = True

            plugin.analytics_handler.add_software_channel_switch_event(
                old_channel, channel
            )
        except:
            _logger.exception("Exception while switching software channel: ")


def _set_octoprint_config(plugin, tier, config, beamos_date):
    """
    handels the config for octoprint, it have to be set in the config.yaml, because a plugin is not allowed to update the information for octoprint
    @param plugin: the calling plugin
    @param tier: the software tier
    @param config: the config from the config file
    @param beamos_date: the image creation date of the running beamos
    """
    tierversion = get_tier_by_id(tier)
    if tierversion in config:
        module_tier = config[tierversion]
        _set_update_config_from_dict(
            config, module_tier
        )  # set tier config from default settings

    if "beamos_date" in config:
        beamos_date_config = config["beamos_date"]
        for date, beamos_config in beamos_date_config.items():
            _logger.debug(
                "date compare %s >= %s -> %s",
                beamos_date,
                datetime.strptime(date, "%Y-%m-%d").date(),
                beamos_config,
            )
            if beamos_date >= datetime.strptime(date, "%Y-%m-%d").date():
                _set_update_config_from_dict(config, beamos_config)
        _logger.debug(
            "beamosconfig %s %s",
            beamos_config,
            config,
        )
    op_swu_keys = ["plugins", "softwareupdate", "checks", "octoprint"]

    plugin._settings.global_set(op_swu_keys + ["pip"], config["pip"])
    plugin._settings.global_set(op_swu_keys + ["user"], "mrbeam")

    _logger.debug("prerelease %s", config["prerelease"])
    plugin._settings.global_set_boolean(
        op_swu_keys + ["prerelease"], config["prerelease"]
    )

    # plugin._settings.global_set_boolean(op_swu_keys + ["prerelease"], False)


def _set_info_from_file(plugin, tier, beamos_date, _softwareupdate_handler):
    """
    loads update info from the update_info.json file
    the override order: default_settings->module_settings->tier_settings->beamos_settings
    and if there are update_settings set in the config.yaml they will replace all of the module
    the json file should look like:
        {
            "version": <version_of_file>
            "default": {<default_settings>}
            <module_id>: {
                <module_settings>,
                <tier>:{<tier_settings>},
                "beamos_date": {
                    <YYYY-MM-DD>: {<beamos_settings>}
                }
            }
        }

    @param plugin: the plugin from which it was started (mrbeam)
    @param tier: the software tier which should be used
    @param beamos_date: the image creation date of the running beamos
    @param _softwareupdate_handler: the handler class to look for a new config file online
    """
    try:
        with open(join(plugin._settings.getBaseFolder("base"), SW_UPDATE_FILE)) as f:
            update_info = json.load(f)
    except IOError as e:
        _softwareupdate_handler.look_for_new_config_file()
        _logger.error(
            "could not find file %s - error: %s",
            join(plugin._settings.getBaseFolder("base"), SW_UPDATE_FILE),
            e,
        )
    except ValueError as e:
        _softwareupdate_handler.look_for_new_config_file()
        _logger.error(
            "there is a wrong configured config file local - try to load from server"
        )
        _logger.debug("error %s - %s", e, f)
    else:

        fileversion = update_info.pop("version")
        _logger.info("Software update file version: %s", fileversion)
        defaultsettings = update_info.pop("default")

        try:
            _set_octoprint_config(
                plugin, tier, update_info.pop("octoprint"), beamos_date
            )
        except:
            _logger.error("Error while setting octoprint update config")

        for module_id, module in update_info.items():
            try:
                if tier in [
                    SW_UPDATE_TIER_BETA,
                    SW_UPDATE_TIER_DEV,
                    SW_UPDATE_TIER_PROD,
                ]:
                    if _is_override_in_settings(
                        plugin, module_id
                    ):  # check if update config gets overriden in the settings
                        return
                    sw_update_config[module_id] = {}
                    moduleconfig = sw_update_config[module_id]
                    moduleconfig.update(defaultsettings)

                    # get update info for tier branch
                    tierversion = get_tier_by_id(tier)

                    if tierversion in moduleconfig:
                        module_tier = moduleconfig[tierversion]
                        _set_update_config_from_dict(
                            moduleconfig, module_tier
                        )  # set tier config from default settings
                    if tierversion in module:
                        module_tier = module[tierversion]
                        _set_update_config_from_dict(
                            moduleconfig, module_tier
                        )  # override tier config from tiers set in config_file

                    _set_update_config_from_dict(
                        moduleconfig, module
                    )  # set default config from file for module

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
                                    _set_update_config_from_dict(
                                        beamos_config, beamos_config_module_tier
                                    )  # override tier config from tiers set in config_file
                                _set_update_config_from_dict(
                                    moduleconfig, beamos_config
                                )

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
                        try:
                            current_version_global_pip = get_version_of_pip_module(
                                package_name, pip_command
                            )
                            if current_version_global_pip is not None:
                                current_version = current_version_global_pip
                        except:
                            current_version = "not found"
                            _logger.error(
                                "version check error %s",
                                current_version,
                            )

                    else:
                        # get versionnumber of octoprint plugin
                        pluginInfo = plugin._plugin_manager.get_plugin_info(module_id)
                        if pluginInfo is not None:
                            current_version = pluginInfo.version

                    _logger.debug("%s current version: %s", module_id, current_version)
                    moduleconfig.update(
                        {
                            "displayName": module["name"],
                            "displayVersion": current_version,
                        }
                    )
            except:
                _logger.error("Error in module %s %s", module_id, sys.exc_info()[0])
        _logger.debug(sw_update_config)


def _set_update_config_from_dict(update_config, dict):
    update_config.update(dict)


def _get_display_name(plugin, name):
    return name


def get_tier_by_id(tier):
    """
    returns the tier name with the given id
    @param tier: id of the softwaretier
    @return: softwaretier name
    """
    return DEFAULT_REPO_BRANCH_ID.get(tier, tier)


def _is_override_in_settings(plugin, module_id):
    """
    checks if there are softwareupdate settings in the config.yaml for the given module_id
    @param plugin:
    @param module_id:
    @return:
    """
    settings_path = ["plugins", "softwareupdate", "checks", module_id, "override"]
    is_override = plugin._settings.global_get(settings_path)
    if is_override:
        _logger.info("Module %s has overriding config in settings!", module_id)
        return True
    return False
