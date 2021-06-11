import os, sys

from octoprint_mrbeam import IS_X86
from octoprint_mrbeam.mrb_logger import mrb_logger
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

SW_UPDATE_FILE_PATH = "static/updates/update_info.json"
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
# GLOBAL_PIP_COMMAND = "sudo {} -m pip".format(GLOBAL_PY_BIN) if os.path.isfile(GLOBAL_PY_BIN) else None #  --disable-pip-version-check
# VENV_PIP_COMMAND = ("%s -m pip --disable-pip-version-check" % VENV_PY_BIN).split(' ') if os.path.isfile(VENV_PY_BIN) else None
BEAMOS_LEGACY_DATE = date(2018, 1, 12)


def get_modules():
    return sw_update_config


def get_update_information(self):
    result = dict()

    tier = self._settings.get(["dev", "software_tier"])
    _logger.info("SoftwareUpdate using tier: %s", tier)

    _config_octoprint(self, tier)

    _set_info_from_file(self, tier)
    return sw_update_config


def software_channels_available(plugin):
    ret = [SW_UPDATE_TIER_PROD, SW_UPDATE_TIER_BETA]
    if plugin.is_dev_env():
        # fmt: off
        ret.extend([SW_UPDATE_TIER_ALPHA, SW_UPDATE_TIER_DEV,])
        # fmt: on
    return ret


def switch_software_channel(plugin, channel):
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


def _config_octoprint(self, tier):
    op_swu_keys = ["plugins", "softwareupdate", "checks", "octoprint"]

    self._settings.global_set(op_swu_keys + ["checkout_folder"], "/home/pi/OctoPrint")
    self._settings.global_set(
        op_swu_keys + ["pip"],
        "https://github.com/mrbeam/OctoPrint/archive/{target_version}.zip",
    )
    self._settings.global_set(op_swu_keys + ["user"], "mrbeam")
    self._settings.global_set(
        op_swu_keys + ["stable_branch", "branch"], "mrbeam2-stable"
    )

    if tier in [SW_UPDATE_TIER_DEV]:
        self._settings.global_set_boolean(op_swu_keys + ["prerelease"], True)
    else:
        self._settings.global_set_boolean(op_swu_keys + ["prerelease"], False)


def _load_update_file_from_cloud():
    try:
        r = requests.get(
            SW_UPDATE_CLOUD_PATH,
            timeout=10,
        )
        with open(join(dirname(realpath(__file__)), SW_UPDATE_FILE_PATH), "r+") as f:
            serverfile_info = json.loads(r.content)
            update_info = json.load(f)
            _logger.info("serverfile_info %s", serverfile_info)
            _logger.info(
                "version compare %s - %s",
                serverfile_info["version"],
                update_info["version"],
            )
            if serverfile_info["version"] > update_info["version"]:
                _logger.info("update local file from server")
                f.seek(0)
                f.write(r.content)
                f.truncate()
        # print(update_info)
    except requests.ReadTimeout:
        _logger.error("timeout while trying to get the update_config file")


def _set_info_from_file(self, tier):
    """
    loads update info from the update_info.json file
    the json file should look like:
        {
            <module_id>: {
                <module_settings>,
                <tier>:{<tier_settings>}
            }
        }

    @param tier: the software tier which should be used
    """
    # todo check for new file on server
    _load_update_file_from_cloud()

    with open(join(dirname(realpath(__file__)), SW_UPDATE_FILE_PATH)) as f:
        update_info = json.load(f)
    print(update_info)
    fileversion = update_info.pop("version")
    _logger.info("Software update file version: %s", fileversion)

    for module_id, module in update_info.items():
        pip_command = False
        if tier in [SW_UPDATE_TIER_BETA, SW_UPDATE_TIER_DEV, SW_UPDATE_TIER_PROD]:
            if _is_override_in_settings(
                self, module_id
            ):  # check if update config gets overriden in the settings
                return

            # get version number
            current_version = "-"
            if "global_pip_command" in module and module["global_pip_command"]:
                # if global_pip_command is set module is installed outside of our virtualenv therefor we can't use default pip command.
                # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
                pip_command = GLOBAL_PIP_COMMAND
                pip_name = module["pip_name"] if "pip_name" in module else module_id
                current_version_global_pip = get_version_of_pip_module(
                    pip_name, pip_command
                )
                if current_version_global_pip is not None:
                    current_version = current_version_global_pip
            else:
                # get versionnumber of octoprint plugin
                pluginInfo = self._plugin_manager.get_plugin_info(module_id)
                if pluginInfo is not None:
                    current_version = pluginInfo.version
            _logger.info("%s current version: %s", module_id, current_version)
            sw_update_config[module_id] = dict(
                displayName=module["name"],
                displayVersion=current_version,
            )

            if pip_command:
                sw_update_config[module_id].update({"pip_command": pip_command})

            _set_update_config_from_dict(
                sw_update_config[module_id], module
            )  # set default config

            # get update info for tier branch
            tierversion = ""
            if tier == SW_UPDATE_TIER_PROD:
                tierversion = "stable"
            elif tier == SW_UPDATE_TIER_BETA:
                tierversion = "beta"
            elif tier == SW_UPDATE_TIER_DEV:
                tierversion = "develop"
            if tierversion in module:
                module_tier = module[tierversion]
                _set_update_config_from_dict(
                    sw_update_config[module_id], module_tier
                )  # set tier config


def _set_update_config_from_dict(update_config, dict):
    update_config.update(dict)


def get_tier_by_id(tier):
    return DEFAULT_REPO_BRANCH_ID.get(tier, tier)


def _is_override_in_settings(plugin, module_id):
    settings_path = ["plugins", "softwareupdate", "checks", module_id, "override"]
    is_override = plugin._settings.global_get(settings_path)
    if is_override:
        _logger.info("Module %s has overriding config in settings!", module_id)
        return True
    return False
