
import time
import os.path
from octoprint_mrbeam.mrb_logger import mrb_logger



SUPPORT_STICK_FILE_PATH = '/home/pi/usb_mount/support'


USER_NAME = 'support@mr-beam.org'
USER_PW   = 'a'


_logger = mrb_logger("octoprint.plugins.mrbeam.support")


def set_support_user(plugin):
	"""
	Creates or removes a user for internal support usage.
	If congi.yaml allows supportuser OR a support stick (usb) is plugged in, the user will be added.
	Otherwise it will be removed.
	If activated per USB stick there's no need for our support agent to remove or disable this user.
	:param plugin: MrBeam Plugin instance
	"""
	if plugin._settings.get(['dev', 'support_user']) or os.path.isfile(SUPPORT_STICK_FILE_PATH):
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
