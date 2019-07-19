# coding=utf-8
import os
import time
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.analytics.analytics_handler import analyticsHandler
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output


def os_health_care(plugin):
	OsHealthCare(plugin).run()



class OsHealthCare(object):

	HEALTHCARE_FILES_FOLDER = "files/os_health_care/"


	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.os_health_care")
		self.plugin = plugin
		self.analyticsHandler = analyticsHandler(plugin)


	def run(self):
		self.etc_network_interfaces()


	def etc_network_interfaces(self):
		needs_fix = False
		max_retries = 3
		sleep_time = 1.2
		for i in range(max_retries):
			ok_eth0  = exec_cmd(['sudo', 'ifup', '--no-act', 'eth0'], shell=False)
			ok_wlan0 = exec_cmd(['sudo', 'ifup', '--no-act', 'wlan0'], shell=False)
			if ok_eth0 and ok_wlan0:
				needs_fix = False
				break
			else:
				self._logger.warn("Failed test on ifup command: eth0: %s, wlan0: %s - Retrying in %ss", ok_eth0, ok_wlan0, sleep_time)
				needs_fix = True
				time.sleep(sleep_time)

		if needs_fix:
			self._logger.warn("Fixing /etc/network/interfaces")
			ok = exec_cmd(['sudo', 'cp', self._get_full_path_to_file('interfaces'), '/etc/network/interfaces'], shell=False)
			self._logger.warn("Fixed  /etc/network/interfaces - Success: %s", ok)
			self.log_analytics('/etc/network/interfaces', ok)
			if ok:
				self._logger.info("Rebooting system...", ok)
				time.sleep(0.1)
				exec_cmd(['sudo', 'reboot', 'now'], shell=False)
		else:
			self._logger.warn("OK /etc/network/interfaces")

	def log_analytics(self, event, success=None):
		data = dict(
			os_health_event=event,
			success=success,
		)
		self.analyticsHandler.log_os_health_event(data)

	def _get_full_path_to_file(self, filename):
		return os.path.join(__package_path__, self.HEALTHCARE_FILES_FOLDER, filename)
