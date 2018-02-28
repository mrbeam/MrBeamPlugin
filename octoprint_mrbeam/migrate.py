import os
import re
import shutil
import subprocess
from distutils.version import StrictVersion
from octoprint_mrbeam.mrb_logger import mrb_logger
from .profile import laserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile


def migrate(plugin):
	Migration(plugin).run()


class Migration(object):

	VERSION_SETUP_IPTABLES           = '0.1.19'
	VERSION_SYNC_GRBL_SETTINGS       = '0.1.24'

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.migrate")
		self.plugin = plugin

		self.version_previous = self.plugin._settings.get(['version'])
		self.version_current  = self.plugin._plugin_version


	def run(self):
		try:
			if not self.is_lasercutterProfile_set():
				self.set_lasercutterProfile()

			# must be done outside of is_migration_required()-block.
			self.delete_egg_dir_leftovers()

			if self.is_migration_required():
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

				# migrations end

				self.save_current_version()
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
		command = "sudo sed -i '/.*ssid: MrBeam-F930.*/c\  ssid: {}' /etc/netconnectd.yaml".format(host)
		code = self.exec_cmd(command)
		self._logger.debug("fix_wifi_ap_name() Corrected Wifi AP name.")



	##########################################################
	#####               migrations                       #####
	##########################################################

	def migrate_from_0_0_0(self):
		self._logger.info("migrate_from_0_0_0() ")
		my_profile = laserCutterProfileManager().get_default()
		# this setting was introduce with MrbeamPlugin version 0.1.13
		my_profile['laser']['intensity_factor'] = 13
		self._logger.info("migrate_from_0_0_0() Set lasercutterProfile ['laser']['intensity_factor'] = 13")
		# previous default was 300 (5min)
		my_profile['dust']['auto_mode_time'] = 60
		self._logger.info("migrate_from_0_0_0() Set lasercutterProfile ['dust']['auto_mode_time'] = 60")
		laserCutterProfileManager().save(my_profile, allow_overwrite=True, make_default=True)

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
		out, code = self._exec_cmd_output(command)
		if code != 0:
			self._logger.error("setup_iptables() Error while writing iptables conf: '%s'", out)
			return

		command = ['sudo', 'chmod', '+x', iptables_file]
		out, code = self._exec_cmd_output(command)
		if code != 0:
			self._logger.error("setup_iptables() Error while chmod iptables conf: '%s'", out)
			return

		command = ['sudo', 'bash', '-c', iptables_file]
		out, code = self._exec_cmd_output(command)
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
			elif self.plugin._device_series == '2D':
				self.set_lasercutterPorfile_2D()
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


	def set_lasercutterPorfile_2D(self):
		"""
		Not sure if first D Series devices going to be shipped with a proper lasercutterProfile installed...
		In case not, let's create it.
		:return:
		"""
		profile_id = "MrBeam2D"
		model = "D"

		if laserCutterProfileManager().exists(profile_id):
			laserCutterProfileManager().set_default(profile_id)
			self._logger.info("set_lasercutterPorfile_2D() Set lasercutterProfile '%s' as default.", profile_id)
		else:
			default_profile = laserCutterProfileManager().get_default()
			default_profile['id'] = profile_id
			default_profile['name'] = "MrBeam2"
			default_profile['model'] = model
			laserCutterProfileManager().save(default_profile, allow_overwrite=True, make_default=True)
			self._logger.info("set_lasercutterPorfile_2D() Created lasercutterProfile '%s' and set as default. Content: %s",profile_id, default_profile)


	##########################################################
	#####                 helpers                        #####
	##########################################################

	def exec_cmd(self, cmd):
		'''
		Executes a system command
		:param cmd:
		:return: True if system returncode was 0,
				 False if the command returned with an error,
				 None if there was an exception.
		'''
		code = None

		self._logger.debug("_execute_command() command: '%s'", cmd)
		try:
			code = subprocess.call(cmd, shell=True)
		except Exception as e:
			self._logger.debug("Failed to execute command '%s', return code: %s, Exception: %s", cmd, code, e)
			return None

			self._logger.debug("_execute_command() command return code: '%s'", code)
		return code == 0

	def _exec_cmd_output(self, cmd):
		'''
		Executes a system command and returns its output.
		:param cmd:
		:return: Tuple(String:output , int return_code)
				If system returncode was not 0 (zero), output will be the error message
		'''
		output = None
		code = 0
		self._logger.debug("_exec_cmd_output() command: '%s'", cmd)
		try:
			output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		except subprocess.CalledProcessError as e:
			code = e.returncode
			output = e.output
			self._logger.debug("Fail to execute command '%s', return code: %s, output: '%s'", cmd, e.returncode, e.output)

		return output, code
