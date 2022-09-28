import copy
from datetime import date
from enum import Enum
from octoprint_mrbeam.mrb_logger import mrb_logger
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

_logger = mrb_logger("octoprint.plugins.mrbeam.software_update_information")

BEAMOS_LEGACY_DATE = date(2018, 1, 12)  # still used in the migrations


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


def _get_current_version(input_moduleconfig, module_id, plugin):
    """returns the version of the given module.

    Args:
        input_moduleconfig (dict): module to get the version for
        module_id (str): id of the module
        plugin (:obj:`OctoPrint Plugin`): Mr Beam Plugin

    Returns:
        version of the module or None
    """
    # get version number
    current_version = None
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


def _get_tier_by_id(tier):
    """
    returns the tier name with the given id
    Args:
        tier: id of the software tier

    Returns:
        softwaretier name
    """
    return DEFAULT_REPO_BRANCH_ID.get(tier, tier)
