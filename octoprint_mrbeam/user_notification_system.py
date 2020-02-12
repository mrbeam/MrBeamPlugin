# coding=utf-8
import uuid

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

		self._stored_notifications = []
		self._stored_legacy_notifications = []


	def add_notification(self, notification_obj):
		if notification_obj.replay_when_new_client_connects:
			self._stored_notifications = notification_obj

		self._plugin_manager.send_plugin_message("mrbeam", dict(user_notification_system = dict(
			notifications=[notification_obj._get_send_obj()]
		)))

	def sync_notifications(self):
		self._plugin_manager.send_plugin_message("mrbeam", dict(user_notification_system=dict(
			notifications=[n._get_send_obj() for n in self._stored_notifications]
		)))


	def legacy_notify_frontend(self, title, text, type=None, sticky=False, delay=None, replay_when_new_client_connects=False, force=False):
		"""
		Show a frontend notification to the user. (PNotify)
		# TODO: All these messages will not be translated to any language. To change this we need:
		# TODO: - either just send an error-code to the frontend and the frontend somehow knows what texts to use
	    # TODO: - or use lazy_gettext and evaluate the resulting object here. (lazy_gettext() returns not a string but a function/object)
	    # TODO:   To do sow we need a flask request context. We could sinply keep the request context from the last request to the webpage.
	    # TODO:   This would be hacky but would work most of the time.
		:param title: title of your mesasge
		:param text: the actual text
		:param type: info, success, error, ... (default is info)
		:param sticky: True | False (default is False)
		:param delay: (int) number of seconds the notification shows until it hides (default: 10s)
		:param replay_when_new_client_connects: If True the notification will be sent to all clients when a new client connects.
				If you send the same notification (all params have identical values) it won't be sent again.
		:param force: forces to show the notification. Default is false.
		:return:
		"""
		text = text.replace("Mr Beam II", "Mr&nbsp;Beam&nbsp;II").replace("Mr Beam", "Mr&nbsp;Beam")
		notification = dict(
			title= title,
			text= text,
			type=type,
			sticky=sticky,
			delay=delay
		)

		send = True
		if replay_when_new_client_connects:
			my_hash = hash(frozenset(notification.items()))
			existing = next((item for item in self._stored_legacy_notifications if item["h"] == my_hash), None)
			if existing is None:
				notification['h'] = my_hash
				self._stored_legacy_notifications.append(notification)
			else:
				send =False

		if send or force:
			self._plugin_manager.send_plugin_message("mrbeam", dict(frontend_notification = notification))


	def _legacy_replay_stored_frontend_notification(self):
		# all currently connected clients will get this notification again
		for n in self._stored_legacy_notifications:
			self.notify_frontend(title = n['title'], text = n['text'], type= n['type'], sticky = n['sticky'], replay_when_new_client_connects=False)


class Notification(object):

	def __init__(self, id):
		self.id = id
		self.pnotify_type = None
		self.sticky = False
		self.delay = None
		self.replay_when_new_client_connects = False
		self.force = False # not sure
		self.params = {}

	def _get_send_obj(self):
		return dict(
			id=self.id,
			type=self.__class__.__name__,
			pnotify_type=self.pnotify_type,
			sticky=self.sticky,
			delay=self.delay,
			replay_when_new_client_connects=self.replay_when_new_client_connects,
			force=self.force,
			params=self.params,
		)


class LegacyNotification(Notification):

	def __init__(self, title, text):
		legacy_id = 'legacy_{}'.format(uuid.uuid4())
		Notification.__init__(self, legacy_id)
		self.params['title'] = title
		self.params['text'] = text


class ErrorNotification(Notification):

	def __init__(self, id, err_msg=[], knowledgebase_url=None):
		Notification.__init__(self, id)
		self.params['err_msg'] = err_msg
		self.params['knowledgebase_url'] = knowledgebase_url
