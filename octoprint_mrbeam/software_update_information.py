from datetime import datetime, date
import os, sys

from octoprint.util import dict_merge
from octoprint_mrbeam import IS_X86
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util import logExceptions
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

# add to the display name to modules that should be shown at the top of the list
SORT_UP_PREFIX = " "


_logger = mrb_logger("octoprint.plugins.mrbeam.software_update_information")

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


def get_update_information(plugin):
    result = dict()

    tier = plugin._settings.get(["dev", "software_tier"])
    beamos_tier, beamos_date = plugin._device_info.get_beamos_version()
    _logger.info("SoftwareUpdate using tier: %s", tier)

    # The increased number of separate virtualenv for iobeam, netconnectd, ledstrips
    # will increase the "discovery time" to find those package versions.
    # "map-reduce" method can decrease lookup time by processing them in parallel
    res = dict(
        reduce(
            dict_merge,
            [
                _set_info_mrbeam_plugin(plugin, tier, beamos_date),
                _set_info_mrbeamdoc(plugin, tier),
                _set_info_netconnectd_plugin(plugin, tier, beamos_date),
                _set_info_findmymrbeam(plugin, tier),
                _set_info_mrbeamledstrips(plugin, tier, beamos_date),
                _set_info_netconnectd_daemon(plugin, tier, beamos_date),
                _set_info_iobeam(plugin, tier, beamos_date),
                _set_info_mrb_hw_info(plugin, tier, beamos_date),
                _config_octoprint(plugin, tier),
            ],
        )
    )
    for pack, updt_info in res.items():
        _logger.debug(
            "{} targets branch {} using pip {}".format(
                pack,
                updt_info.get("branch"),
                updt_info.get("pip_command", "~/oprint/bin/pip"),
            )
        )
    return res


def software_channels_available(plugin):
    ret = [SW_UPDATE_TIER_PROD, SW_UPDATE_TIER_BETA]
    if plugin.is_dev_env():
        # fmt: off
        ret.extend([SW_UPDATE_TIER_ALPHA, SW_UPDATE_TIER_DEV,])
        # fmt: on
    return ret


@logExceptions
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


def _config_octoprint(plugin, tier):
    prerelease_channel = None
    type = "github_release"
    if tier in [SW_UPDATE_TIER_ALPHA, SW_UPDATE_TIER_BETA]:
        prerelease_channel = "mrbeam2-{tier}"

    elif tier in [SW_UPDATE_TIER_DEV]:
        type = "github_commit"

    return _get_octo_plugin_description(
        "octoprint",
        tier,
        plugin,
        type=type,
        displayName="OctoPrint",
        prerelease=(tier in [SW_UPDATE_TIER_ALPHA, SW_UPDATE_TIER_BETA]),
        prerelease_channel=prerelease_channel,
        restart="octoprint",
        pip="https://github.com/mrbeam/OctoPrint/archive/{target_version}.zip",
    )


def _set_info_mrbeam_plugin(plugin, tier, beamos_date):
    branch = "mrbeam2-{tier}"
    return _get_octo_plugin_description(
        "mrbeam",
        tier,
        plugin,
        displayName=SORT_UP_PREFIX + "MrBeam Plugin",
        branch=branch,
        branch_default=branch,
        repo="MrBeamPlugin",
        pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
        restart="octoprint",
    )


def _set_info_mrbeamdoc(plugin, tier):
    return _get_octo_plugin_description(
        "mrbeamdoc",
        tier,
        plugin,
        displayName="Mr Beam Documentation",
        repo="MrBeamDoc",
        pip="https://github.com/mrbeam/MrBeamDoc/archive/{target_version}.zip",
        restart="octoprint",
    )


def _set_info_netconnectd_plugin(plugin, tier, beamos_date):
    branch = "mrbeam2-{tier}"
    return _get_octo_plugin_description(
        "netconnectd",
        tier,
        plugin,
        displayName="OctoPrint-Netconnectd Plugin",
        branch=branch,
        branch_default=branch,
        repo="OctoPrint-Netconnectd",
        pip="https://github.com/mrbeam/OctoPrint-Netconnectd/archive/{target_version}.zip",
        restart="octoprint",
    )


def _set_info_findmymrbeam(plugin, tier):
    return _get_octo_plugin_description(
        "findmymrbeam",
        tier,
        plugin,
        displayName="OctoPrint-FindMyMrBeam",
        repo="OctoPrint-FindMyMrBeam",
        pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
        restart="octoprint",
    )


def _set_info_mrbeamledstrips(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        pip_command = "sudo /usr/local/mrbeam_ledstrips/venv/bin/pip"
    else:
        pip_command = GLOBAL_PIP_COMMAND
    return _get_package_description_with_version(
        "mrbeam-ledstrips",
        tier,
        package_name="mrbeam-ledstrips",
        pip_command=pip_command,
        displayName="MrBeam LED Strips",
        repo="MrBeamLedStrips",
        pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
    )


def _set_info_netconnectd_daemon(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        branch = "master"
        pip_command = "sudo /usr/local/netconnectd/venv/bin/pip"
    else:
        branch = "mrbeam2-stable"
        pip_command = GLOBAL_PIP_COMMAND
    package_name = "netconnectd"
    # get_package_description does not search for package version.
    version = get_version_of_pip_module(package_name, pip_command)
    # get_package_description does not force "develop" branch.
    return _get_package_description(
        module_id="netconnectd-daemon",
        tier=tier,
        package_name=package_name,
        displayName="Netconnectd Daemon",
        displayVersion=version,
        repo="netconnectd_mrbeam",
        branch=branch,
        branch_default=branch,
        pip="https://github.com/mrbeam/netconnectd_mrbeam/archive/{target_version}.zip",
        pip_command=pip_command,
    )


def _set_info_iobeam(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        pip_command = "sudo /usr/local/iobeam/venv/bin/pip"
    else:
        pip_command = GLOBAL_PIP_COMMAND
    return _get_package_description_with_version(
        module_id="iobeam",
        tier=tier,
        package_name="iobeam",
        pip_command=pip_command,
        displayName="iobeam",
        type="bitbucket_commit",
        repo="iobeam",
        api_user="MrBeamDev",
        api_password="v2T5pFkmdgDqbFBJAqrt",
        pip="git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target_version}",
    )


def _set_info_mrb_hw_info(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        pip_command = "sudo /usr/local/iobeam/venv/bin/pip"
    else:
        pip_command = GLOBAL_PIP_COMMAND
    return _get_package_description_with_version(
        module_id="mrb_hw_info",
        tier=tier,
        package_name="mrb-hw-info",
        pip_command=pip_command,
        displayName="mrb_hw_info",
        type="bitbucket_commit",
        repo="mrb_hw_info",
        api_user="MrBeamDev",
        api_password="v2T5pFkmdgDqbFBJAqrt",
        pip="git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target_version}",
    )


@logExceptions
def _get_octo_plugin_description(module_id, tier, plugin, **kwargs):
    """Additionally get the version from plugin manager (doesn't it do that by default??)"""
    # Commented pluginInfo -> If the module is not installed, then it Should be.
    pluginInfo = plugin._plugin_manager.get_plugin_info(module_id)
    if pluginInfo is None:
        display_version = None
    else:
        display_version = pluginInfo.version
    if tier == SW_UPDATE_TIER_DEV:
        # Fix: the develop branches are not formatted as "mrbeam2-{tier}"
        _b = DEFAULT_REPO_BRANCH_ID[SW_UPDATE_TIER_DEV]
        kwargs.update(branch=_b, branch_default=_b)
    return _get_package_description(
        module_id=module_id, tier=tier, displayVersion=display_version, **kwargs
    )


@logExceptions
def _get_package_description_with_version(
    module_id, tier, package_name, pip_command, **kwargs
):
    """Additionally get the version diplayed through pip_command"""
    if tier == SW_UPDATE_TIER_DEV:
        # Fix: the develop branches are not formatted as "mrbeam2-{tier}"
        _b = DEFAULT_REPO_BRANCH_ID[SW_UPDATE_TIER_DEV]
        kwargs.update(branch=_b, branch_default=_b)

    version = get_version_of_pip_module(package_name, pip_command)
    if version:
        kwargs.update(dict(displayVersion=version))

    return _get_package_description(
        module_id=module_id, tier=tier, pip_command=pip_command, **kwargs
    )


def _get_package_description(
    module_id,
    tier,
    displayName=None,
    type="github_commit",
    user="mrbeam",
    branch="mrbeam2-{tier}",
    branch_default="mrbeam2-{tier}",
    restart="environment",
    prerelease_channel=None,
    **kwargs
):
    """Shorthand to create repo details for octoprint software update plugin to handle."""
    displayName = displayName or module_id
    if "{tier}" in branch:
        branch = branch.format(tier=get_tier_by_id(tier))
    if "{tier}" in branch_default:
        branch_default = branch_default.format(tier=get_tier_by_id(tier))
    if prerelease_channel and "{tier}" in prerelease_channel:
        kwargs.update(prerelease_channel=prerelease_channel.format(tier=get_tier_by_id(tier)))
    if tier in (SW_UPDATE_TIER_DEV, SW_UPDATE_TIER_ALPHA):
        # adds pip upgrade flag in the develop tier so it will do a upgrade even without a version bump
        kwargs.update(pip_upgrade_flag=True)
    # Disable pip colored output during software update for all tiers and updatable packages
    kwargs.update(pip_nocolor_flag=True)
    #dummy commit, to be removed before review
    update_info = dict(
        tier=tier,
        displayName=displayName,
        user=user,
        type=type,
        branch=branch,
        branch_default=branch_default,
        restart=restart,
        **kwargs
    )
    return {module_id: update_info}


def get_tier_by_id(tier):
    return DEFAULT_REPO_BRANCH_ID.get(tier, tier)


def _is_override_in_settings(plugin, module_id):
    settings_path = ["plugins", "softwareupdate", "checks", module_id, "override"]
    is_override = plugin._settings.global_get(settings_path)
    if is_override:
        _logger.info("Module %s has overriding config in settings!", module_id)
        return True
    return False
