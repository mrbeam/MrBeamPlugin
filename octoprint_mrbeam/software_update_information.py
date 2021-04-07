from datetime import datetime, date
import os, sys

from octoprint.util import dict_merge
from octoprint_mrbeam import IS_X86
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util import logExceptions
from util.pip_util import get_version_of_pip_module


SW_UPDATE_TIER_PROD = "PROD"
SW_UPDATE_TIER_BETA = "BETA"
SW_UPDATE_TIER_DEV = "DEV"
DEFAULT_REPO_BRANCH_ID = {
    SW_UPDATE_TIER_PROD: "stable",
    SW_UPDATE_TIER_BETA: "beta",
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


def get_modules():
    return sw_update_config


def get_update_information(plugin):
    result = dict()

    tier = plugin._settings.get(["dev", "software_tier"])
    beamos_tier, beamos_date = plugin._device_info.get_beamos_version()
    _logger.info("SoftwareUpdate using tier: %s", tier)

    _config_octoprint(plugin, tier)

    # The increased number of separate virtualenv for iobeam, netconnectd, ledstrips
    # will increase the "discovery time" to find those package versions.
    # "map-reduce" method can decrease lookup time by processing them in parallel
    return dict(
        reduce(
            dict_merge,
            [
                _set_info_mrbeam_plugin(plugin, tier),
                _set_info_mrbeamdoc(plugin, tier),
                _set_info_netconnectd_plugin(plugin, tier, beamos_date),
                _set_info_findmymrbeam(plugin, tier),
                _set_info_mrbeamledstrips(plugin, tier, beamos_date),
                _set_info_netconnectd_daemon(plugin, tier, beamos_date),
                _set_info_iobeam(plugin, tier, beamos_date),
                _set_info_mrb_hw_info(plugin, tier, beamos_date),
                # _set_info_rpiws281x(plugin, tier),
            ],
        )
    )


def software_channels_available(plugin):
    res = [dict(id=SW_UPDATE_TIER_PROD), dict(id=SW_UPDATE_TIER_BETA)]
    try:
        if plugin.is_dev_env():
            res.extend([dict(id=SW_UPDATE_TIER_DEV)])
    except:
        pass
    return res


def switch_software_channel(plugin, channel):
    old_channel = plugin._settings.get(["dev", "software_tier"])

    if (
        channel in (SW_UPDATE_TIER_PROD, SW_UPDATE_TIER_BETA)
        or (plugin.is_dev_env() and channel in (SW_UPDATE_TIER_DEV,))
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


def _config_octoprint(plugin, tier):
    op_swu_keys = ["plugins", "softwareupdate", "checks", "octoprint"]

    plugin._settings.global_set(op_swu_keys + ["checkout_folder"], "/home/pi/OctoPrint")
    plugin._settings.global_set(
        op_swu_keys + ["pip"],
        "https://github.com/mrbeam/OctoPrint/archive/{target_version}.zip",
    )
    plugin._settings.global_set(op_swu_keys + ["user"], "mrbeam")
    plugin._settings.global_set(
        op_swu_keys + ["stable_branch", "branch"], "mrbeam2-stable"
    )

    plugin._settings.global_set_boolean(
        op_swu_keys + ["prerelease"], tier == SW_UPDATE_TIER_DEV
    )


def _set_info_mrbeam_plugin(plugin, tier):
    return _get_octo_plugin_description(
        "mrbeam",
        tier,
        plugin,
        DisplayName=SORT_UP_PREFIX + "MrBeam Plugin",
        repo="MrBeamPlugin",
        pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
        restart="octoprint",
    )


#     name = "MrBeam Plugin"
#     module_id = "mrbeam"

#     default = dict(
#             displayName=SORT_UP_PREFIX + name,
#             displayVersion=self._plugin_version,
#             type="github_commit",  # "github_release",
#             user="mrbeam",
#             repo="MrBeamPlugin",
#             branch="mrbeam2-stable",
#             branch_default="mrbeam2-stable",
#             pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
#             restart="octoprint",
#     )
#     try:
#         if _is_override_in_settings(self, module_id):
#             return

#         if tier == SW_UPDATE_TIER_DEV:
#              return dict_merge(default, dict(
#                 branch="develop",
#                 branch_default="develop",
#             ))

#         elif tier == SW_UPDATE_TIER_BETA:
#              return dict_merge(default, dict(
#                 branch="mrbeam2-beta",
#                 branch_default="mrbeam2-beta",
#             ))
#         else: # stable
#             return default

#     except Exception as e:
#         _logger.exception("Exception during _set_info_mrbeam_plugin: {}".format(e))
#         return {}


def _set_info_mrbeamdoc(plugin, tier):
    return _get_octo_plugin_description(
        "mrbeamdoc",
        tier,
        plugin,
        DisplayName="Mr Beam Documentation",
        repo="MrBeamDoc",
        pip="https://github.com/mrbeam/MrBeamDoc/archive/{target_version}.zip",
        restart="octoprint",
    )
    # name = "Mr Beam Documentation"
    # module_id = "mrbeamdoc"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return

    #     current_version = "-"
    #     pluginInfo = self._plugin_manager.get_plugin_info(module_id)
    #     if pluginInfo is not None:
    #         current_version = pluginInfo.version

    #     default = dict(
    #         displayName=name,
    #         displayVersion=current_version,
    #         type="github_commit",  # "github_release",
    #         user="mrbeam",
    #         repo="MrBeamDoc",
    #         branch="mrbeam2-stable",
    #         branch_default="mrbeam2-stable",
    #         pip="https://github.com/mrbeam/MrBeamDoc/archive/{target_version}.zip",
    #         restart="octoprint",
    #     )

    #     if tier == SW_UPDATE_TIER_DEV:
    #         return dict_merge(default, dict(
    #             branch="develop",
    #             branch_default="develop",
    #         ))

    #     elif tier == SW_UPDATE_TIER_BETA:
    #         return dict_merge(default, dict(
    #             branch="mrbeam2-beta",
    #             branch_default="mrbeam2-beta",
    #         ))
    #     else:
    #         return default
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_mrbeamdoc: {}".format(e))
    #     return {}


def _set_info_netconnectd_plugin(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        branch = "mrbeam-buster-{tier}"
    else:
        branch = "mrbeam2-{tier}"
    return _get_octo_plugin_description(
        "netconnectd",
        tier,
        plugin,
        DisplayName="OctoPrint-Netconnectd Plugin",
        branch=branch,
        branch_default=branch,
        repo="OctoPrint-Netconnectd",
        pip="https://github.com/mrbeam/OctoPrint-Netconnectd/archive/{target_version}.zip",
        restart="octoprint",
    )
    # name = "OctoPrint-Netconnectd Plugin"
    # module_id = "netconnectd"

    # if beamos_date > BEAMOS_LEGACY_DATE:
    #     branch = "mrbeam-buster-{tier}"
    # else:
    #     branch = "mrbeam2-{tier}"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return

    #     pluginInfo = self._plugin_manager.get_plugin_info(module_id)
    #     if pluginInfo is None:
    #         return
    #     current_version = pluginInfo.version

    #     default = dict(
    #         displayName=name,
    #         displayVersion=current_version,
    #         type="github_commit",
    #         user="mrbeam",
    #         repo="OctoPrint-Netconnectd",
    #         branch=branch.format(tier="stable"),
    #         branch_default=branch.format(tier="stable"),
    #         pip="https://github.com/mrbeam/OctoPrint-Netconnectd/archive/{target_version}.zip",
    #         restart="octoprint",
    #     )

    #     if tier == SW_UPDATE_TIER_DEV:
    #         return dict_merge(default, dict(
    #             branch=branch.format(tier="develop"),
    #             branch_default=branch.format(tier="develop"),
    #         ))

    #     elif tier == SW_UPDATE_TIER_BETA:
    #         return dict_merge(default, dict(
    #             branch=branch.format(tier="beta"),
    #             branch_default=branch.format(tier="beta"),
    #         ))
    #     else:
    #         return default
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_netconnectd_plugin: {}".format(e))
    #     return {}


def _set_info_findmymrbeam(plugin, tier):
    return _get_octo_plugin_description(
        "findmymrbeam",
        tier,
        plugin,
        DisplayName="OctoPrint-FindMyMrBeam",
        repo="OctoPrint-FindMyMrBeam",
        pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
        restart="octoprint",
    )
    # name = "OctoPrint-FindMyMrBeam"
    # module_id = "findmymrbeam"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return

    #     pluginInfo = self._plugin_manager.get_plugin_info(module_id)
    #     if pluginInfo is None:
    #         return
    #     current_version = pluginInfo.version

    #     default = dict(
    #         displayName=name,
    #         displayVersion=current_version,
    #         type="github_commit",
    #         user="mrbeam",
    #         repo="OctoPrint-FindMyMrBeam",
    #         branch="mrbeam2-stable",
    #         branch_default="mrbeam2-stable",
    #         pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
    #         restart="octoprint",
    #     )

    #     if tier == SW_UPDATE_TIER_DEV:
    #         return dict_merge(default, dict(
    #             branch="develop",
    #             branch_default="develop",
    #         ))

    #     elif tier == SW_UPDATE_TIER_BETA:
    #         return dict_merge(default, dict(
    #             branch="mrbeam2-beta",
    #             branch_default="mrbeam2-beta",
    #         ))
    #     else:
    #         return default
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_findmymrbeam: {}".format(e))
    #     return {}


def _set_info_mrbeamledstrips(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        pip_command = GLOBAL_PIP_COMMAND
    else:
        pip_command = "sudo /usr/local/iobeam/venv/bin/pip"
    return _get_package_description_with_version(
        "mrbeam-ledstrips",
        tier,
        package_name="mrbeam-ledstrips",
        pip_command=pip_command,
        displayName="MrBeam LED Strips",
        repo="MrBeamLedStrips",
        pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
    )
    # name = "MrBeam LED Strips"
    # module_id = "mrbeam-ledstrips"
    # # ths module is installed outside of our virtualenv therefor we can't use default pip command.
    # # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command

    # pip_name = "mrbeam-ledstrips"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return {}

    #     # version = get_version_of_pip_module(pip_name, pip_command)
    #     # if version is None:
    #     #     return

    #     default = dict(
    #         displayName=name,
    #         # displayVersion=version,
    #         type="github_commit",  # ""github_release",
    #         user="mrbeam",
    #         repo="MrBeamLedStrips",
    #         branch="mrbeam2-stable",
    #         branch_default="mrbeam2-stable",
    #         pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
    #         pip_command=GLOBAL_PIP_COMMAND,
    #         restart="environment",
    #     )

    #     if tier == SW_UPDATE_TIER_DEV:
    #         return dict_merge(default, dict(
    #             branch="develop",
    #             branch_default="develop",
    #         ))

    #     elif tier == SW_UPDATE_TIER_BETA:
    #         return dict_merge(default, dict(
    #             branch="mrbeam2-beta",
    #             branch_default="mrbeam2-beta",
    #         ))
    #     else:
    #         return default
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_mrbeamledstrips: {}".format(e))
    #     return {}


def _set_info_netconnectd_daemon(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        branch = "mrbeam-buster"
        pip_command = GLOBAL_PIP_COMMAND
    else:
        branch = "mrbeam2-stable"
        pip_command = "sudo /usr/local/netconnectd/venv/bin/pip"
    # get_package_description does not force "develop" branch.
    return _get_package_description(
        module_id="netconnectd-daemon",
        tier=tier,
        displayName="Netconnectd Daemon",
        repo="netconnectd_mrbeam",
        branch=branch,
        branch_default=branch,
        pip="https://github.com/mrbeam/netconnectd_mrbeam/archive/{target_version}.zip",
        pip_command=pip_command,
    )
    # name = "Netconnectd Daemon"
    # module_id = "netconnectd-daemon"
    # # ths module is installed outside of our virtualenv therefor we can't use default pip command.
    # # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
    # pip_name = "netconnectd"
    # if beamos_date > BEAMOS_LEGACY_DATE:
    #     branch = "mrbeam-buster"
    #     pip_command = GLOBAL_PIP_COMMAND
    # else:
    #     branch = "mrbeam2-stable"
    #     pip_command = "/usr/local/netconnectd/venv/bin/pip"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return

    #     version = get_version_of_pip_module(pip_name, pip_command)

    #     if version is None:
    #         return

    #     return dict(
    #         displayName=name,
    #         # displayVersion=version,
    #         type="github_commit",
    #         user="mrbeam",
    #         repo="netconnectd_mrbeam",
    #         branch=branch,
    #         branch_default=branch,
    #         pip="https://github.com/mrbeam/netconnectd_mrbeam/archive/{target_version}.zip",
    #         pip_command=pip_command,
    #         restart="environment",
    #     )
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_netconnectd_daemon: {}".format(e))
    #     return {}


def _set_info_iobeam(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        pip_command = GLOBAL_PIP_COMMAND
    else:
        pip_command = "sudo /usr/local/iobeam/venv/bin/pip"
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
    # name = "iobeam"
    # module_id = "iobeam"
    # # this module is installed outside of our virtualenv therefor we can't use default pip command.
    # # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command

    # pip_name = "iobeam"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return

    #     # version = get_version_of_pip_module(pip_name, pip_command)
    #     # if version is None:
    #     #     return

    #     default = dict(
    #         displayName=name,
    #         # displayVersion=version,
    #         type="bitbucket_commit",
    #         user="mrbeam",
    #         repo="iobeam",
    #         branch="mrbeam2-stable",
    #         branch_default="mrbeam2-stable",
    #         api_user="MrBeamDev",
    #         api_password="v2T5pFkmdgDqbFBJAqrt",
    #         pip="git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target_version}",
    #         pip_command=GLOBAL_PIP_COMMAND,
    #         restart="environment",
    #     )

    #     if tier == SW_UPDATE_TIER_DEV:
    #         return dict_merge(default, dict(
    #             branch="develop",
    #             branch_default="develop",
    #         ))

    #     elif tier == SW_UPDATE_TIER_BETA:
    #         return dict_merge(default, dict(
    #             branch="mrbeam2-beta",
    #             branch_default="mrbeam2-beta",
    #         ))
    #     else:
    #         return default
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_iobeam: {}".format(e))
    #     return {}


def _set_info_mrb_hw_info(plugin, tier, beamos_date):
    if beamos_date > BEAMOS_LEGACY_DATE:
        pip_command = GLOBAL_PIP_COMMAND
    else:
        pip_command = "sudo /usr/local/iobeam/venv/bin/pip"
    return _get_package_description_with_version(
        module_id="mrb_hw_info",
        tier=tier,
        package_name="mrb_hw_info",
        pip_command=pip_command,
        displayName="mrb_hw_info",
        type="bitbucket_commit",
        repo="mrb_hw_info",
        api_user="MrBeamDev",
        api_password="v2T5pFkmdgDqbFBJAqrt",
        pip="git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target_version}",
    )
    # name = "mrb_hw_info"
    # module_id = "mrb_hw_info"
    # # this module is installed outside of our virtualenv therefor we can't use default pip command.
    # # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
    # pip_name = "mrb-hw-info"

    # try:
    #     if _is_override_in_settings(self, module_id):
    #         return

    #     # version = get_version_of_pip_module(pip_name, pip_command)
    #     # if version is None: return

    #     default = dict(
    #         displayName=name,
    #         # displayVersion=version,
    #         type="bitbucket_commit",
    #         user="mrbeam",
    #         repo="mrb_hw_info",
    #         branch="mrbeam2-stable",
    #         branch_default="mrbeam2-stable",
    #         api_user="MrBeamDev",
    #         api_password="v2T5pFkmdgDqbFBJAqrt",
    #         pip="git+ssh://git@bitbucket.org/mrbeam/mrb_hw_info.git@{target_version}",
    #         pip_command=GLOBAL_PIP_COMMAND,
    #         restart="environment",
    #     )

    #     if tier == SW_UPDATE_TIER_DEV:
    #         return dict_merge(default, dict(
    #             branch="develop",
    #             branch_default="develop",
    #         ))

    #     elif tier == SW_UPDATE_TIER_BETA:
    #         return dict_merge(default, dict(
    #             branch="mrbeam2-beta",
    #             branch_default="mrbeam2-beta",
    #         ))
    #     else:
    #         return default
    # except Exception as e:
    #     _logger.exception("Exception during _set_info_mrb_hw_info: {}".format(e))
    #     return {}


# def _set_info_rpiws281x(self, tier):
#     # NOTE: As it should now be a dependency of the mrbeam-ledstrips,
#     #       one simply needs to change the required version in setup.py
#     name = "rpi-ws281x"
#     module_id = "rpi-ws281x"
#     # this module is installed outside of our virtualenv therefor we can't use default pip command.
#     # /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
#     pip_name = module_id

#     try:
#         if _is_override_in_settings(self, module_id):
#             return

#         version = get_version_of_pip_module(pip_name, pip_command)

#         # currently only master branch exists. (June 2020)
#         # Should we want to distribute an update, just create the according branches
#         return dict(
#             displayName=name,
#             displayVersion=version,
#             type="github_commit",
#             user="mrbeam",
#             repo="rpi_ws281x_compiled",
#             branch="mrbeam2-stable",
#             branch_default="mrbeam2-stable",
#             pip="https://github.com/mrbeam/rpi_ws281x_compiled/archive/{target_version}.zip",
#             pip_command=GLOBAL_PIP_COMMAND,
#             restart="environment",
#         )

#         if tier == SW_UPDATE_TIER_DEV:
#             return dict(
#                 displayName=name,
#                 displayVersion=version,
#                 type="github_commit",
#                 user="mrbeam",
#                 repo="rpi_ws281x_compiled",
#                 branch="develop",
#                 branch_default="develop",
#                 pip="https://github.com/mrbeam/rpi_ws281x_compiled/archive/{target_version}.zip",
#                 pip_command=GLOBAL_PIP_COMMAND,
#                 restart="environment",
#             )

#         elif tier == SW_UPDATE_TIER_BETA:
#             return dict(
#                 displayName=name,
#                 displayVersion=version,
#                 type="github_commit",
#                 user="mrbeam",
#                 repo="rpi_ws281x_compiled",
#                 branch="mrbeam2-beta",
#                 branch_default="mrbeam2-beta",
#                 pip="https://github.com/mrbeam/rpi_ws281x_compiled/archive/{target_version}.zip",
#                 pip_command=GLOBAL_PIP_COMMAND,
#                 restart="environment",
#             )
#         else:
#             return default
#     except Exception as e:
#         _logger.exception("Exception during _set_info_rpiws281x: {}".format(e))
#         return {}


@logExceptions
def _get_octo_plugin_description(module_id, tier, plugin, **kwargs):
    """Additionally get the version from plugin manager (doesn't it do that by default??)"""
    # Commented pluginInfo -> If the module is not installed, then it Should be.
    pluginInfo = plugin._plugin_manager.get_plugin_info(module_id)
    # if pluginInfo is None:
    #     return {}
    if tier == SW_UPDATE_TIER_DEV:
        # Fix: the develop branches are not formatted as "mrbeam2-{tier}"
        _b = DEFAULT_REPO_BRANCH_ID[SW_UPDATE_TIER_DEV]
        kwargs.update(branch=_b, branch_default=_b)
    return _get_package_description(
        module_id=module_id, tier=tier, displayVersion=pluginInfo.version, **kwargs
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

    # TODO fix the pip module get_version -> use the pip_command from config.yaml if explicited.
    # version = get_version_of_pip_module(package_name, pip_command)
    # if version is None:
    #     return {}

    return _get_package_description(
        module_id=module_id,
        tier=tier,
        pip_command=pip_command,
        # displayVersion=pluginInfo.version,
        **kwargs
    )


def _get_package_description(
    module_id,
    tier,
    displayName=None,
    displayVersion=None,
    type="github_commit",
    user="mrbeam",
    repo=None,
    branch="mrbeam2-{tier}",
    branch_default="mrbeam2-{tier}",
    restart="environment",
    **kwargs
):
    """Shorthand to create repo details for octoprint software update plugin to handle."""
    displayName = displayName or module_id
    if "{tier}" in branch:
        branch = branch.format(tier=tier)
    if "{tier}" in branch_default:
        branch_default = branch_default.format(tier=tier)
    update_info = dict(
        tier=tier,
        displayName=displayName,
        displayVersion=displayVersion,
        user=user,
        type=type,
        repo=repo,
        branch=branch,
        branch_default=branch_default,
        restart=restart,
        **kwargs
    )
    return {module_id: update_info}


def _is_override_in_settings(plugin, module_id):
    settings_path = ["plugins", "softwareupdate", "checks", module_id, "override"]
    is_override = plugin._settings.global_get(settings_path)
    if is_override:
        _logger.info("Module %s has overriding config in settings!", module_id)
        return True
    return False
