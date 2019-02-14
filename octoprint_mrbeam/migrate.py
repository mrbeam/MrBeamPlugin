import os
import re
import shutil
import subprocess
from distutils.version import StrictVersion
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output
from .profile import laserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile
from .comm_acc2 import MachineCom


def migrate(plugin):
	Migration(plugin).run()


class Migration(object):

	VERSION_SETUP_IPTABLES                   = '0.1.19'
	VERSION_SYNC_GRBL_SETTINGS               = '0.1.24'
	VERSION_FIX_SSH_KEY_PERMISSION           = '0.1.28'
	VERSION_UPDATE_CHANGE_HOSTNAME_SCRIPTS   = '0.1.37'
	VERSION_UPDATE_LOGROTATE_CONF            = '0.1.45'
	VERSION_GRBL_AUTO_UPDATE                 = '0.1.53'
	VERSION_INFLATE_FILE_SYSTEM              = '0.1.51'
	VERSION_MOUNT_MANAGER_160                = '0.1.55'
	VERSION_PREFILL_MRB_HW_INFO              = '0.1.55'

	# this is where we have files needed for migrations
	MIGRATE_FILES_FOLDER     = 'files/migrate/'
	MIGRATE_LOGROTATE_FOLDER = 'files/migrate_logrotate/'

	# grbl auto update conf
	GRBL_AUTO_UPDATE_FILE = "grbl_0.9g_20181116_a437781.hex"
	GRBL_AUTO_UPDATE_VERSION = MachineCom.GRBL_VERSION_20181116_a437781


	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.migrate")
		self.plugin = plugin

		self.version_previous = self.plugin._settings.get(['version']) or "0.0.0"
		self.version_current  = self.plugin._plugin_version
		self.suppress_migrations = self.plugin._settings.get(['dev', 'suppress_migrations'])


	def run(self):
		try:
			if not self.is_lasercutterProfile_set():
				self.set_lasercutterProfile()

			# must be done outside of is_migration_required()-block.
			self.delete_egg_dir_leftovers()

			if self.is_migration_required() and not self.suppress_migrations:
				self._logger.info("Starting migration from v{} to v{}".format(self.version_previous, self.version_current))

				# migrations
				if self.version_previous is None or self._compare_versions(self.version_previous, '0.1.13', equal_ok=False):
					self.migrate_from_0_0_0()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_SETUP_IPTABLES, equal_ok=False):
					self.setup_iptables()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_SYNC_GRBL_SETTINGS, equal_ok=False):
					if self.plugin._device_series == '2C':
						self.add_grbl_130_maxTravel()

				# only needed for image'PROD 2018-01-12 19:15 1515784545'
				if self.plugin.get_octopi_info() == 'PROD 2018-01-12 19:15 1515784545':
					self.fix_wifi_ap_name()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_FIX_SSH_KEY_PERMISSION, equal_ok=False):
					self.fix_ssh_key_permissions()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_UPDATE_CHANGE_HOSTNAME_SCRIPTS, equal_ok=False):
					self.update_change_hostename_apname_scripts()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_UPDATE_LOGROTATE_CONF, equal_ok=False):
					self.update_logrotate_conf()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_MOUNT_MANAGER_160, equal_ok=False):
					self.update_mount_manager()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_GRBL_AUTO_UPDATE, equal_ok=False):
					self.auto_update_grbl()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_INFLATE_FILE_SYSTEM, equal_ok=False):
					self.inflate_file_system()

				if self.version_previous is None or self._compare_versions(self.version_previous, self.VERSION_PREFILL_MRB_HW_INFO, equal_ok=False):
					self.prefill_software_update_for_mrb_hw_info()

				# migrations end

				self.save_current_version()
				self._logger.info("Finished migration from v{} to v{}.".format(self.version_previous, self.version_current))
			elif self.suppress_migrations:
				self._logger.warn("No migration done because 'suppress_migrations' is set to true in settings.")
			else:
				self._logger.debug("No migration required.")
		except:
			self._logger.exception("Unhandled exception during migration: ")


	def is_migration_required(self):
		if self.version_previous is None:
			return True
		try:
			StrictVersion(self.version_previous)
		except ValueError as e:
			self._logger.error("Previous version is invalid: '{}'. ValueError from StrictVersion: {}".format(self.version_previous, e))
			return None
		return StrictVersion(self.version_current) > StrictVersion(self.version_previous)

	def _compare_versions(self, lower_vers, higher_vers, equal_ok=True):
		"""
		Compares two versions and returns true if lower_vers < higher_vers
		:param lower_vers: needs to be inferior to higher_vers to be True
		:param lower_vers: needs to be superior to lower_vers to be True
		:param equal_ok: returned value if lower_vers and lower_vers are equal.
		:return: True or False. None if one of the version was not a valid version number
		"""
		if lower_vers is None or higher_vers is None:
			return None
		try:
			StrictVersion(lower_vers)
			StrictVersion(higher_vers)
		except ValueError as e:
			self._logger.error("_compare_versions() One of the two version is invalid: lower_vers:{}, higher_vers:{}. ValueError from StrictVersion: {}".format(lower_vers, higher_vers, e))
			return None
		if StrictVersion(lower_vers) == StrictVersion(higher_vers):
			return equal_ok
		return StrictVersion(lower_vers) < StrictVersion(higher_vers)

	def save_current_version(self):
		self.plugin._settings.set(['version'], self.version_current, force=True)



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
		site_packages_dir = '/home/pi/site-packages'
		folders = []
		keep_version = None
		if os.path.isdir(site_packages_dir):
			for f in os.listdir(site_packages_dir):
				match = re.match(r'Mr_Beam-(?P<version>[0-9.]+)[.-].+', f)
				if match:
					version = match.group('version')
					folders.append((version, f))

					if keep_version is None:
						keep_version = version
					elif self._compare_versions(keep_version, version, equal_ok=False):
						keep_version = version

			if len(folders) > 1:
				for version, folder in folders:
					if version != keep_version:
						del_dir = os.path.join(site_packages_dir, folder)
						self._logger.warn("Cleaning up old .egg dir: %s  !!! RESTART OCTOPRINT TO GET RELIABLE MRB-PLUGIN VERSION !!", del_dir)
						shutil.rmtree(del_dir)

			# Also delete an old OctoPrint folder.
			del_op_dir = os.path.join(site_packages_dir, 'OctoPrint-v1.3.5.1-py2.7.egg')
			if os.path.isdir(del_op_dir):
				self._logger.warn("Cleaning up old .egg dir: %s", del_op_dir)
				shutil.rmtree(del_op_dir)

		else:
			self._logger.error("delete_egg_dir_leftovers() Dir not existing '%s', Can't check for egg leftovers.")


	def fix_wifi_ap_name(self):
		"""
		image 'PROD 2018-01-12 19:15 1515784545' has wifi AP name: 'MrBeam-F930'
		Let's correct it to actual wifi AP name
		"""
		host = self.plugin.getHostname()
		# at some point change this to: command = "sudo /root/scripts/change_apname {}".format(host)
		# but make sure that the new change_apname script has already been installed!!! (update_change_hostename_apname_scripts)
		command = "sudo sed -i '/.*ssid: MrBeam-F930.*/c\  ssid: {}' /etc/netconnectd.yaml".format(host)
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
		if not 'laser' in my_profile or not 'intensity_factor' in my_profile['laser'] or not my_profile['laser']['intensity_factor']:
			# this setting was introduce with MrbeamPlugin version 0.1.13
			my_profile['laser']['intensity_factor'] = 13
			write = True
			self._logger.info("migrate_from_0_0_0() Set lasercutterProfile ['laser']['intensity_factor'] = 13")
		if not 'dust' in my_profile or not 'auto_mode_time' in my_profile['dust'] or not my_profile['dust']['auto_mode_time']:
			# previous default was 300 (5min)
			my_profile['dust']['auto_mode_time'] = 60
			write = True
			self._logger.info("migrate_from_0_0_0() Set lasercutterProfile ['dust']['auto_mode_time'] = 60")
		if write:
			laserCutterProfileManager().save(my_profile, allow_overwrite=True, make_default=True)
		else:
			self._logger.info("migrate_from_0_0_0() nothing to do here.")

	def setup_iptables(self):
		"""
		Creates iptables config file.
		This is required to redirect all incoming traffic to localhost.
		"""
		self._logger.info("setup_iptables() ")
		iptables_file = '/etc/network/if-up.d/iptables'
		iptables_body = """#!/bin/sh
iptables -t nat -F
# route all incoming traffic to localhost
sysctl -w net.ipv4.conf.all.route_localnet=1
iptables -t nat -I PREROUTING -p tcp --dport 80 -j DNAT --to 127.0.0.1:80
"""

		command = ['sudo', 'bash', '-c', "echo '{data}' > {file}".format(data=iptables_body, file=iptables_file)]
		out, code = exec_cmd_output(command)
		if code != 0:
			self._logger.error("setup_iptables() Error while writing iptables conf: '%s'", out)
			return

		command = ['sudo', 'chmod', '+x', iptables_file]
		out, code = exec_cmd_output(command)
		if code != 0:
			self._logger.error("setup_iptables() Error while chmod iptables conf: '%s'", out)
			return

		command = ['sudo', 'bash', '-c', iptables_file]
		out, code = exec_cmd_output(command)
		if code != 0:
			self._logger.error("setup_iptables() Error while executing iptables conf: '%s'", out)
			return

		self._logger.info("setup_iptables() Created and loaded iptables conf: '%s'", iptables_file)


	def add_grbl_130_maxTravel(self):
		"""
		Since we introduced GRBL settings sync (aka correct_settings), we have grbl settings in machine profiles
		So we need to add the old value for 'x max travel' for C-Series devices there.
		"""
		if self.plugin._device_series == '2C':
			default_profile = laserCutterProfileManager().get_default()
			default_profile['grbl']['settings'][130] = 501.1
			laserCutterProfileManager().save(default_profile, allow_overwrite=True, make_default=True)
			self._logger.info("add_grbl_130_maxTravel() C-Series Device: Added ['grbl']['settings'][130]=501.1 to lasercutterProfile: %s", default_profile)


	def update_change_hostename_apname_scripts(self):
		self._logger.info("update_change_hostename_apname_scripts() ")
		src_change_hostname = os.path.join(__package_path__, self.MIGRATE_FILES_FOLDER, 'change_hostname')
		src_change_apname = os.path.join(__package_path__, self.MIGRATE_FILES_FOLDER, 'change_apname')

		if os.path.isfile(src_change_hostname) and src_change_apname:
			exec_cmd("sudo cp {src} /root/scripts/change_hostname".format(src=src_change_hostname))
			exec_cmd("sudo chmod 755 /root/scripts/change_hostname")

			exec_cmd("sudo cp {src} /root/scripts/change_apname".format(src=src_change_apname))
			exec_cmd("sudo chmod 755 /root/scripts/change_apname")
		else:
			self._logger.error("update_change_hostename_apname_scripts() One or more source files not found! Not Updated!")


	def update_logrotate_conf(self):
		self._logger.info("update_logrotate_conf() ")

		logrotate_d_files = ['haproxy', 'iobeam', 'mount_manager', 'mrb_check', 'mrbeam_ledstrips', 'netconnectd', 'rsyslog']
		for f in logrotate_d_files:
			my_file = os.path.join(__package_path__, self.MIGRATE_LOGROTATE_FOLDER, f)
			exec_cmd("sudo cp {src} /etc/logrotate.d/".format(src=my_file))

		exec_cmd("sudo rm /var/log/*.gz")
		exec_cmd("sudo mv /etc/cron.daily/logrotate /etc/cron.hourly")
		exec_cmd("sudo logrotate /etc/logrotate.conf")
		exec_cmd("sudo service cron restart")


	def update_mount_manager(self):
		self._logger.info("update_mount_manager() ")

		mount_manager_file = os.path.join(__package_path__, self.MIGRATE_FILES_FOLDER, 'mount_manager')
		exec_cmd("sudo cp {src} /root/mount_manager/mount_manager".format(src=mount_manager_file))


	def auto_update_grbl(self):
		self._logger.info("auto_update_grbl() ")
		default_profile = laserCutterProfileManager().get_default()
		default_profile['grbl']['auto_update_version'] = self.GRBL_AUTO_UPDATE_VERSION
		default_profile['grbl']['auto_update_file'] = self.GRBL_AUTO_UPDATE_FILE
		laserCutterProfileManager().save(default_profile, allow_overwrite=True)


	def inflate_file_system(self):
		self._logger.info("inflate_file_system() ")
		exec_cmd("sudo resize2fs -p /dev/mmcblk0p2")


	def prefill_software_update_for_mrb_hw_info(self):
		from software_update_information import get_version_of_pip_module
		vers = get_version_of_pip_module("mrb-hw-info", "sudo /usr/local/bin/pip")
		if StrictVersion(vers) == StrictVersion('0.0.19'):
			self._logger.info("prefill_software_update_for_mrb_hw_info() mrb-hw-info is %s, setting commit hash", vers)
			self.plugin._settings.global_set(['plugins', 'softwareupdate', 'checks', 'mrb_hw_info', 'current'], '15dfcc2c74608adb8f07a7ea115078356f4bb09c', force=True)
		else:
			self._logger.info("prefill_software_update_for_mrb_hw_info() mrb-hw-info is %s, no changes to settings done.", vers)




	##########################################################
	#####             lasercutterProfiles                #####
	##########################################################

	def is_lasercutterProfile_set(self):
		"""
		Is a non-generic lasercutterProfile set as default profile?
		:return: True if a non-generic lasercutterProfile is set as default
		"""
		return laserCutterProfileManager().get_default()['id'] != 'my_default'


	def set_lasercutterProfile(self):
		if laserCutterProfileManager().get_default()['id'] == 'my_default':
			self._logger.info("set_lasercutterPorfile() Setting lasercutterProfile for device '%s'", self.plugin._device_series)

			if self.plugin._device_series == '2X':
				# 2X placeholder value.
				self._logger.error("set_lasercutterProfile() Can't set lasercutterProfile. device_series is %s: ", self.plugin._device_series)
				return
			elif self.plugin._device_series == '2C':
				self.set_lasercutterPorfile_2C()
			elif self.plugin._device_series in ('2D', '2E', '2F'):
				self.set_lasercutterPorfile_2DEF(series=self.plugin._device_series[1])
			else:
				self.set_lasercutterPorfile_2all()
			self.save_current_version()


	def set_lasercutterPorfile_2all(self):
		profile_id = "MrBeam{}".format(self.plugin._device_series)
		if laserCutterProfileManager().exists(profile_id):
			laserCutterProfileManager().set_default(profile_id)
			self._logger.info("set_lasercutterPorfile_2all() Set lasercutterProfile '%s' as default.", profile_id)
		else:
			self._logger.warn("set_lasercutterPorfile_2all() No lasercutterProfile '%s' found. Keep using generic profile.", profile_id)


	def set_lasercutterPorfile_2C(self):
		"""
		Series C came with no default lasercutterProfile set.
		FYI: the image contained only a profile called 'MrBeam2B' which was never used since it wasn't set as default
		"""
		profile_id = "MrBeam2C"
		model = "C"

		if laserCutterProfileManager().exists(profile_id):
			laserCutterProfileManager().set_default(profile_id)
			self._logger.info("set_lasercutterPorfile_2C() Set lasercutterProfile '%s' as default.", profile_id)
		else:
			default_profile = laserCutterProfileManager().get_default()
			default_profile['id'] = profile_id
			default_profile['name'] = "MrBeam2"
			default_profile['model'] = model
			default_profile['legacy'] = dict()
			default_profile['legacy']['job_done_home_position_x'] = 250
			default_profile['grbl']['settings'][130] = 501.1
			laserCutterProfileManager().save(default_profile, allow_overwrite=True, make_default=True)
			self._logger.info("set_lasercutterPorfile_2C() Created lasercutterProfile '%s' and set as default. Content: %s", profile_id, default_profile)


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
			self._logger.info("set_lasercutterPorfile_2DEF() Set lasercutterProfile '%s' as default.", profile_id)
		else:
			default_profile = laserCutterProfileManager().get_default()
			default_profile['id'] = profile_id
			default_profile['name'] = "MrBeam2"
			default_profile['model'] = model
			laserCutterProfileManager().save(default_profile, allow_overwrite=True, make_default=True)
			self._logger.info("set_lasercutterPorfile_2DEF() Created lasercutterProfile '%s' and set as default. Content: %s",profile_id, default_profile)


			self._logger.info("set_lasercutterPorfile_2DEF() Created lasercutterProfile '%s' and set as default. Content: %s",profile_id, default_profile)




