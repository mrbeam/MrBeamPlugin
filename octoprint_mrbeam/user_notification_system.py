# coding=utf-8


from octoprint_mrbeam.mrb_logger import mrb_logger


# singleton
_instance = None


def userNotificationSystem(plugin):
	global _instance
	if _instance is None:
		_instance = UserNotificationSystem(plugin)
	return _instance




class UserNotificationSystem(object):

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.user_notificatation_system")
		self._plugin = plugin
		self._plugin_manager = plugin._plugin_manager
