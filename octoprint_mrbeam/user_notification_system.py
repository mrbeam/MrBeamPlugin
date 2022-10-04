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

        self._event_bus.subscribe(
            OctoPrintEvents.CLIENT_OPENED, self.replay_notifications
        )
        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, *args, **kwargs):
        self._analytics_handler = self._plugin.analytics_handler

    @staticmethod
    def get_notification(notification_id, err_msg=[], err_code=[], replay=False):
        return dict(
            notification_id=notification_id,
            err_msg=err_msg,
            err_code=err_code,
            replay=replay,
        )

    @staticmethod
    def get_legacy_notification(title, text, err_msg=[], replay=False, is_err=False):
        res = dict(
            title=title,
            text=text,
            replay=replay,
        )
        if err_msg or is_err:
            res["type"] = "error"
            res["hide"] = False
            res["err_msg"] = err_msg
            res["replay"] = True
        return res

    def show_notifications(self, notifications):
        if not isinstance(notifications, list):
            notifications = [notifications]

        for n in notifications:
            if "notification_id" not in n:
                n["notification_id"] = "legacy_{}".format(uuid.uuid4())
            if n["replay"]:
                self._stored_notifications[n["notification_id"]] = n

        self._send(notifications)

    def replay_notifications(self, *args, **kwargs):
        if self._stored_notifications:
            self._send(list(self._stored_notifications.values()))

    def _send(self, notifications):
        self._plugin_manager.send_plugin_message(
            "mrbeam",
            dict(
                user_notification_system=dict(
                    notifications=notifications,
                )
            ),
        )

    def dismiss_notification(self, notification_id):
        """Dismisses a notification.

        Args:
            notification_id: id of the notification to dimiss

        Returns:
            None
        """
        self._logger.debug("dismiss_notification: %s", notification_id)
        self._stored_notifications.pop(notification_id, None)
