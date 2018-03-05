
import yaml
import os
import subprocess

from octoprint_mrbeam.mrb_logger import mrb_logger


SW_UPDATE_TIER_PROD =      "PROD"
SW_UPDATE_TIER_DEV =       "DEV"
SW_UPDATE_TIER_DEMO =      "DEMO"
SW_UPDATE_TIER_NO_UPDATE = "NO_UPDATE"

sw_update_config = dict()

def get_modules():
	return sw_update_config




def get_update_information(self):
	result = dict()

	tier = self._settings.get(["dev", "software_tier"])
	_logger(self).info("SoftwareUpdate using tier: %s", tier)

	if not tier in [SW_UPDATE_TIER_NO_UPDATE]:

		set_info_mrbeam_plugin(self, tier)
		set_info_netconnectd_plugin(self, tier)
		set_info_findmymrbeam(self, tier)
		set_info_mrbeamledstrips(self, tier)
		set_info_netconnectd_daemon(self, tier)
		set_info_iobeam(self, tier)
		set_info_camera_calibration(self, tier)
		set_info_rpiws281x(self, tier)
		# set_info_testplugin(self, tier) # See function definition for more details

	# _logger(self).debug("MrBeam Plugin provides this config (might be overridden by settings!):\n%s", yaml.dump(sw_update_config, width=50000).strip())
	return sw_update_config


def set_info_mrbeam_plugin(self, tier):
	name = "MrBeam Plugin"
	module_id = "mrbeam"

	if _is_override_in_settings(self, module_id): return

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=self._plugin_version,
		type="github_commit", # "github_release",
		user="mrbeam",
		repo="MrBeamPlugin",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
		restart="octoprint")

	if tier in [SW_UPDATE_TIER_DEV]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="develop",
			branch_default="develop",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
			restart="octoprint")

	if tier in [SW_UPDATE_TIER_DEMO]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="demo",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip",
			restart="octoprint")


def set_info_netconnectd_plugin(self, tier):
	name = "OctoPrint-Netconnectd Plugin"
	module_id = "netconnectd"

	if _is_override_in_settings(self, module_id): return

	pluginInfo = self._plugin_manager.get_plugin_info(module_id)
	if pluginInfo is None: return
	current_version = pluginInfo.version

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=current_version,
		type="github_commit",
		user="mrbeam",
		repo="OctoPrint-Netconnectd",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		pip="https://github.com/mrbeam/OctoPrint-Netconnectd/archive/{target_version}.zip",
		restart="octoprint")


def set_info_findmymrbeam(self, tier):
	name = "OctoPrint-FindMyMrBeam"
	module_id = "findmymrbeam"

	if _is_override_in_settings(self, module_id): return

	pluginInfo = self._plugin_manager.get_plugin_info(module_id)
	if pluginInfo is None: return
	current_version = pluginInfo.version

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=current_version,
		type="github_commit",
		user="mrbeam",
		repo="OctoPrint-FindMyMrBeam",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
		restart="octoprint")

	if tier in [SW_UPDATE_TIER_DEV]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=current_version,
			type="github_commit",
			user="mrbeam",
			repo="OctoPrint-FindMyMrBeam",
			branch="develop",
			branch_default="develop",
			pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
			restart="octoprint")


def set_info_mrbeamledstrips(self, tier):
	name = "MrBeam LED Strips"
	module_id = "mrbeam-ledstrips"
	# ths module is installed outside of our virtualenv therefor we can't use default pip command.
	# /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
	pip_command = "sudo /usr/local/bin/pip"
	pip_name = "mrbeam-ledstrips"

	if _is_override_in_settings(self, module_id): return

	version = get_version_of_pip_module(self, pip_name, pip_command)
	if version is None: return

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=version,
		type="github_commit", #""github_release",
		user="mrbeam",
		repo="MrBeamLedStrips",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
		pip_command=pip_command,
		restart="environment")

	if tier in [SW_UPDATE_TIER_DEV]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamLedStrips",
			branch="develop",
			branch_default="develop",
			pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
			pip_command=pip_command,
			restart="environment")

	if tier in [SW_UPDATE_TIER_DEMO]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamLedStrips",
			branch="demo",
			pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
			pip_command=pip_command,
			restart="environment")


def set_info_netconnectd_daemon(self, tier):
	name = "Netconnectd Daemon"
	module_id = "netconnectd-daemon"
	# ths module is installed outside of our virtualenv therefor we can't use default pip command.
	# /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
	pip_command = "sudo /usr/local/bin/pip"
	pip_name = "netconnectd"

	if _is_override_in_settings(self, module_id): return

	version = get_version_of_pip_module(self, pip_name, pip_command)
	if version is None: return

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=version,
		type="github_commit",
		user="mrbeam",
		repo="netconnectd_mrbeam",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		pip="https://github.com/mrbeam/netconnectd_mrbeam/archive/{target_version}.zip",
		pip_command=pip_command,
		restart="environment")



def set_info_iobeam(self, tier):
	name = "iobeam"
	module_id = "iobeam"
	# this module is installed outside of our virtualenv therefor we can't use default pip command.
	# /usr/local/lib/python2.7/dist-packages must be writable for pi user otherwise OctoPrint won't accept this as a valid pip command
	pip_command = "sudo /usr/local/bin/pip"
	pip_name = "iobeam"

	if _is_override_in_settings(self, module_id): return

	version = get_version_of_pip_module(self, pip_name, pip_command)
	if version is None: return

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=version,
		type="bitbucket_commit",
		user="mrbeam",
		repo="iobeam",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		api_user="MrBeamDev",
		api_password="v2T5pFkmdgDqbFBJAqrt",
		pip="git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target_version}",
		pip_command=pip_command,
		restart="environment"
	)

	if tier in [SW_UPDATE_TIER_DEV]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=version,
			type="bitbucket_commit",
			user="mrbeam",
			repo="iobeam",
			branch="develop",
			branch_default="develop",
			api_user="MrBeamDev",
			api_password="v2T5pFkmdgDqbFBJAqrt",
			pip="git+ssh://git@bitbucket.org/mrbeam/iobeam.git@{target_version}",
			pip_command=pip_command,
			restart="environment"
		)

def set_info_camera_calibration(self, tier):
	name = "mb_camera_calibration"
	module_id = "mb-camera-calibration"
	pip_name = module_id
	# hmmm... I thought, i don't need to provide a special pip command if we are in the venv...
	pip_command = "/home/pi/oprint/bin/pip"

	if _is_override_in_settings(self, module_id): return

	version = get_version_of_pip_module(self, pip_name, pip_command)
	if version is None: return

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion=version,
		type="bitbucket_commit",
		user="mrbeam",
		repo="mb_camera_calibration",
		branch="mrbeam2-stable",
		branch_default="mrbeam2-stable",
		api_user="MrBeamDev",
		api_password="v2T5pFkmdgDqbFBJAqrt",
		pip="git+ssh://git@bitbucket.org/mrbeam/mb_camera_calibration.git@{target_version}",
		restart="octoprint"
	)

	if tier in [SW_UPDATE_TIER_DEV]:
		sw_update_config[module_id] = dict(
			displayName=_get_display_name(self, name),
			displayVersion=version,
			type="bitbucket_commit",
			user="mrbeam",
			repo="mb_camera_calibration",
			branch="develop",
			branch_default="develop",
			api_user="MrBeamDev",
			api_password="v2T5pFkmdgDqbFBJAqrt",
			pip="git+ssh://git@bitbucket.org/mrbeam/mb_camera_calibration.git@{target_version}",
			restart="octoprint"
		)


def set_info_rpiws281x(self, tier):
	name = "rpi-ws281x"
	module_id = "rpi-ws281x"

	if _is_override_in_settings(self, module_id): return

	sw_update_config[module_id] = dict(
		displayName=_get_display_name(self, name),
		displayVersion="1.0",
		type="github_commit",
		user="mrbeam",
		repo="rpi_ws281x",
		branch="master",
		branch_default="master",
		update_folder="/home/pi/rpi_ws281x",
		update_script="/home/pi/rpi_ws281x/update_script.sh",
		restart="environment")

# This is a template to later allow the installation of a new octoprint plugin.
# The necesarry setup.py and plugin template is in the bitbucket repo linked below.
# def set_info_testplugin(self, tier):
# 	sw_update_config["testplugin"] = dict(
# 		displayName="Test Plugin",
# 		displayVersion="0.0.2",
# 		type="bitbucket_commit",
# 		user="mrbeam",
# 		repo="testplugin",
# 		branch="master",
# 		pip="https://bitbucket.org/mrbeam/testplugin/get/{target_version}.zip",
# 		restart="environment")

def _get_display_name(self, name):
	return name
	# if tier is not None and not tier == SW_UPDATE_TIER_PROD:
	# 	return "{} ({})".format(name, tier)
	# else:
	# 	return name


def _is_override_in_settings(self, module_id):
	settings_path = ["plugins", "softwareupdate", "checks", module_id, "override"]
	is_override = self._settings.global_get(settings_path)
	if is_override:
		_logger(self).info("Module %s has overriding config in settings!", module_id)
		return True
	return False


def get_version_of_pip_module(self, pip_name, pip_command=None):
	version = None
	if pip_command is None: pip_command = "pip"
	command = "{pip_command} freeze".format(pip_command=pip_command)
	returncode, output = _sys_command(self, command)
	if returncode == 0:
		lines = output.splitlines()
		for myLine in lines:
			token = myLine.split("==")
			if len(token) >= 2 and token[0] == pip_name:
				if token[1][:1] == "=":
					version = token[1][1:]
				else:
					version = token[1]
				break
	_logger(self).debug("get_version_of_pip_module() version of pip module '%s' is '%s' (pip command '%s' returned %s)",
						pip_name, version, pip_command, returncode)
	return version


# Executes a system command in shell-mode
def _sys_command(self, command):
	returncode = -1
	output = None
	try:
		output = subprocess.check_output(command, shell=True)
		returncode = 0
	except subprocess.CalledProcessError as e:
		output = e.output
		returncode = e.returncode
		_logger(self).warn("System command quit with error %s. Command: '%s', output: %s ", e.returncode, e.cmd, e.output)
	return (returncode, output)


def _logger(self):
	return mrb_logger("octoprint.plugins.mrbeam.software_update_information")
