# coding=utf-8


import threading
import urllib

from flask_babel import gettext

from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None


def hwMalfunctionHandler(plugin):
    global _instance
    if _instance is None:
        _instance = HwMalfunctionHandler(plugin)
    return _instance


class HwMalfunctionHandler(object):
    MALFUNCTION_ID_BOTTOM_OPEN = "bottom_open"
    MALFUNCTION_ID_LASERHEADUNIT_MISSING = "laserheadunit_missing"
    MALFUNCTION_ID_GENERAL = "hw_malfunction"

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.hw_malfunction")
        self._plugin = plugin
        self._user_notification_system = plugin.user_notification_system
        self._event_bus = plugin._event_bus
        self._printer = plugin._printer

        self._messages_to_show = {}
        self._timer = None
        self.hardware_malfunction = False

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._iobeam_handler = self._plugin.iobeam

    def report_hw_malfunction_from_plugin(self, malfunction_id, msg, payload=None):
        if not isinstance(payload, dict):
            payload = {}
        data = dict(
            msg=msg,
            payload=payload,
        )
        dataset = {malfunction_id: data}

        self.report_hw_malfunction(dataset, from_plugin=True)

    def report_hw_malfunction(self, dataset, from_plugin=False):
        self.hardware_malfunction = True
        self._logger.warn("hardware_malfunction: %s", dataset)
        for malfunction_id, data in dataset.items():
            data = data or {}
            msg = data.get("msg", malfunction_id)
            data["msg"] = msg
            data["priority"] = data.get("priority", 0)
            self._messages_to_show[malfunction_id] = data
            self._plugin.fire_event(
                MrBeamEvents.HARDWARE_MALFUNCTION,
                dict(id=malfunction_id, msg=msg, data=data),
            )

        dataset.update({"from_plugin": from_plugin})
        self._iobeam_handler.send_iobeam_analytics(
            eventname="hw_malfunction",
            data=dataset,
        )

        self._start_notification_timer()

    def _start_notification_timer(self):
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(1.0, self.show_hw_malfunction_notification)
        self._timer.start()

    def show_hw_malfunction_notification(self):
        notifications = []
        general_malfunctions = []
        messages_sorted = sorted(
            self._messages_to_show.items(), key=lambda k: k[1]["priority"], reverse=True
        )

        for malfunction_id, data in messages_sorted:
            if malfunction_id == self.MALFUNCTION_ID_BOTTOM_OPEN:
                notifications.append(
                    self._user_notification_system.get_notification(
                        notification_id="err_bottom_open", replay=True
                    )
                )
            elif malfunction_id == self.MALFUNCTION_ID_LASERHEADUNIT_MISSING:
                notifications.append(
                    self._user_notification_system.get_notification(
                        notification_id="err_leaserheadunit_missing",
                        err_msg=data.get("msg", None),
                        replay=True,
                    )
                )
            else:
                general_malfunctions.append(data.get("msg", None))

        if general_malfunctions:
            notifications.append(
                self._user_notification_system.get_notification(
                    notification_id="err_hardware_malfunction",
                    replay=True,
                    err_msg=general_malfunctions,
                )
            )

        self._user_notification_system.show_notifications(notifications)

    def get_messages_to_show(self):
        return self._messages_to_show
