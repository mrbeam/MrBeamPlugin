# coding=utf-8

import os
import collections
import time
import datetime
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.util import RepeatedTimer



class AccWatchDog(object):

	DEFAULT_COMMAND_NUM = 10
	DEFAULT_WATCH_INTERVAL = 60.0

	CPU_TEMP_THRESHOLD = 60.0

	def __init__(self, comm_acc2, interval=None, command_num=None):
		self.interval = interval or self.DEFAULT_WATCH_INTERVAL
		self.command_num = command_num or self.DEFAULT_COMMAND_NUM

		self._logger = mrb_logger("octoprint.plugins.mrbeam.printing.acc_watch_dog")
		self._comm_acc2 = comm_acc2
		self._currentFile = None
		self._repeatedTimer = None
		self._commands = collections.deque(maxlen=self.command_num)
		self._cmd_counter = 0
		self._cpu_temp = self._get_cpu_temp()
		self._cpu_throttle_warnings = self._get_cpu_throttle_warnings()

		self._do_regular_check()

	def start(self, current_file=None):
		self.stop()
		self._cmd_counter = 0
		if current_file:
			self._currentFile = current_file
		self._repeatedTimer = RepeatedTimer(self.interval, self._do_regular_check, run_first=True)
		self._repeatedTimer.daemon = True
		self._repeatedTimer.start()
		self._logger.debug("Start with interval %ss", self.interval)

	def stop(self):
		if self._repeatedTimer is not None:
			self._repeatedTimer.cancel()
			self._repeatedTimer = None
			self._logger.debug("Stop")

	def reset(self):
		self._logger.debug("Reset")
		self._cmd_counter = 0
		self._commands = collections.deque(maxlen=self.command_num)

	def notify_command(self, cmd):
		self._commands.append((cmd, time.time()))
		self._cmd_counter += 1

	def log_state(self, trigger=None):
		t = "{:.3f}s".format(time.time() - self._commands[-1][1]) if self._commands else 'unknown'
		self._logger.info("Log state. trigger: %s, Last command was %s\n%s", trigger, t, self._get_state_str())

	def _do_regular_check(self):
		try:
			# CPU temp
			self._cpu_temp = self._get_cpu_temp()
			self._cpu_throttle_warnings = self._get_cpu_throttle_warnings()
			if self._cpu_temp > self.CPU_TEMP_THRESHOLD or self._cpu_throttle_warnings:
				self._logger.warn("CPU warning: temp: %s, throttle_warnings: %s", self._cpu_temp, self._cpu_throttle_warnings)

			# commands
			if self._commands:
				t = time.time() - self._commands[-1][1]
				if t > self.interval:
					self._logger.warn("Looks like there was no command since {:.3f}s.\n{}".format(t, self._get_state_str()))
				else:
					self._logger.debug("All good. Last command was {:.3f}s ago.".format(t))
		except:
			self._logger.exception("Exception in _check()")

	def _get_state_str(self):
		res = []
		res.append("Commands: len: {}, file_lines_total: {}, file_lines_read: {}, file_lines_remaining: {}, _lines_recoverd_total: {}".format(
			self._cmd_counter,
			self._currentFile.getLinesTotal(),
			self._currentFile.getLinesRead(),
			self._currentFile.getLinesRemaining(),
			self._comm_acc2._lines_recoverd_total,
		))
		res.append("Finish conditions: _finished_passes: {}, _passes: {}, _acc_line_buffer.is_empty(): {}".format(
			self._comm_acc2._finished_passes,
			self._comm_acc2._passes,
			self._comm_acc2._acc_line_buffer.is_empty(),
		))
		res.append(str(self._comm_acc2._acc_line_buffer))
		cmds = []
		for c,t in reversed(self._commands):
			cmds.append("({}) {}".format(datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S,%f")[:-3], c))
		res.append("Last commands: {}".format(", ".join(cmds)))
		return "\n".join(res)

	def _get_cpu_temp(self):
		try:
			temp = os.popen("vcgencmd measure_temp").readline()
			temp = float(temp.strip().replace("temp=", "").replace("'C", ""))
			return temp
		except:
			self._logger.exception("Excpetion while reading cpu temperature: ")

	def _get_cpu_throttle_warnings(self):
		"""
		See this https://harlemsquirrel.github.io/shell/2019/01/05/monitoring-raspberry-pi-power-and-thermal-issues.html
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
		MESSAGES = {
			0: 'Under-voltage!',
			1: 'ARM frequency capped!',
			2: 'Currently throttled!',
			16: 'Under-voltage has occurred since last reboot.',
			17: 'Throttling has occurred since last reboot.',
			18: 'ARM frequency capped has occurred since last reboot.'
		}
		t_hex = None
		throttled_binary = None
		try:
			t_hex = self._get_cpu_throttled()
			t_int = int(t_hex, 16)
			if t_int == 0:
				return []
			throttled_binary = bin(t_int)[2:].zfill(16)
		except:
			self._logger.exception("Excpetion in _get_cpu_throttle_warnings while converting cpu get_throttled: %s", t_hex)
			return []

		for position, message in MESSAGES.iteritems():
			# Check for the binary digits to be "on" for each warning message
			if len(throttled_binary) > position and throttled_binary[0 - position - 1] == '1':
				res.append(message)

		return res

	def _get_cpu_throttled(self):
		try:
			tmp = os.popen("vcgencmd get_throttled").readline()
			t_hex = tmp.strip().replace("throttled=", "")
			return t_hex
		except:
			self._logger.exception("Excpetion in _get_cpu_throttled() while reading cpu get_throttled: ")
