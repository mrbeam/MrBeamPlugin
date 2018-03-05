
import time
import os.path
from octoprint_mrbeam.mrb_logger import mrb_logger



SUPPORT_STICK_FILE_PATH = '/home/pi/usb_mount/support'


USER_NAME = 'support@mr-beam.org'
USER_PW   = 'a'


_logger = mrb_logger("octoprint.plugins.mrbeam.support")



def set_support_mode(plugin):
	"""
	Enables support_mode IF support file from USB stick is present or if support_mode is enabled in dev settings
	:param plugin: MrBeam Plugin instance
	:returns True if support_mode is enabled, False otherwise
	"""
	support_mode_enabled = False
	if plugin._settings.get(['dev', 'support_mode']) or os.path.isfile(SUPPORT_STICK_FILE_PATH):
		_logger.info("SUPPORT MODE ENABLED")
		support_mode_enabled = True
	else:
		support_mode_enabled = False

	set_support_user(plugin, support_mode_enabled)

	return support_mode_enabled


def set_support_user(plugin, support_mode):
	"""
	Creates or removes a user for internal support usage or removes it.
	:param support_mode
	"""
	if support_mode:
		_logger.info("Enabling support user: %s", USER_NAME)
		plugin._user_manager.addUser(USER_NAME, USER_PW, active=True, roles=["user", "admin"], overwrite=True)
		plugin.setUserSetting(USER_NAME, plugin.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SENT_TO_CLOUD, time.time())
		plugin.setUserSetting(USER_NAME, plugin.USER_SETTINGS_KEY_LASERSAFETY_CONFIRMATION_SHOW_AGAIN, False)
	else:
		try:
			# raises UnknownUser exception if user not existing
			plugin._user_manager.removeUser(USER_NAME)
		except:
			pass



