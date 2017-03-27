
import logging
import yaml
import os



def get_update_information(self):
	_logger = logging.getLogger("octoprint.plugins.mrbeam.software_update_information")

	tier = self._settings.get(["dev", "software_tier"])
	_logger.info("SoftwareUpdate using tier: %s", tier)

	result = dict()

	# mrbeam plugin
	result['mrbeam'] = get_info_mrbeam_plugin(self, tier)

	# netconnectd plugin
	config = get_info_netconnectd_plugin(self, tier)
	if config is not None: result['netconnectd'] = config

	# findmyoctoprint
	config = get_info_findmymrbeam(self, tier)
	if config is not None: result['findmyoctoprint'] = config


	# octoprint
	path = "/home/pi/OctoPrint"
	if (os.path.isdir(path)):
		result['octoprint'] = dict(
			checkout_folder=path,
			prerelease=True,
			prerelease_channel="rc/maintenance")


	# netconnectd daemon:
	name = "Netconnectd"
	path = "/home/pi/netconnectd"
	if (os.path.isdir(path)):
		result['netconnectd-daemon'] = dict(
			displayName=_get_display_name(self, name),
			type="git_commit",
			branch="master",
			checkout_folder=path,
			update_script="{folder}/update.sh -b {branch}")

	# mrbeam-ledstrips:
	name = "MrBeam LED"
	path = "/home/pi/mrbeamledstrips"
	if (os.path.isdir(path)):
		result['mrbeam-ledstrips'] = dict(
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

	# FindMyMrBeam


	_logger.debug("unsing config:\n%s", yaml.dump(result))

	return result


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

	if tier in ["ANDYTEST"]:
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

	pluginInfo = self._plugin_manager.get_plugin_info("findmyoctoprint")
	if pluginInfo is None:
		return None

	current_version = pluginInfo.version

	result = dict(
		displayName=_get_display_name(self, name),
		displayVersion=current_version,
		type="github_commit",
		user="mrbeam",
		repo="OctoPrint-FindMyMrBeam",
		branch="master",
		pip="https://github.com/mrbeam/OctoPrint-FindMyMrBeam/archive/{target_version}.zip",
		restart="octoprint")

	# result['netconnectd'] = dict(
	# 	displayName=_get_display_name(self, name),
	# 	type="git_commit",
	# 	checkout_folder="/home/pi/OctoPrint-Netconnectd",
	# 	restart="octoprint",
	# 	update_script="{folder}/update.sh")

	return result


def _get_display_name(self, name, tier=None):
	if tier is not None and not tier == "PROD":
		return "{} ({})".format(name, tier)
	else:
		return name


