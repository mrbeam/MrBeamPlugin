# coding=utf-8
import uuid

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None
_plugin_version = None
_plugin_env = None

def user_notification_system(plugin):
	global _instance, _plugin_version, _plugin_env
	if _instance is None:
		_plugin_version = plugin.get_plugin_version()
		_plugin_env = plugin.get_env()
		_instance = UserNotificationSystem(plugin)
	return _instance


class UserNotificationSystem(object):

	def __init__(self, plugin):
		global _plugin_version, _plugin_env
		self._logger = mrb_logger("octoprint.plugins.mrbeam.user_notificatation_system")
		self._plugin = plugin
		self._plugin_manager = plugin._plugin_manager
		self._event_bus = plugin._event_bus
		self._analytics_handler = None

		self._stored_notifications = {}

		self._event_bus.subscribe(OctoPrintEvents.CLIENT_OPENED, self.replay_notifications)
		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)


	def _on_mrbeam_plugin_initialized(self, *args, **kwargs):
		self._analytics_handler = self._plugin.analytics_handler


	def show_notifications(self, notifications):
		if issubclass(type(notifications), Notification):
			notifications = [notifications]

		for n in notifications:
			if n['replay_when_new_client_connects']:
				self._stored_notifications[n['notification_id']] = n

		self._send(notifications)


	def replay_notifications(self, *args, **kwargs):
		if self._stored_notifications:
			self._send(self._stored_notifications.values())


	def _send(self, notifications):
		self._plugin_manager.send_plugin_message("mrbeam", dict(
			user_notification_system=dict(
				notifications=notifications,
			)
		))



class Notification(dict):

	def __init__(self, notification_id, **kwargs):
		"""
		Show a frontend notification to the user. (PNotify)
		!!! All notifications need templates in user_notifications_viewmodel.js !!! (except LegacyNotification)
		:param notification_id: id to identify this notification. New notifications will replace existing notifications with the same id.
		:param pnotify_type: info, success, error, ... (default is info)
		:param sticky: True | False (default is False)
		:param delay: (int) number of seconds the notification shows until it hides (default: 10s)
		:param replay_when_new_client_connects: If True the notification will be sent to all clients when a new client connects.
				If you send the same notification (all params have identical values) it won't be sent again.
		:param title: (deprecated!) title of your mesasge
		:param text: (deprecated!) the actual text
		"""
		super(Notification, self).__init__()
		self['notification_id'] = notification_id
		self['pnotify_type'] = 'info'
		self['sticky'] = False
		self['delay'] = None
		self['replay_when_new_client_connects'] = False
		self.update(kwargs)


class LegacyNotification(Notification):

	def __init__(self, title, text, **kwargs):
		legacy_id = 'legacy_{}'.format(uuid.uuid4())
		super(LegacyNotification, self).__init__(legacy_id, **kwargs)
		self['title'] = title
		self['text'] = text


class ErrorNotification(Notification):

	def __init__(self, notification_id, err_msg=[], knowledgebase_url=None, utm_campaign=None, **kwargs):
		global _plugin_version, _plugin_env
		super(ErrorNotification, self).__init__(notification_id)
		self['pnotify_type'] = 'error'
		self['sticky'] = True
		self['replay_when_new_client_connects'] = True
		self['err_msg'] = err_msg
		self['knowledgebase_showlink'] = True
		self['knowledgebase_url'] = knowledgebase_url
		self['knowledgebase_params'] = dict(
			utm_medium='beamos',
			utm_source='beamos',
			utm_campaign=utm_campaign or "notification",
			version=_plugin_version,
			env=_plugin_env,
		)
		if err_msg:
			self['knowledgebase_params']['error'] = err_msg
		self.update(kwargs)


