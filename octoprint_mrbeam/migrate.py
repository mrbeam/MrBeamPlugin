import json
from collections import Iterable, Sized, Mapping
import os
import re
import shutil
from datetime import datetime
from distutils.version import LooseVersion, StrictVersion

from enum import Enum

from octoprint_mrbeam import IS_X86, __version__
from octoprint_mrbeam.software_update_information import BEAMOS_LEGACY_DATE
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output
from octoprint_mrbeam.util import logExceptions
from octoprint_mrbeam.printing.profile import laserCutterProfileManager
from octoprint_mrbeam.printing.comm_acc2 import MachineCom
from octoprint_mrbeam.materials import materials
from octoprint_mrbeam.migration import (
    MIGRATION_STATE,
    MigrationBaseClass,
    list_of_migrations,
    MIGRATION_RESTART,
)


def migrate(plugin):
    Migration(plugin).run()


class MigrationException(Exception):
    pass


class Migration(object):
    VERSION_SETUP_IPTABLES = "0.1.19"
    VERSION_SYNC_GRBL_SETTINGS = "0.1.24"
    VERSION_FIX_SSH_KEY_PERMISSION = "0.1.28"
    VERSION_UPDATE_CHANGE_HOSTNAME_SCRIPTS = "0.1.37"
    VERSION_UPDATE_LOGROTATE_CONF = "0.8.0.2"
    VERSION_INFLATE_FILE_SYSTEM = "0.1.51"
    VERSION_PREFILL_MRB_HW_INFO = "0.1.55"
    VERSION_AVRDUDE_AUTORESET_SCRIPT = "0.2.0"
    VERSION_USERNAME_LOWCASE = "0.2.0"
    VERSION_GRBL_AUTO_UPDATE = "0.10.0"
    VERSION_MOUNT_MANAGER_172 = "0.7.13.1"
    VERSION_INITD_NETCONNECTD = "0.5.5"
    VERSION_DELETE_UPLOADED_STL_FILES = "0.6.1"
    VERSION_DISABLE_WIFI_POWER_MANAGEMENT = "0.6.13.2"
    VERSION_DISABLE_GCODE_AUTO_DELETION = "0.7.10.2"
    VERSION_UPDATE_CUSTOM_MATERIAL_SETTINGS = "0.9.9"
    VERSION_UPDATE_OCTOPRINT_PRERELEASE_FIX = "0.9.10"
    VERSION_UPDATE_FORCE_FOCUS_REMINDER = "0.10.0"

    # this is where we have files needed for migrations
    MIGRATE_FILES_FOLDER = "files/migrate/"
    MIGRATE_LOGROTATE_FOLDER = "files/migrate_logrotate/"

    # grbl auto update conf
    GRBL_AUTO_UPDATE_FILE = MachineCom.get_grbl_file_name()
    GRBL_AUTO_UPDATE_VERSION = MachineCom.GRBL_DEFAULT_VERSION

    # GRBL version that should be updated, regardless...
    GRBL_VERSIONS_NEED_UPDATE = ["0.9g_20190329_ec6a7c7-dirty"]

    # mount manager version
    MOUNT_MANAGER_VERSION = StrictVersion("1.7.2")

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.migrate")
        self.plugin = plugin

        self.version_previous = self.plugin._settings.get(["version"]) or __version__
        self.version_current = self.plugin.get_plugin_version()
        self.suppress_migrations = (
            self.plugin._settings.get(["dev", "suppress_migrations"]) or IS_X86
        )
        beamos_tier, self.beamos_date = self.plugin._device_info.get_beamos_version()
        self.beamos_version = self.plugin._device_info.get_beamos_version_number()
        self._restart = MIGRATION_RESTART.NONE

    def run(self):
        try:
            if not self.is_lasercutterProfile_set():
                self.set_lasercutterProfile()

            # must be done outside of is_migration_required()-block.
            self.delete_egg_dir_leftovers()

            if self.is_migration_required() and not self.suppress_migrations:
                self._logger.info(
                    "Starting migration from v{} to v{}".format(
                        self.version_previous, self.version_current
                    )
                )

                # migrations
                if self.version_previous is None or self._compare_versions(
                    self.version_previous, "0.1.13", equal_ok=False
                ):
                    self.migrate_from_0_0_0()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous, self.VERSION_SETUP_IPTABLES, equal_ok=False
                ):
                    self.setup_iptables()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_SYNC_GRBL_SETTINGS,
                    equal_ok=False,
                ):
                    if self.plugin._device_series == "2C":
                        self.add_grbl_130_maxTravel()

                # only needed for image'PROD 2018-01-12 19:15 1515784545'
                if self.plugin.get_octopi_info() == "PROD 2018-01-12 19:15 1515784545":
                    self.fix_wifi_ap_name()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_FIX_SSH_KEY_PERMISSION,
                    equal_ok=False,
                ):
                    self.fix_ssh_key_permissions()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_UPDATE_CHANGE_HOSTNAME_SCRIPTS,
                    equal_ok=False,
                ):
                    self.update_change_hostename_apname_scripts()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_UPDATE_LOGROTATE_CONF,
                    equal_ok=False,
                ):
                    self.update_logrotate_conf()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_MOUNT_MANAGER_172,
                    equal_ok=False,
                ):
                    self.update_mount_manager()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous, self.VERSION_GRBL_AUTO_UPDATE, equal_ok=False
                ):
                    self.auto_update_grbl()
                if (
                    self.plugin._settings.get(["grbl_version_lastknown"])
                    in self.GRBL_VERSIONS_NEED_UPDATE
                ):
                    self.auto_update_grbl()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_INFLATE_FILE_SYSTEM,
                    equal_ok=False,
                ):
                    self.inflate_file_system()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_PREFILL_MRB_HW_INFO,
                    equal_ok=False,
                ):
                    self.prefill_software_update_for_mrb_hw_info()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_AVRDUDE_AUTORESET_SCRIPT,
                    equal_ok=False,
                ):
                    self.avrdude_autoreset_script()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous, self.VERSION_USERNAME_LOWCASE, equal_ok=False
                ):
                    self.change_usernames_tolower()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_INITD_NETCONNECTD,
                    equal_ok=False,
                ):
                    self.update_etc_initd_netconnectd()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_DELETE_UPLOADED_STL_FILES,
                    equal_ok=False,
                ):
                    self.delete_uploaded_stl_files()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_DISABLE_WIFI_POWER_MANAGEMENT,
                    equal_ok=False,
                ):
                    self.disable_wifi_power_management()
                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    "0.7.7",
                    equal_ok=False,
                ):
                    self.rm_camera_calibration_repo()
                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    "0.7.9.2",
                    equal_ok=False,
                ):
                    self.fix_settings()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_DISABLE_GCODE_AUTO_DELETION,
                    equal_ok=False,
                ):
                    self.disable_gcode_auto_deletion()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    "0.9.4.0",
                    equal_ok=False,
                ):
                    self.hostname_helper_scripts()

                if (
                    self.beamos_date is not None
                    and BEAMOS_LEGACY_DATE
                    < self.beamos_date
                    <= datetime.strptime("2021-07-19", "%Y-%m-%d").date()
                    and (self.plugin._settings.get(["version"]) is None)
                ):  # for images before the 19.7.2021
                    self.fix_s_series_mount_manager()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_UPDATE_CUSTOM_MATERIAL_SETTINGS,
                    equal_ok=False,
                ):
                    self.update_custom_material_settings()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_UPDATE_FORCE_FOCUS_REMINDER,
                    equal_ok=False,
                ):
                    self.update_focus_reminder_setting()

                if self.version_previous is None or self._compare_versions(
                    self.version_previous,
                    self.VERSION_UPDATE_OCTOPRINT_PRERELEASE_FIX,
                    equal_ok=False,
                ):
                    self.fix_octoprint_prerelease_setting()

                # migrations end

                self._logger.info(
                    "Finished migration from v{} to v{}.".format(
                        self.version_previous, self.version_current
                    )
                )

            elif self.suppress_migrations:
                self._logger.warn(
                    "No migration done because 'suppress_migrations' is set to true in settings."
                )
            else:
                self._logger.info("old migration - No migration required.")

            self._run_migration()
            self.save_current_version()
        except MigrationException as e:
            self._logger.exception("Error while migration: {}".format(e))
        except Exception as e:
            self._logger.exception("Unhandled exception during migration: {}".format(e))

    def _run_migration(self):
        """
        run the new migrations
        @return:
        """
        self._logger.debug("beamos_version: {}".format(self.beamos_version))

        list_of_migrations_obj_available_to_run = [
            MigrationBaseClass.return_obj(migration, self.plugin)
            for migration in list_of_migrations
            if migration.shouldrun(migration, self.beamos_version)
        ]
        self._logger.debug(list_of_migrations_obj_available_to_run)

        if not len(list_of_migrations_obj_available_to_run):
            self._logger.info("new migration - no migration needed")
            return

        migrations_json_file_path = os.path.join(
            self.plugin._settings.getBaseFolder("base"), "migrations.json"
        )

        # if file is not there create it
        if not os.path.exists(migrations_json_file_path):
            self._logger.info("create " + migrations_json_file_path + " file")
            with open(migrations_json_file_path, "w") as f:
                json.dump({}, f)

        try:
            with open(migrations_json_file_path, "r") as f:
                try:
                    migration_executed = json.load(f)
                except ValueError:
                    raise MigrationException(
                        "couldn't read migrations json file content filepath:"
                        + migrations_json_file_path
                    )

                list_of_migrations_to_run = list(
                    list_of_migrations_obj_available_to_run
                )
                for migration in list_of_migrations_obj_available_to_run:
                    if migration.id in migration_executed:
                        if migration_executed[migration.id]:
                            list_of_migrations_to_run.remove(migration)
                        else:
                            # migration failed, should stay in execution queue and the following too
                            break

                if not len(list_of_migrations_to_run):
                    self._logger.info("new migration - all migrations already done")
                    return

                for migration in list_of_migrations_to_run:
                    migration.run()

                    # if migration sucessfull append to executed successfull
                    if migration.state == MIGRATION_STATE.migration_done:
                        migration_executed[migration.id] = True
                        if migration.restart:
                            self.restart = migration.restart
                    else:
                        # mark migration as failed and skipp the following ones
                        migration_executed[migration.id] = False
                        break

            with open(migrations_json_file_path, "w") as f:
                f.write(json.dumps(migration_executed))

            MigrationBaseClass.execute_restart(self.restart)
        except IOError:
            self._logger.error("migration execution file IO error")
        except MigrationException as e:
            self._logger.exception("error during migration {}".format(e))

    def is_migration_required(self):
        self._logger.debug(
            "beomosdate %s version %s",
            self.beamos_date,
            self.plugin._settings.get(["version"]),
        )
        if (
            self.beamos_date is not None
            and BEAMOS_LEGACY_DATE < self.beamos_date
            and (self.plugin._settings.get(["version"]) is None)
        ):  # fix migration won't run for s-series image
            return True
        if self.version_previous is None:
            return True
        try:
            LooseVersion(self.version_previous)
        except ValueError as e:
            self._logger.error(
                "Previous version is invalid: '{}'. ValueError from LooseVersion: {}".format(
                    self.version_previous, e
                )
            )
            return None
        return LooseVersion(self.version_current) > LooseVersion(self.version_previous)

    def _compare_versions(self, lower_vers, higher_vers, equal_ok=True):
        """
        Compares two versions and returns true if lower_vers < higher_vers
        :param lower_vers: needs to be inferior to higher_vers to be True
        :param lower_vers: needs to be superior to lower_vers to be True
        :param equal_ok: returned value if lower_vers and higher_vers are equal.
        :return: True or False. None if one of the version was not a valid version number
        """
        if lower_vers is None or higher_vers is None:
            return None
        try:
            LooseVersion(lower_vers)
            LooseVersion(higher_vers)
        except ValueError as e:
            self._logger.error(
                "_compare_versions() One of the two version is invalid: lower_vers:{}, higher_vers:{}. ValueError from LooseVersion: {}".format(
                    lower_vers, higher_vers, e
                )
            )
            return None
        if LooseVersion(lower_vers) == LooseVersion(higher_vers):
            return equal_ok
        return LooseVersion(lower_vers) < LooseVersion(higher_vers)

    def save_current_version(self):
        if self.plugin._settings.get(["version"]) != self.version_current:
            self.plugin._settings.set(
                ["version"], self.version_current, force=True
            )  # force needed to save it if it wasn't there
            self.plugin._settings.save()

    @property
    def restart(self):
        return self._restart

    @restart.setter
    def restart(self, value):
        if self._restart == 0 or value < self._restart:
            self._restart = value

    ##########################################################
    #####              general stuff                     #####
    ##########################################################

    def delete_egg_dir_leftovers(self):
        """
        Deletes egg files/dirs of older versions of MrBeamPlugin
        Our first mrb_check USB sticks updated MrBeamPlugin per 'pip --ignore-installed'
        which left old egg directories in site-packages.
        This then caused the plugin to assume it's version is the old version, even though the new code was executed.
        2018: Since we still see this happening, let's do this on every startup.
        Since plugin version num is not reliable if there are old egg folders,
        we must not call this from within a is_migration_needed()

        Also cleans up an old OctoPrint folder which very likely is part of the image...
        """
        site_packages_dir = "/home/pi/site-packages"
        folders = []
        keep_version = None
        if os.path.isdir(site_packages_dir):
            for f in os.listdir(site_packages_dir):
                match = re.match(r"Mr_Beam-(?P<version>[0-9.]+)[.-].+", f)
                if match:
                    version = match.group("version")
                    folders.append((version, f))

                    if keep_version is None:
                        keep_version = version
                    elif self._compare_versions(keep_version, version, equal_ok=False):
                        keep_version = version

            if len(folders) > 1:
                for version, folder in folders:
                    if version != keep_version:
                        del_dir = os.path.join(site_packages_dir, folder)
                        self._logger.warn(
                            "Cleaning up old .egg dir: %s  !!! RESTART OCTOPRINT TO GET RELIABLE MRB-PLUGIN VERSION !!",
                            del_dir,
                        )
                        shutil.rmtree(del_dir)

            # Also delete an old OctoPrint folder.
            del_op_dir = os.path.join(site_packages_dir, "OctoPrint-v1.3.5.1-py2.7.egg")
            if os.path.isdir(del_op_dir):
                self._logger.warn("Cleaning up old .egg dir: %s", del_op_dir)
                shutil.rmtree(del_op_dir)

        else:
            self._logger.error(
                "delete_egg_dir_leftovers() Dir not existing '%s', Can't check for egg leftovers."
            )

    def fix_wifi_ap_name(self):
        """
        image 'PROD 2018-01-12 19:15 1515784545' has wifi AP name: 'MrBeam-F930'
        Let's correct it to actual wifi AP name
        """
        host = self.plugin.getHostname()
        # at some point change this to: command = "sudo /root/scripts/change_apname {}".format(host)
        # but make sure that the new change_apname script has already been installed!!! (update_change_hostename_apname_scripts)
        command = "sudo sed -i '/.*ssid: MrBeam-F930.*/c\  ssid: {}' /etc/netconnectd.yaml".format(
            host
        )
        code = exec_cmd(command)
        self._logger.debug("fix_wifi_ap_name() Corrected Wifi AP name.")

    def fix_ssh_key_permissions(self):
        command = "sudo chmod 600 /root/.ssh/id_rsa"
        code = exec_cmd(command)
        self._logger.info("fix_ssh_key_permissions() Corrected permissions: %s", code)

    ##########################################################
    #####               migrations                       #####
    ##########################################################

    def migrate_from_0_0_0(self):
        self._logger.info("migrate_from_0_0_0() ")
        write = False
        my_profile = laserCutterProfileManager().get_default()
        if (
            not "laser" in my_profile
            or not "intensity_factor" in my_profile["laser"]
            or not my_profile["laser"]["intensity_factor"]
        ):
            # this setting was introduce with MrbeamPlugin version 0.1.13
            my_profile["laser"]["intensity_factor"] = 13
            write = True
            self._logger.info(
                "migrate_from_0_0_0() Set lasercutterProfile ['laser']['intensity_factor'] = 13"
            )
        if (
            not "dust" in my_profile
            or not "auto_mode_time" in my_profile["dust"]
            or not my_profile["dust"]["auto_mode_time"]
        ):
            # previous default was 300 (5min)
            my_profile["dust"]["auto_mode_time"] = 60
            write = True
            self._logger.info(
                "migrate_from_0_0_0() Set lasercutterProfile ['dust']['auto_mode_time'] = 60"
            )
        if write:
            laserCutterProfileManager().save(
                my_profile, allow_overwrite=True, make_default=True
            )
        else:
            self._logger.info("migrate_from_0_0_0() nothing to do here.")

    def setup_iptables(self):
        """
        Creates iptables config file.
        This is required to redirect all incoming traffic to localhost.
        """
        self._logger.info("setup_iptables() ")
        iptables_file = "/etc/network/if-up.d/iptables"
        iptables_body = """#!/bin/sh
iptables -t nat -F
# route all incoming traffic to localhost
sysctl -w net.ipv4.conf.all.route_localnet=1
iptables -t nat -I PREROUTING -p tcp --dport 80 -j DNAT --to 127.0.0.1:80
"""

        command = [
            "sudo",
            "bash",
            "-c",
            "echo '{data}' > {file}".format(data=iptables_body, file=iptables_file),
        ]
        out, code = exec_cmd_output(command)
        if code != 0:
            self._logger.error(
                "setup_iptables() Error while writing iptables conf: '%s'", out
            )
            return

        command = ["sudo", "chmod", "+x", iptables_file]
        out, code = exec_cmd_output(command)
        if code != 0:
            self._logger.error(
                "setup_iptables() Error while chmod iptables conf: '%s'", out
            )
            return

        command = ["sudo", "bash", "-c", iptables_file]
        out, code = exec_cmd_output(command)
        if code != 0:
            self._logger.error(
                "setup_iptables() Error while executing iptables conf: '%s'", out
            )
            return

        self._logger.info(
            "setup_iptables() Created and loaded iptables conf: '%s'", iptables_file
        )

    def add_grbl_130_maxTravel(self):
        """
        Since we introduced GRBL settings sync (aka correct_settings), we have grbl settings in machine profiles
        So we need to add the old value for 'x max travel' for C-Series devices there.
        """
        if self.plugin._device_series == "2C":
            default_profile = laserCutterProfileManager().get_default()
            default_profile["grbl"]["settings"][130] = 501.1
            laserCutterProfileManager().save(
                default_profile, allow_overwrite=True, make_default=True
            )
            self._logger.info(
                "add_grbl_130_maxTravel() C-Series Device: Added ['grbl']['settings'][130]=501.1 to lasercutterProfile: %s",
                default_profile,
            )

    def update_change_hostename_apname_scripts(self):
        self._logger.info("update_change_hostename_apname_scripts() ")
        src_change_hostname = os.path.join(
            __package_path__, self.MIGRATE_FILES_FOLDER, "change_hostname"
        )
        src_change_apname = os.path.join(
            __package_path__, self.MIGRATE_FILES_FOLDER, "change_apname"
        )

        if os.path.isfile(src_change_hostname) and src_change_apname:
            exec_cmd(
                "sudo cp {src} /root/scripts/change_hostname".format(
                    src=src_change_hostname
                )
            )
            exec_cmd("sudo chmod 755 /root/scripts/change_hostname")

            exec_cmd(
                "sudo cp {src} /root/scripts/change_apname".format(
                    src=src_change_apname
                )
            )
            exec_cmd("sudo chmod 755 /root/scripts/change_apname")
        else:
            self._logger.error(
                "update_change_hostename_apname_scripts() One or more source files not found! Not Updated!"
            )

    def update_logrotate_conf(self):
        self._logger.info("update_logrotate_conf() ")

        logrotate_d_files = [
            "analytics",
            "haproxy",
            "iobeam",
            "mount_manager",
            "mrb_check",
            "mrbeam_ledstrips",
            "netconnectd",
            "rsyslog",
        ]
        for f in logrotate_d_files:
            my_file = os.path.join(__package_path__, self.MIGRATE_LOGROTATE_FOLDER, f)
            exec_cmd("sudo cp {src} /etc/logrotate.d/".format(src=my_file))

        exec_cmd("sudo rm /var/log/*.gz")
        exec_cmd("sudo mv /etc/cron.daily/logrotate /etc/cron.hourly")
        exec_cmd("sudo logrotate /etc/logrotate.conf")
        exec_cmd("sudo service cron restart")

    def update_mount_manager(
        self,
        mount_manager_path="/root/mount_manager/mount_manager",
        mount_manager_file="mount_manager",
    ):
        self._logger.info("update_mount_manager() ")
        needs_update = True
        out, code = exec_cmd_output([mount_manager_path, "version"])
        version = None
        if code == 0:
            try:
                version = StrictVersion(out)
                needs_update = version < self.MOUNT_MANAGER_VERSION
            except:
                pass

        if needs_update:
            self._logger.debug(
                "update_mount_manager() updating mount_manager from v%s to v%s",
                version,
                self.MOUNT_MANAGER_VERSION,
            )
            mount_manager_file = os.path.join(
                __package_path__, self.MIGRATE_FILES_FOLDER, mount_manager_file
            )
            exec_cmd(
                ["sudo", "cp", str(mount_manager_file), mount_manager_path],
                shell=False,
            )
            exec_cmd(["sudo", "chmod", "745", mount_manager_path])
            exec_cmd(["sudo", "chown", "root:root", mount_manager_path])
        else:
            self._logger.debug(
                "update_mount_manager() NOT updating mount_manager, current version: v%s",
                version,
            )

    def auto_update_grbl(self):
        self._logger.info("auto_update_grbl() ")
        laserCutterProfile = laserCutterProfileManager().get_current_or_default()
        if laserCutterProfile:
            laserCutterProfile["grbl"][
                "auto_update_version"
            ] = self.GRBL_AUTO_UPDATE_VERSION
            laserCutterProfile["grbl"]["auto_update_file"] = self.GRBL_AUTO_UPDATE_FILE
            laserCutterProfileManager().save(laserCutterProfile, allow_overwrite=True)
        else:
            raise MigrationException(
                "Error while configuring grbl update - no lasercutterProfile",
            )

    def inflate_file_system(self):
        self._logger.info("inflate_file_system() ")
        exec_cmd("sudo resize2fs -p /dev/mmcblk0p2")

    def prefill_software_update_for_mrb_hw_info(self):
        from software_update_information import get_version_of_pip_module

        try:
            vers = get_version_of_pip_module("mrb-hw-info", "/usr/local/bin/pip")
            if LooseVersion(vers) == LooseVersion("0.0.19"):
                self._logger.info(
                    "prefill_software_update_for_mrb_hw_info() mrb-hw-info is %s, setting commit hash",
                    vers,
                )
                self.plugin._settings.global_set(
                    ["plugins", "softwareupdate", "checks", "mrb_hw_info", "current"],
                    "15dfcc2c74608adb8f07a7ea115078356f4bb09c",
                    force=True,
                )
            else:
                self._logger.info(
                    "prefill_software_update_for_mrb_hw_info() mrb-hw-info is %s, no changes to settings done.",
                    vers,
                )
        except Exception as e:
            self._logger.exception(
                "Exception in prefill_software_update_for_mrb_hw_info: {}".format(e)
            )

    def avrdude_autoreset_script(self):
        self._logger.info("avrdude_autoreset_script() ")
        src = os.path.join(__package_path__, self.MIGRATE_FILES_FOLDER, "autoreset")
        dst = "/usr/bin/autoreset"
        exec_cmd("sudo cp {src} {dst}".format(src=src, dst=dst))

    def change_usernames_tolower(self):
        self._logger.info("change_usernames_tolower() ")
        if not self.plugin._user_manager.hasBeenCustomized():
            self._logger.info(
                "change_usernames_tolower() _user_manager not hasBeenCustomized(): skip"
            )
            return

        users = self.plugin._user_manager._users
        self._logger.info("{numUsers} users:".format(numUsers=len(users)))

        for key, value in users.iteritems():
            username = value.get_name()

            if any(c.isupper() for c in username):
                lower_username = username.lower()
                users[lower_username] = users.pop(key)
                users[lower_username]._username = lower_username
                self._logger.info(
                    "- User {upper} changed to {lower}".format(
                        upper=username, lower=lower_username
                    )
                )
            else:
                self._logger.info("- User {user} not changed".format(user=username))

        self.plugin._user_manager._save(force=True)

    def update_etc_initd_netconnectd(self):
        self._logger.info("update_etc_initd_netconnectd() ")
        src = os.path.join(
            __package_path__, self.MIGRATE_FILES_FOLDER, "etc_initd_netconnectd"
        )
        dst = "/etc/init.d/netconnectd"
        exec_cmd("sudo cp {src} {dst}".format(src=src, dst=dst))

    def delete_uploaded_stl_files(self):
        self._logger.info("delete_uploaded_stl_files() ")
        exec_cmd("rm -f /home/pi/.octoprint/uploads/*.stl")

    def disable_wifi_power_management(self):
        self._logger.info("disable_wifi_power_management() ")
        script = os.path.join(
            __package_path__, self.MIGRATE_FILES_FOLDER, "wifi_power_management"
        )
        exec_cmd("sudo {script}".format(script=script))

    def disable_gcode_auto_deletion(self):
        # For all the old Mr Beams, we preset the value to False. Then we will ask the users if they want to change it.
        if not self.plugin.isFirstRun():
            self.plugin._settings.set_boolean(["gcodeAutoDeletion"], False)

    def fix_s_series_mount_manager(self):
        """
        fixes a problem with the images before 19.7.2021
        the rc.local file was missing the clear command for the mount_manager
        this replaces the rc.local file with the one containing this row
        """
        self._logger.info("start fix_s_series_mount_manager")
        src_rc_local = os.path.join(
            __package_path__, self.MIGRATE_FILES_FOLDER, "rc.local"
        )
        dst_rc_local = "/etc/rc.local"
        if exec_cmd("sudo cp {src} {dst}".format(src=src_rc_local, dst=dst_rc_local)):
            self._logger.info("rc.local file copied to %s", dst_rc_local)

        dst = "/etc/systemd/system"
        self._logger.info("copy files")

        systemdfiles = (
            (False, "mount_manager_remove.service"),
            (True, "mount_manager_remove_before_octo.service"),
            (False, "mount_manager_add.service"),
        )
        for enable, systemdfile in systemdfiles:
            src = os.path.join(__package_path__, self.MIGRATE_FILES_FOLDER, systemdfile)
            if (
                exec_cmd("sudo cp {src} {dst}".format(src=src, dst=dst))
                and exec_cmd("sudo systemctl daemon-reload")
                and (
                    not enable
                    or exec_cmd("sudo systemctl enable {}".format(systemdfile))
                )
            ):
                self._logger.info("successfully created ", systemdfile)

        self.update_mount_manager(
            mount_manager_path="/usr/bin/mount_manager",
            mount_manager_file="mount_manager_s_series",
        )
        src_rc_local = os.path.join(
            __package_path__, self.MIGRATE_FILES_FOLDER, "mount_manager.rules"
        )
        dst_rc_local = "/lib/udev/rules.d/00-mount_manager.rules"
        if exec_cmd("sudo cp {src} {dst}".format(src=src_rc_local, dst=dst_rc_local)):
            exec_cmd("sudo systemctl restart udev")
            self._logger.info("updated mountmanager udev rules", dst_rc_local)
            exec_cmd("sudo rm /etc/systemd/system/usb_mount_manager_add.service")
            exec_cmd("sudo rm /etc/systemd/system/usb_mount_manager_remove.service")
        self._logger.info("end fix_s_series_mount_manager")

    ##########################################################
    #####             lasercutterProfiles                #####
    ##########################################################

    def is_lasercutterProfile_set(self):
        """
        Is a non-generic lasercutterProfile set as default profile?
        :return: True if a non-generic lasercutterProfile is set as default
        """
        return laserCutterProfileManager().get_default()["id"] != "my_default"

    def set_lasercutterProfile(self):
        if laserCutterProfileManager().get_default()["id"] == "my_default":
            self._logger.info(
                "set_lasercutterPorfile() Setting lasercutterProfile for device '%s'",
                self.plugin._device_series,
            )

            if self.plugin._device_series == "2X":
                # 2X placeholder value.
                self._logger.error(
                    "set_lasercutterProfile() Can't set lasercutterProfile. device_series is %s",
                    self.plugin._device_series,
                )
                return
            elif self.plugin._device_series == "2C":
                self.set_lasercutterPorfile_2C()
            elif self.plugin._device_series in ("2D", "2E", "2F"):
                self.set_lasercutterPorfile_2DEF(series=self.plugin._device_series[1])
            else:
                self.set_lasercutterPorfile_2all()
            self.save_current_version()

    def set_lasercutterPorfile_2all(self):
        profile_id = "MrBeam{}".format(self.plugin._device_series)
        if laserCutterProfileManager().exists(profile_id):
            laserCutterProfileManager().set_default(profile_id)
            self._logger.info(
                "set_lasercutterPorfile_2all() Set lasercutterProfile '%s' as default.",
                profile_id,
            )
        else:
            self._logger.warn(
                "set_lasercutterPorfile_2all() No lasercutterProfile '%s' found. Keep using generic profile.",
                profile_id,
            )

    def set_lasercutterPorfile_2C(self):
        """
        Series C came with no default lasercutterProfile set.
        FYI: the image contained only a profile called 'MrBeam2B' which was never used since it wasn't set as default
        """
        profile_id = "MrBeam2C"
        model = "C"

        if laserCutterProfileManager().exists(profile_id):
            laserCutterProfileManager().set_default(profile_id)
            self._logger.info(
                "set_lasercutterPorfile_2C() Set lasercutterProfile '%s' as default.",
                profile_id,
            )
        else:
            default_profile = laserCutterProfileManager().get_default()
            default_profile["id"] = profile_id
            default_profile["name"] = "MrBeam2"
            default_profile["model"] = model
            default_profile["legacy"] = dict()
            default_profile["legacy"]["job_done_home_position_x"] = 250
            default_profile["grbl"]["settings"][130] = 501.1
            laserCutterProfileManager().save(
                default_profile, allow_overwrite=True, make_default=True
            )
            self._logger.info(
                "set_lasercutterPorfile_2C() Created lasercutterProfile '%s' and set as default. Content: %s",
                profile_id,
                default_profile,
            )

    def set_lasercutterPorfile_2DEF(self, series):
        """
        In case lasercutterProfile does not exist
        :return:
        """
        series = series.upper()
        profile_id = "MrBeam2{}".format(series)
        model = series

        if laserCutterProfileManager().exists(profile_id):
            laserCutterProfileManager().set_default(profile_id)
            self._logger.info(
                "set_lasercutterPorfile_2DEF() Set lasercutterProfile '%s' as default.",
                profile_id,
            )
        else:
            default_profile = laserCutterProfileManager().get_default()
            default_profile["id"] = profile_id
            default_profile["name"] = "MrBeam2"
            default_profile["model"] = model
            laserCutterProfileManager().save(
                default_profile, allow_overwrite=True, make_default=True
            )
            self._logger.info(
                "set_lasercutterPorfile_2DEF() Created lasercutterProfile '%s' and set as default. Content: %s",
                profile_id,
                default_profile,
            )

            self._logger.info(
                "set_lasercutterPorfile_2DEF() Created lasercutterProfile '%s' and set as default. Content: %s",
                profile_id,
                default_profile,
            )

    def rm_camera_calibration_repo(self):
        """Delete the legacy camera calibration and detection repo."""
        from octoprint.settings import settings

        self._logger.info("Removing mb-camera-calibration from the config file...")
        sett = settings()  # .octoprint/config.yaml
        sett.remove(
            ["plugins", "softwareupdate", "check_providers", "mb-camera-calibration"]
        )
        sett.remove(["plugins", "softwareupdate", "checks", "mb-camera-calibration"])
        sett.save()
        self._logger.info("Done")

    def fix_settings(self):
        """Sanitize the data from the settings"""

        from octoprint.settings import settings

        self._logger.info("Sanitizing the config file...")
        data = settings().get(["plugins", "mrbeam"])

        def _set(path, _data, set_func, fullpath=None):
            """
            If _data has given path, then set settings
            with that value.
            """
            if not isinstance(path, (Iterable, Sized)) or len(path) <= 0:
                return
            elif isinstance(_data, Mapping) and path[0] in _data.keys():
                if fullpath is None:
                    # for settings() you need to provide
                    # path to the plugin data as well
                    fullpath = ["plugins", "mrbeam"] + path
                value = _data[path[0]]
                if len(path) > 1:
                    _set(path[1:], value, set_func, fullpath)
                else:
                    set_func(fullpath, value)

        # ~ Do some action before saving to settings
        if "machine" in data and isinstance(data["machine"], Mapping):
            if "backlash_compensation_x" in data["machine"]:
                _val = data["machine"]["backlash_compensation_x"]
                min_mal = -1.0
                max_val = 1.0
                val = 0.0
                try:
                    val = float(_val)
                except ValueError:
                    self._logger.warning(
                        "Failed to convert %s to a float for backlash", _val
                    )
                else:
                    data["machine"]["backlash_compensation_x"] = max(
                        min(max_val, val), min_mal
                    )
                    _set(
                        ["machine", "backlash_compensation_x"],
                        data,
                        settings().setFloat,
                    )

        # ~ Sanitize data type
        float_params = (
            ["cam", "previewOpacity"],
            ["dxfScale"],
        )
        int_params = (
            ["cam", "markerRecognitionMinPixel"],
            ["svgDPI"],
            ["leds", "fps"],
            ["leds", "brightness"],
        )
        bool_params = (
            ["terminal"],
            ["terminal_show_checksums"],
            ["gcode_nextgen", "clip_working_area"],
            ["analyticsEnabled"],
            ["focusReminder"],
            ["analytics", "job_analytics"],
            ["cam", "remember_markers_across_sessions"],
        )

        for path in float_params:
            _set(path, data, settings().setFloat)
        for path in int_params:
            _set(path, data, settings().setInt)
        for path in bool_params:
            _set(path, data, settings().setBoolean)
        settings().save()
        self._logger.info("Done.")

    @logExceptions
    def hostname_helper_scripts(self):
        """
        Add systemd files and scripts to auto change the hostname on boot and/or
        change of name in /etc/mrbeam
        """
        self._logger.info("Removing previous first_boot_script...")
        for rm_fname in [
            "/root/scripts/change_hostname",
            "/root/scripts/change_apname",
            "/root/scripts/change_etc_mrbeam",
            "/etc/init.d/first_boot_script",
        ]:
            # permission...
            os.system("sudo rm '%s'" % rm_fname)
            # os.remove(rm_fname)
        self._logger.info("Adding hostname helper scripts...")
        for fname in [
            "/usr/bin/beamos_hostname",
            "/usr/bin/beamos_serial",
            "/etc/init.d/beamos_first_boot",
        ]:
            src = os.path.join(
                os.path.dirname(__file__),
                self.MIGRATE_FILES_FOLDER,
                os.path.basename(fname),
            )
            # permission...
            os.system("sudo mv '%s' '%s'" % (src, fname))
            # os.renames(src, fname)

    def update_custom_material_settings(self):
        """
        Updates custom material settings keys and values
        It replaces 'laser_type 'key with 'laser_model' and
        it sets the value according to the latest laserhead
        model updates
        It also replaces 'model' key with 'device_model'
        """
        self._logger.info("start update_custom_material_settings")
        my_materials = materials(self.plugin)
        for k, v in my_materials.get_custom_materials().items():
            my_materials.put_custom_material(k, v)

    def fix_octoprint_prerelease_setting(self):
        """
        Removes the prerelease flag from the OctoPrint update
        config so it will only use releases of OctoPrint
        """
        self._logger.info("start fix_octoprint_prerelease_setting")
        self.plugin._settings.global_set(
            ["plugins", "softwareupdate", "checks", "octoprint", "prerelease"],
            False,
            force=True,
        )
        self.plugin._settings.save()

    def update_focus_reminder_setting(self):
        """
        Updates the 'focusReminder' flag in settings
        Enforce the flag to True so the user can see
        the laser head removal warning at least once
        """
        self._logger.info("start update_focus_reminder_setting")
        self.plugin._settings.set_boolean(["focusReminder"], True)
        self.plugin._settings.save()
