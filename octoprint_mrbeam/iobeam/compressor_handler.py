# coding=utf-8

import threading
import time
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents, IoBeamValueEvents
from octoprint_mrbeam.mrb_logger import mrb_logger


# singleton
_instance = None


def compressor_handler(plugin):
    global _instance
    if _instance is None:
        _instance = CompressorHandler(plugin)
    return _instance


class CompressorHandler(object):

    COMPRESSOR_MIN = 0
    COMPRESSOR_MAX = 100

    MAX_TIMES_RPM_0 = 5

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.compressorhandler")
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._printer = plugin._printer

        self._iobeam = None
        self._analytics_handler = None

        self._compressor_current_state = -1
        self._compressor_nominal_state = 0
        self._compressor_present = False

        self._last_dynamic_data = {}

        self._num_rpm_0 = 0

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._iobeam = self._plugin.iobeam
        self._analytics_handler = self._plugin.analytics_handler
        self._hw_malfunction_handler = self._plugin.hw_malfunction_handler

        self._subscribe()

    def _subscribe(self):
        self._iobeam.subscribe(
            IoBeamValueEvents.COMPRESSOR_STATIC, self._handle_static_data
        )
        self._iobeam.subscribe(
            IoBeamValueEvents.COMPRESSOR_DYNAMIC, self._handle_dynamic_data
        )

        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_STARTED, self.set_compressor_job_start
        )

        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_DONE, self.set_compressor_job_end
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_FAILED, self.set_compressor_job_end
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_CANCELLED, self.set_compressor_job_end
        )
        self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.set_compressor_job_end)

        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_PAUSED, self.set_compressor_pause
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_RESUMED, self.set_compressor_unpause
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING, self._on_high_temperature_warning
        )

    def has_compressor(self):
        return self._plugin._device_info.is_mrbeam2_dc_series()

    def get_current_state(self):
        if self.has_compressor():
            return self._compressor_current_state
        else:
            return None

    def set_compressor(self, value, set_nominal_value=True, msg=""):
        if self.has_compressor():
            self._logger.info(
                "Compressor set to %s %s (nominal state before: %s, real state: %s)",
                value,
                msg,
                self._compressor_nominal_state,
                self._compressor_current_state,
            )
            if value > self.COMPRESSOR_MAX:
                value = self.COMPRESSOR_MAX
            if value < self.COMPRESSOR_MIN:
                value = self.COMPRESSOR_MIN
            if set_nominal_value:
                self._compressor_nominal_state = value
            self._iobeam.send_compressor_command(value)

    def set_compressor_job_start(self, event, *args, **kwargs):
        self.set_compressor(self.COMPRESSOR_MAX, msg=event)

    def set_compressor_job_end(self, event, *args, **kwargs):
        self.set_compressor(self.COMPRESSOR_MIN, msg=event)

    def set_compressor_off(self):
        self.set_compressor(self.COMPRESSOR_MIN)

    def set_compressor_pause(self, *args, **kwargs):
        self.set_compressor(self.COMPRESSOR_MIN, set_nominal_value=False)

    def set_compressor_unpause(self, *args, **kwargs):
        self.set_compressor(self._compressor_nominal_state)

    def resend_compressor(self):
        self.set_compressor(self._compressor_nominal_state, set_nominal_value=False)

    def _handle_static_data(self, payload):
        dataset = payload.get("message", {})
        if dataset:
            self._add_static_data_analytics(dataset)
            if "version" in dataset:
                self._compressor_present = True
                self._logger.info("Enabling compressor. compressor_static: %s", dataset)
            else:
                self._logger.warn(
                    "Received compressor_static dataset without version information: compressor_static: %s",
                    dataset,
                )
        else:
            # If the dataset is empty but we know there is a compressor, something is wrong
            if self.has_compressor():
                self._hw_malfunction_handler.report_hw_malfunction_from_plugin(
                    malfunction_id="compressor", msg="no_compressor_static_data"
                )

    def _handle_dynamic_data(self, payload):
        dataset = payload.get("message", {})
        if dataset:
            self._last_dynamic_data = dataset
            if "state" in dataset:
                try:
                    self._compressor_current_state = int(dataset["state"])
                except:
                    self._logger.exception(
                        "Cant convert compressor state to int from compressor_dynamic: %s",
                        dataset,
                    )

            if "rpm_actual" in dataset and self._printer.is_printing():
                if dataset["rpm_actual"] == 0:
                    self._num_rpm_0 += 1
                    if self._num_rpm_0 >= self.MAX_TIMES_RPM_0:
                        self._logger.error(
                            "Compressor zero rpm value! Max tries reached, throwing HARDWARE MALFUNCTION, turning off compressor. (current real state: %s, zero-rpm-count %s)",
                            self._compressor_current_state,
                            self._num_rpm_0,
                        )
                        # avoid overheating an potential further damage
                        self.set_compressor_off()
                        self._hw_malfunction_handler.report_hw_malfunction_from_plugin(
                            malfunction_id="compressor", msg="compressor_rpm_0"
                        )
                    else:
                        self.resend_compressor()
                        self._logger.warn(
                            "Compressor zero rpm value! Resending nominal state: %s, current real state: %s, zero-rpm-count %s",
                            self._compressor_nominal_state,
                            self._compressor_current_state,
                            self._num_rpm_0,
                        )
                else:
                    self._num_rpm_0 = 0
        else:
            # If the dataset is empty but we know there is a compressor, something is wrong
            if self.has_compressor():
                self._hw_malfunction_handler.report_hw_malfunction_from_plugin(
                    malfunction_id="compressor", msg="no_compressor_dynamic_data"
                )

    def _add_static_data_analytics(self, data):
        data = dict(
            check=data.get("compressor_check", None),
            error_msg=data.get("error", {}).get("msg", None),
            error_id=data.get("error", {}).get("id", None),
        )

        self._analytics_handler.add_compressor_data(data)

    def get_compressor_data(self):
        data = dict(
            voltage=self._last_dynamic_data.get("voltage", None),
            current=self._last_dynamic_data.get("current", None),
            rpm=self._last_dynamic_data.get("rpm_actual", None),
            pressure=self._last_dynamic_data.get("press_actual", None),
            state=self._compressor_nominal_state,
            mode_name=self._last_dynamic_data.get("mode_name", None),
        )

        return data

    def _on_high_temperature_warning(self, event, payload):
        self._logger.info("High temperature Warning triggered, turning off compressor")
        self.set_compressor_off()
