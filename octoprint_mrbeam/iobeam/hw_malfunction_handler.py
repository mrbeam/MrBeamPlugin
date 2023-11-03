# coding=utf-8


import threading
import urllib

from flask.ext.babel import gettext

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


class HwMalfunction:
    def __init__(self, malfunction_id, msg, data, error_code=None, priority=0):
        self.id = malfunction_id
        self._msg = msg
        self.data = data
        self.priority = priority
        self.error_code = error_code

    @property
    def msg(self):
        """Returns the message to be shown to the user."""
        # if error_code is set, only show the code else show the message
        if isinstance(self.error_code, list):
            return ("{} ".format(code) for code in self.error_code)
        if self.error_code:
            return "{}".format(self.error_code)

        return self._msg

    def __str__(self):
        return "HwMalfunction(id:{id}, msg:{msg}, data:{data}, prio:{priority})".format(
            id=self.id, msg=self.msg, data=self.data, priority=self.priority
        )

    def __repr__(self):
        return self.__str__()


class HwMalfunctionHandler(object):
    MALFUNCTION_ID_BOTTOM_OPEN = "bottom_open"
    MALFUNCTION_ID_LASERHEADUNIT_MISSING = "laserheadunit_missing"
    HW_MANIPULATION = "hw_mnpltn"
    PCF_ANOMALY = "pcf_anomaly"
    FAN_NOT_SPINNING = "err_fan_not_spinning"
    EXHAUST_HOSE_BLOCKED = "exhaust_hose_blocked"
    MALFUNCTION_ID_GENERAL = "err_unknown_malfunction"
    COMPRESSOR_MALFUNCTION = "compressor_malfunction"
    ONEBUTTON_NOT_INITIALIZED = "onebtn_not_initialized"
    I2C_BUS_MALFUNCTION = "i2c_bus_malfunction"
    I2C_DEVICE_MISSING = "i2c_missing_"
    HARDWARE_MALFUNCTION_NON_I2C = "hardware_malfunction_non_i2c"
    KNOWN_MALFUNCTIONS = [
        MALFUNCTION_ID_BOTTOM_OPEN,
        MALFUNCTION_ID_LASERHEADUNIT_MISSING,
        HW_MANIPULATION,
        FAN_NOT_SPINNING,
        EXHAUST_HOSE_BLOCKED,
        MALFUNCTION_ID_GENERAL,
        COMPRESSOR_MALFUNCTION,
        ONEBUTTON_NOT_INITIALIZED,
        I2C_BUS_MALFUNCTION,
        I2C_DEVICE_MISSING,
    ]

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.hw_malfunction")
        self._plugin = plugin
        self._user_notification_system = plugin.user_notification_system
        self._event_bus = plugin._event_bus
        self._printer = plugin._printer

        self._messages_to_show = {}
        self._timer = None
        self._hardware_malfunction = False

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._iobeam_handler = self._plugin.iobeam

    def report_hw_malfunction_from_plugin(
        self, malfunction_id, msg, payload=None, error_code=None
    ):
        if not isinstance(payload, dict):
            payload = {}
        data = dict(
            msg=msg,
            payload=payload,
            code=error_code,
        )
        dataset = {malfunction_id: data}
        if not self.error_already_reported(malfunction_id):
            self.report_hw_malfunction(dataset, from_plugin=True)
        else:
            self._logger.debug("error already reported: %s", malfunction_id)

    def error_already_reported(self, malfunction_id):
        return self._messages_to_show.get(malfunction_id) is not None

    @property
    def hardware_malfunction(self):
        if not self._messages_to_show:
            self._hardware_malfunction = False
        return self._hardware_malfunction

    def report_hw_malfunction(self, dataset, from_plugin=False):
        self._hardware_malfunction = True
        self._logger.warn("hardware_malfunction: %s", dataset)
        for malfunction_id, data in dataset.items():
            data = data or {}
            msg = data.get("msg", malfunction_id)
            malfunction = HwMalfunction(
                malfunction_id,
                msg,
                data,
                error_code=data.get("code", None),
                priority=data.get("priority", 0),
            )
            self._messages_to_show[malfunction_id] = malfunction
            self._plugin.fire_event(
                MrBeamEvents.HARDWARE_MALFUNCTION,
                dict(id=malfunction_id, msg=msg, data=malfunction.data),
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
            self._messages_to_show.items(), key=lambda k: k[1].priority, reverse=True
        )

        for malfunction_id, malfunction in messages_sorted:
            if malfunction_id == self.PCF_ANOMALY:
                notifications.append(
                    self._user_notification_system.get_notification(
                        notification_id=self.HARDWARE_MALFUNCTION_NON_I2C,
                        err_code=malfunction.error_code,
                        replay=True,
                    )
                )
            elif malfunction_id and malfunction_id.startswith(self.I2C_DEVICE_MISSING):
                notifications.append(
                    self._user_notification_system.get_notification(
                        notification_id=self.I2C_BUS_MALFUNCTION,
                        err_code=malfunction.error_code,
                        replay=True,
                    )
                )
            elif malfunction_id in self.KNOWN_MALFUNCTIONS:
                notifications.append(
                    self._user_notification_system.get_notification(
                        notification_id=malfunction_id,
                        err_code=malfunction.error_code,
                        replay=True,
                    )
                )
            else:
                general_malfunctions.append(malfunction.msg)
            self._messages_to_show.pop(malfunction_id, None)

        if general_malfunctions:
            notifications.append(
                self._user_notification_system.get_notification(
                    notification_id=self.MALFUNCTION_ID_GENERAL,
                    replay=True,
                    err_msg=general_malfunctions,
                )
            )

        self._user_notification_system.show_notifications(notifications)

    def get_messages_to_show(self):
        return self._messages_to_show
