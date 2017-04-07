
import logging
import yaml
import os





def get_update_information(self):
	result = dict()

	tier = self._settings.get(["dev", "software_tier"])
	_logger(self).info("SoftwareUpdate using tier: %s", tier)

	# configure OctoPrint
	octoprint_configured = octoprint_checkout_folder(self, tier)

	# mrbeam plugin
	result['mrbeam'] = get_info_mrbeam_plugin(self, tier)

	# netconnectd plugin
	config_netconnectd_plugin = get_info_netconnectd_plugin(self, tier)
	if config_netconnectd_plugin is not None: result['netconnectd'] = config_netconnectd_plugin

	# findmymrbeam
	config_findmymrbeam = get_info_findmymrbeam(self, tier)
	if config_findmymrbeam is not None: result['findmymrbeam'] = config_findmymrbeam

	# mrbeam_ledstrips
	config_mrbeam_ledstrips = get_info_mrbeamledstrips(self, tier)
	if config_mrbeam_ledstrips is not None: result['mrbeam-ledstrips'] = config_mrbeam_ledstrips


	# netconnectd daemon:
	name = "Netconnectd"
	path = "/home/pi/netconnectd"
	if (os.path.isdir(path)):
		result['netconnectd-daemon'] = dict(
			displayName=_get_display_name(self, name),
			type="git_commit",
			checkout_folder=path,
			update_script="{folder}/update.sh")


	# pcf8575:
	name = "pcf8575"
	path = "/home/pi/pcf8575"
	if (os.path.isdir(path)):
		result['pcf8575'] = dict(
			displayName=_get_display_name(self, name),
			type="git_commit",
			checkout_folder=path,
			update_script="{folder}/update.sh")


	_logger(self).debug("Using config:\n%s", yaml.dump(result))

	return result

# We need octoprint's checkout_folder to be set in config.yaml
# (These's no way to set sw_update config for octoprint from the third party plugin update_hooks)
# returns True if it was already set, False otherwise
def octoprint_checkout_folder(self, tier):
	settings_path = ["plugins", "softwareupdate", "checks", "octoprint", "checkout_folder"]
	octoprint_checkout_folder = self._settings.global_get(settings_path)
	if octoprint_checkout_folder is not None:
		return True
	else:
		octoprint_checkout_folder = "/home/pi/OctoPrint"
		if os.path.isdir(octoprint_checkout_folder):
			self._settings.global_set(settings_path, octoprint_checkout_folder, force=True)
			self._settings.save(force=True)
			_logger(self).debug("config.yaml: setting octoprint_checkout_folder: %s", octoprint_checkout_folder)
		else:
			_logger(self).warning("OctoPrint octoprint_checkout_folder wasn't set because path doesnt' exist: %s ", octoprint_checkout_folder)
			return False

	test = self._settings.global_get(settings_path)
	if test is None:
		_logger(self).warning("OctoPrint octoprint_checkout_folder could not be set.")

	return False


def get_info_mrbeam_plugin(self, tier):
	name = "MrBeam Plugin"

	result = dict(
		displayName=_get_display_name(self, name),
		displayVersion=self._plugin_version,
		type="github_release",
		user="mrbeam",
		repo="MrBeamPlugin",
		branch="master",
		pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")

	if tier in ["DEV"]:
		result = dict(
			displayName=_get_display_name(self, name, tier),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="develop",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")

	if tier in ["ANDY"]:
		result = dict(
			displayName=_get_display_name(self, name, tier),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="andy_softwareupdate_test1",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")

	return result


def get_info_netconnectd_plugin(self, tier):
	name = "OctoPrint-Netconnectd Plugin"

	pluginInfo = self._plugin_manager.get_plugin_info("netconnectd")
	if pluginInfo is None:
		return None

	current_version = pluginInfo.version

	result = dict(
		displayName=_get_display_name(self, name),
		displayVersion=current_version,
		type="github_commit",
		user="mrbeam",
		repo="OctoPrint-Netconnectd",
		branch="mrbeam2-stable",
		pip="https://github.com/mrbeam/OctoPrint-Netconnectd/archive/{target_version}.zip",
		restart="octoprint")

	return result


def get_info_findmymrbeam(self, tier):
	name = "OctoPrint-FindMyMrBeam"

	pluginInfo = self._plugin_manager.get_plugin_info("findmymrbeam")

	if pluginInfo is None:
		return None

	current_version = pluginInfo.version

	result = dict(
		displayName=_get_display_name(self, name),
		displayVersion=current_version,
		type="github_commit",
		user="mrbeam",
		repo="OctoPrint-FindMyMrBeam",
		branch="mrbeam2-stable",
		pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
		restart="octoprint")

	if tier in ["DEV", "ANDY"]:
		result = dict(
			displayName=_get_display_name(self, name, tier),
			displayVersion=current_version,
			type="github_commit",
			user="mrbeam",
			repo="OctoPrint-FindMyMrBeam",
			branch="develop",
			pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
			restart="octoprint")

	return result


def get_info_mrbeamledstrips(self, tier):
	name = "MrBeam LED Strips"

	result = dict(
		displayName=_get_display_name(self, name),
		type="github_commit",
		user="mrbeam",
		repo="MrBeamLedStrips",
		branch="mrbeam2-stable",
		pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
		restart="environment")

	if tier in ["DEV", "ANDY"]:
		result = dict(
			displayName=_get_display_name(self, name),
			type="github_commit",
			user="mrbeam",
			repo="MrBeamLedStrips",
			branch="develop",
			pip="https://github.com/mrbeam/MrBeamLedStrips/archive/{target_version}.zip",
			restart="environment")

	return result



def _get_display_name(self, name, tier=None):
	if tier is not None and not tier == "PROD":
		return "{} ({})".format(name, tier)
	else:
		return name


def _logger(self):
	return logging.getLogger("octoprint.plugins.mrbeam.software_update_information")
