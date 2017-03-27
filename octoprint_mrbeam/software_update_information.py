
import logging




def get_update_information(self):
	_logger = logging.getLogger("octoprint.plugins.mrbeam.software_update_information")

	tier = self._settings.get(["dev", "software_tier"])
	_logger.info("SoftwareUpdate using tier: %s", tier)

	result = dict()

	# mrbeam plugin
	result['mrbeam'] = dict(
		displayName="MrBeam Plugin",
		displayVersion=self._plugin_version,
		type="github_release",
		user="mrbeam",
		repo="MrBeamPlugin",
		branch="master",
		# current=self._plugin_version,
		pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")
	if tier in ["DEV"]:
		result['mrbeam'] = dict(
			displayName="MrBeam Plugin ({})".format(tier),
			displayVersion=self._plugin_version,
			type="github_commit",
			user="mrbeam",
			repo="MrBeamPlugin",
			branch="develop",
			pip="https://github.com/mrbeam/MrBeamPlugin/archive/{target_version}.zip")
	if tier in ["ANDYTEST"]:
		result['mrbeam'] = dict(
			displayName="MrBeam Plugin ({})".format(tier),
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
	result['netconnectd'] = dict(
		type="git_commit",
		checkout_folder="/home/pi/OctoPrint-Netconnectd",
		restart="octoprint",
		update_script="{folder}/update.sh")

	# netconnectd daemon:
	result['netconnectd-daemon'] = dict(
		type="git_commit",
		branch="mrbeam-stable",
		checkout_folder="/home/pi/netconnectd",
		update_script="{folder}/update.sh -b {branch}")

	# mrbeam-ledstrips:
	result['mrbeam-ledstrips'] = dict(
		displayName="MrBeam	LED",
		type="git_commit",
		checkout_folder="/home/pi/mrbeamledstrips",
		update_script="{folder}/update.sh")

	# pcf8575:
	result['pcf8575'] = dict(
		type="git_commit",
		checkout_folder="/home/pi/pcf8575",
		update_script="{folder}/update.sh")

	return result
