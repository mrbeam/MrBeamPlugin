
from distutils.version import StrictVersion
from octoprint_mrbeam.mrb_logger import mrb_logger


def migrate(plugin):
	Migration(plugin).run()


class Migration(object):


	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.migrate")
		self.plugin = plugin

		self.version_previous = self.plugin._settings.get(['version'])
		self.version_current  = self.plugin._plugin_version


	def run(self):
		if self.is_migration_required():
			self._logger.info("Starting migration from v{} to v{}".format(self.version_previous, self.version_current))

			# migrations go here
			if self.version_previous is None:
				self.migrate_from_0_0_1()
			# migrations end

			self.save_current_version()
		else:
			self._logger.debug("No migration required.")


	def migrate_from_0_0_1(self):
		self._logger.info("migrate_from_0_0_1() _device_series: %s", self.plugin._device_series)
		if self.plugin._device_series == '2C':
			profile = "MrBeam2C"
			self.plugin._settings.global_set(['lasercutterProfiles', 'default'], profile, force=True)
			self._logger.info("migrate_from_0_0_1(): Settings: set lasercutterProfiles default to '%s'", profile)
		elif self.plugin._device_series == '2D':
			profile = "MrBeam2D"
			self.plugin._settings.global_set(['lasercutterProfiles', 'default'], profile, force=True)
			self._logger.info("migrate_from_0_0_1(): Settings: set lasercutterProfiles default to '%s'", profile)


	def is_migration_required(self):
		if self.version_previous is None:
			return True
		try:
			StrictVersion(self.version_previous)
		except ValueError as e:
			self._logger.error("Previous version is invalid: '{}'. ValueError from StrictVersion: {}".format(self.version_previous, e))
			return None
		return StrictVersion(self.version_current) > StrictVersion(self.version_previous)


	def save_current_version(self):
		self.plugin._settings.set(['version'], self.version_current, force=True)
