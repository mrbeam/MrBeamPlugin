import os
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.util import RepeatedTimer


class Cpu(object):
    MESSAGES = {
        0: "Under-voltage!",
        1: "ARM frequency capped!",
        2: "Currently throttled!",
        16: "Under-voltage has occurred since last reboot.",
        17: "Throttling has occurred since last reboot.",
        18: "ARM frequency capped has occurred since last reboot.",
    }

    SAVE_TEMP_INTERVAL = 60.0

    def __init__(self, state=None, repeat=False, interval=None):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.cpu")
        self._temp = {}
        self._throttle_warnings = []
        self._progress = None
        self._state = state
        self._repeatedTimer = None
        self.interval = interval or self.SAVE_TEMP_INTERVAL

        if repeat:
            self._start_temp_recording()
        else:
            self.record_cpu_data()

    def _start_temp_recording(self):
        self._repeatedTimer = RepeatedTimer(
            self.interval, self.record_cpu_data, run_first=True
        )
        self._repeatedTimer.daemon = True
        self._repeatedTimer.start()
        self._logger.debug(
            "Start cpu temperature recording with interval %ss", self.SAVE_TEMP_INTERVAL
        )

    def _stop_temp_recording(self):
        if self._repeatedTimer is not None:
            self._repeatedTimer.cancel()
            self._repeatedTimer = None
            self._logger.debug("Stop cpu temperature recording")

    def update_progress(self, progress):
        self._progress = progress

    def _add_cpu_temp_value(self, cpu_temp):
        if cpu_temp == None:
            rounded = "None"
        else:
            rounded = str(self._round_temp_down_to(cpu_temp))
        if rounded in self._temp:
            self._temp[rounded] += 1
        else:
            self._temp[rounded] = 1

    def _add_throttle_warning(self, cpu_temp, warnings, progress):
        if warnings:
            throttle = {
                "progress": progress,
                "cpu_temp": cpu_temp,
                "warnings": warnings,
            }
            if not self._throttle_warnings:
                self._throttle_warnings.append(throttle)

            else:
                last_warnings = self._throttle_warnings[-1]
                if last_warnings["warnings"] != warnings:
                    self._throttle_warnings.append(throttle)

    def get_cpu_data(self):
        self._stop_temp_recording()
        data = {
            "temp": self._temp,
            "throttle_warnings": self._throttle_warnings,
            "state": self._state,
        }
        return data

    def _get_cpu_temp(self):
        try:
            temp = os.popen("vcgencmd measure_temp").readline()
            temp = float(temp.strip().replace("temp=", "").replace("'C", ""))
            return temp
        except:
            self._logger.exception("Exception while reading cpu temperature: ")

    def record_cpu_data(self):
        try:
            _cpu_temp = self._get_cpu_temp()
            _cpu_throttle_warnings = self.get_cpu_throttle_warnings()

            self._add_cpu_temp_value(_cpu_temp)
            self._add_throttle_warning(
                _cpu_temp, _cpu_throttle_warnings, self._progress
            )

            self._logger.debug(
                "CPU: OK - temp: %s, throttle_warnings: %s",
                _cpu_temp,
                _cpu_throttle_warnings,
            )
        except:
            self._logger.exception("Exception in record_cpu_data()")

    def get_cpu_throttle_warnings(self):
        """See this
        https://harlemsquirrel.github.io/shell/2019/01/05/monitoring-raspberry-
       pi-power-and-thermal-issues.html
        0b1010000000000000000
          1110000000000000010
          |||             |||_ under-voltage
          |||             ||_ currently throttled
          |||             |_ arm frequency capped
          |||_ under-voltage has occurred since last reboot!!
          ||_ throttling has occurred since last reboot
          |_ arm frequency capped has occurred since last reboot!!
        :return:
        """
        res = []

        t_hex = None
        try:
            t_hex = self._get_cpu_throttled()
            t_int = int(t_hex, 16)
            # if t_int == 0:
            # 	return []
            throttled_binary = bin(t_int)[2:].zfill(16)

            for position, message in self.MESSAGES.iteritems():
                # Check for the binary digits to be "on" for each warning message
                if (
                    len(throttled_binary) > position
                    and throttled_binary[0 - position - 1] == "1"
                ):
                    res.append(message)

            return res

        except:
            self._logger.error(
                "Exception in _get_cpu_throttle_warnings while converting cpu get_throttled: '%s'",
                t_hex,
            )
            return []

    def _get_cpu_throttled(self):
        try:
            tmp = os.popen("vcgencmd get_throttled").readline()
            t_hex = tmp.strip().replace("throttled=", "")
            return t_hex
        except:
            self._logger.exception(
                "Exception in _get_cpu_throttled() while reading cpu get_throttled: "
            )

    @staticmethod
    def _round_temp_down_to(cpu_temp, round_to=2):
        rounded = cpu_temp - (cpu_temp % round_to)
        return int(rounded)
