
from distutils.version import StrictVersion
from octoprint_mrbeam.mrb_logger import mrb_logger
from .profile import laserCutterProfileManager, InvalidProfileError, CouldNotOverwriteError, Profile


def migrate(plugin):
	Migration(plugin).run()


class Migration(object):


	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.migrate")
		self.plugin = plugin

		self.version_previous = self.plugin._settings.get(['version'])
		self.version_current  = self.plugin._plugin_version


	def run(self):
		if not self.is_lasercutterProfile_set(): self.set_lasercutterProfile()

		if self.is_migration_required():
			self._logger.info("Starting migration from v{} to v{}".format(self.version_previous, self.version_current))
			# if self.version_previous is None:
			# 	self.migrate_from_0_0_0() # add you migration methods here
			# migrations end
			self.save_current_version()
		else:
			self._logger.debug("No migration required.")


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


	def migrate_from_0_0_0(self):
		self._logger.warn("migrate_from_0_0_0() This is just a dummy method for demonstration. Should never show up in a real logfile.")
		# If you don't use force=True, OP will just ignore this set. (May the force be with you.)
		self.plugin._settings.global_set(['bla', 'blub'], 'just_a_test', force=True)




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

			if self.plugin._device_series == '2C':
				self.set_lasercutterPorfile_2C()
			elif self.plugin._device_series == '2D':
				self.set_lasercutterPorfile_2D()
			else:
				set_lasercutterPorfile_2all()
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



