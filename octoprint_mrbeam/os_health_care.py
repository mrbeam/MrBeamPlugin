# coding=utf-8
import os
import time
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam import IS_X86

def os_health_care(plugin):
	OsHealthCare(plugin)


class OsHealthCare(object):

	HEALTHCARE_FILES_FOLDER = "files/os_health_care/"

	def __init__(self, plugin):
		self._logger = mrb_logger("octoprint.plugins.mrbeam.os_health_care")
		self.plugin = plugin
		self._event_bus = plugin._event_bus
		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

	def _on_mrbeam_plugin_initialized(self, event, payload):
		self._analytics_handler = self.plugin.analytics_handler
		self.run()

	def run(self):
		if IS_X86: return
		try:
			self.etc_network_interfaces()
		except Exception as e:
			self._logger.exception('Exception when running the OS heath care: {}'.format(e))

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
			out, code = exec_cmd_output(['sudo', 'cp', self._get_full_path_to_file('interfaces'), '/etc/network/interfaces'], shell=False)
			if code != 0:
				success = False
				self._logger.info("Could not fix /etc/network/interfaces")
			else:
				success = True
				self._logger.info("Fixed /etc/network/interfaces")

			self.log_analytics('/etc/network/interfaces', success=success, output=out)

			if success:
				self._logger.info("Rebooting system...")
				time.sleep(0.1)
				exec_cmd(['sudo', 'reboot', 'now'], shell=False)
		else:
			self._logger.info("OK /etc/network/interfaces")

	def log_analytics(self, event, success=None, output=None):
		data = dict(
			os_health_event=event,
			success=success,
			output=output,
		)
		self._analytics_handler.add_os_health_log(data)

	def _get_full_path_to_file(self, filename):
		return os.path.join(__package_path__, self.HEALTHCARE_FILES_FOLDER, filename)
