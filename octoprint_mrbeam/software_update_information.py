
import logging
import yaml




def get_update_information(self):
	_logger = logging.getLogger("octoprint.plugins.mrbeam.software_update_information")

	tier = self._settings.get(["dev", "software_tier"])
	_logger.info("SoftwareUpdate using tier: %s", tier)

	result = dict()

	# mrbeam plugin
	name = "MrBeam Plugin"
	result['mrbeam'] = dict(
		displayName=_get_display_name(self, name, tier),
		displayVersion=self._plugin_version,
		type="github_release",
		user="mrbeam",
		repo="MrBeamPlugin",
		branch="master",
		pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")
	if tier in ["DEV"]:
		result['mrbeam'] = dict(
			displayName=_get_display_name(self, name, tier),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="develop",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")
	if tier in ["ANDYTEST"]:
		result['mrbeam'] = dict(
			displayName=_get_display_name(self, name, tier),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="andy_softwareupdate_test1",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")

	# octoprint
	result['octoprint'] = dict(
		checkout_folder="/home/pi/OctoPrint",
		prerelease=True,
		prerelease_channel="rc/maintenance")

	# OctoPrint-Netconnectd Plugin:
	name = "OctoPrint-Netconnectd Plugin"
	result['netconnectd'] = dict(
		displayName=_get_display_name(self, name),
		type="git_commit",
		checkout_folder="/home/pi/OctoPrint-Netconnectd",
		restart="octoprint",
		update_script="{folder}/update.sh")

	# netconnectd daemon:
	name = "Netconnectd"
	result['netconnectd-daemon'] = dict(
		displayName=_get_display_name(self, name),
		type="git_commit",
		branch="master",
		checkout_folder="/home/pi/netconnectd",
		update_script="{folder}/update.sh -b {branch}")

	# mrbeam-ledstrips:
	name = "MrBeam LED"
	result['mrbeam-ledstrips'] = dict(
		displayName=_get_display_name(self, name),
		type="git_commit",
		checkout_folder="/home/pi/mrbeamledstrips",
		update_script="{folder}/update.sh")

	# pcf8575:
	name = "pcf8575"
	result['pcf8575'] = dict(
		displayName=_get_display_name(self, name),
		type="git_commit",
		checkout_folder="/home/pi/pcf8575",
		update_script="{folder}/update.sh")

	# FindMyMrBeam


	_logger.debug("unsing config:\n%s", yaml.dump(result))

	return result


def _get_display_name(self, name, tier=None):
	if tier is not None and not tier == "PROD":
		return "{} ({})".format(name, tier)
	else:
		return name


