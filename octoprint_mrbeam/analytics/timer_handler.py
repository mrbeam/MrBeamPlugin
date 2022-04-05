# coding=utf-8
import re

import netifaces
import requests
import os
from threading import Timer

from analytics_keys import AnalyticsKeys as ak
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.cmd_exec import exec_cmd, exec_cmd_output


class TimerHandler:
    MAX_FILE_SIZE_BYTES = 50000000  # 50 MB
    NUM_ROWS_TO_KEEP = 20000

    DISK_SPACE_TIMER = 3.0
    NUM_FILES_TIMER = 5.0
    SW_VERSIONS_TIMER = 7.0
    IP_ADDRESSES_TIMER = 15.0
    SELF_CHECK_TIMER = 20.0
    INTERNET_CONNECTION_TIMER = 25.0
    FILE_CROP_TIMER = 60.0

    SELF_CHECK_USER_AGENT = "MrBeamPlugin self check"
    ONLINE_CHECK_URL = "https://find.mr-beam.org/onlinecheck"

    def __init__(self, plugin, analytics_handler, analytics_lock):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.analytics.timerhandler")
        self._plugin = plugin
        self._analytics_handler = analytics_handler
        self._analytics_lock = analytics_lock

        self._timers = []

    def start_timers(self):
        try:
            self._timers = []
            self._timers.append(Timer(self.DISK_SPACE_TIMER, self._disk_space))
            self._timers.append(Timer(self.NUM_FILES_TIMER, self._num_files))
            self._timers.append(Timer(self.IP_ADDRESSES_TIMER, self._ip_addresses))
            self._timers.append(Timer(self.SELF_CHECK_TIMER, self._http_self_check))
            self._timers.append(
                Timer(self.INTERNET_CONNECTION_TIMER, self._internet_connection)
            )
            self._timers.append(Timer(self.SW_VERSIONS_TIMER, self._software_versions))
            self._timers.append(
                Timer(self.FILE_CROP_TIMER, self._crop_analytics_file_if_too_big)
            )

            for timer in self._timers:
                timer.start()

        except RuntimeError as e:
            self._logger.exception("Exception during start_timers: {}".format(e))

    def cancel_timers(self):
        try:
            for timer in self._timers:
                timer.cancel()

        except RuntimeError as e:
            self._logger.exception("Exception during cancel_timers: {}".format(e))

    def _crop_analytics_file_if_too_big(self):
        try:
            if os.path.exists(self._analytics_handler.analytics_file):
                analytics_size = os.path.getsize(self._analytics_handler.analytics_file)
                if analytics_size > self.MAX_FILE_SIZE_BYTES:
                    with self._analytics_lock:
                        self._logger.info("Cropping analytics file...")

                        command = 'echo "$(tail -n {lines} {file})" > {file}'.format(
                            lines=self.NUM_ROWS_TO_KEEP,
                            file=self._analytics_handler.analytics_file,
                        )
                        success = exec_cmd(command, shell=True)

                        if success:
                            self._logger.info(
                                "Cropping of the analytics file finished."
                            )
                        else:
                            self._logger.warning("Could not crop analytics file.")

                    payload = {
                        ak.Log.SUCCESS: success,
                        ak.Log.AnalyticsFile.PREV_SIZE: analytics_size,
                        ak.Log.AnalyticsFile.NEW_SIZE: os.path.getsize(
                            self._analytics_handler.analytics_file
                        ),
                        ak.Log.AnalyticsFile.NUM_LINES: self.NUM_ROWS_TO_KEEP,
                    }
                    self._plugin.analytics_handler.add_analytics_file_crop(payload)

        except Exception:
            self._logger.exception("Exception during _crop_analytics_file_if_too_big")

    def _http_self_check(self):
        try:
            payload = dict()
            interfaces = netifaces.interfaces()
            err = None
            elapsed_seconds = None

            for interface in interfaces:
                if interface != "lo":
                    addresses = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addresses:
                        for tmp in addresses[netifaces.AF_INET]:
                            ip = tmp["addr"]

                            try:
                                url = "http://" + ip
                                headers = {"User-Agent": self.SELF_CHECK_USER_AGENT}
                                r = requests.get(url, headers=headers)
                                response = r.status_code
                                elapsed_seconds = r.elapsed.total_seconds()
                            except requests.exceptions.RequestException as e:
                                response = -1
                                err = str(e)

                            if interface not in payload:
                                payload[interface] = []
                            payload[interface].append(
                                {
                                    ak.Device.Request.IP: ip,
                                    ak.Device.Request.RESPONSE: response,
                                    ak.Device.Request.ELAPSED_S: elapsed_seconds,
                                    ak.Device.ERROR: err,
                                }
                            )

            self._plugin.analytics_handler.add_http_self_check(payload)

        except Exception as e:
            self._logger.exception(
                "Exception during the _http_self_check: {}".format(e)
            )

    def _internet_connection(self):
        try:
            try:
                headers = {"User-Agent": self.SELF_CHECK_USER_AGENT}
                r = requests.head(self.ONLINE_CHECK_URL, headers=headers)
                response = r.status_code
                err = None
                connection = True
            except requests.exceptions.RequestException as e:
                response = -1
                err = str(e)
                connection = False

            payload = {
                ak.Device.Request.RESPONSE: response,
                ak.Device.ERROR: err,
                ak.Device.Request.CONNECTION: connection,
            }
            self._plugin.analytics_handler.add_internet_connection(payload)

        except Exception as e:
            self._logger.exception(
                "Exception during the _internet_connection check: {}".format(e)
            )

    def _ip_addresses(self):
        try:
            payload = dict()
            interfaces = netifaces.interfaces()

            for interface in interfaces:
                addresses = netifaces.ifaddresses(interface)
                payload[interface] = dict()
                if netifaces.AF_INET in addresses:
                    payload[interface]["IPv4"] = []
                    for idx, addr in enumerate(addresses[netifaces.AF_INET]):
                        payload[interface]["IPv4"].append(addr["addr"])
                if netifaces.AF_INET6 in addresses:
                    payload[interface]["IPv6"] = []
                    for idx, addr in enumerate(addresses[netifaces.AF_INET6]):
                        payload[interface]["IPv6"].append(addr["addr"])

            self._plugin.analytics_handler.add_ip_addresses(payload)

        except Exception as e:
            self._logger.exception(
                "Exception during the _ip_addresses check: {}".format(e)
            )

    def _disk_space(self):
        try:
            statvfs = os.statvfs("/")
            total_space = statvfs.f_frsize * statvfs.f_blocks
            available_space = (
                statvfs.f_frsize * statvfs.f_bavail
            )  # Available space for non-super users
            used_percent = round((total_space - available_space) * 100 / total_space)

            disk_space = {
                ak.Device.Usage.TOTAL_SPACE: total_space,
                ak.Device.Usage.AVAILABLE_SPACE: available_space,
                ak.Device.Usage.USED_SPACE: used_percent,
            }
            self._plugin.analytics_handler.add_disk_space(disk_space)

        except Exception as e:
            self._logger.exception(
                "Exception during the _disk_space check: {}".format(e)
            )

    def _software_versions(self):
        """
        TODO: Move this back to analytics handler.
        I do not se any reason any more to run this as a timed and threaded task.
        it made sens when we did a filesystem checksum calculation... _software_versions_and_checksums()
        """
        sw_versions = self._get_software_versions()
        self._logger.debug("Software Version info: \n{}".format(sw_versions))
        self._plugin.analytics_handler.add_software_versions(sw_versions)

    def _software_versions_and_checksums(self):
        """
        Deprecated
        Checksum calculation significantly slows down the device.
        Furthermore we never used these checksums for anything.
        :return:
        """
        try:
            # must end with /
            folders = {
                "mrbeam": {
                    "src_path": "/home/pi/site-packages/octoprint_mrbeam/",
                },
                "iobeam": {
                    "src_path": "/home/pi/dist-packages/iobeam/",
                },
                "findmymrbeam": {
                    "src_path": "/home/pi/site-packages/octoprint_findmymrbeam/",
                },
                "netconnectd-daemon": {
                    "src_path": "/home/pi/dist-packages/netconnectd/",
                },
                "netconnectd": {
                    "src_path": "/home/pi/site-packages/octoprint_netconnectd/",
                },
                "mrb_hw_info": {
                    "src_path": "/home/pi/dist-packages/mrb_hw_info/",
                },
                "mrbeam-ledstrips": {
                    "src_path": "/home/pi/dist-packages/mrbeam_ledstrips/",
                },
                "octoprint": {
                    "src_path": "/home/pi/site-packages/octoprint/",
                },
                "_dist-packages": {
                    "src_path": "/home/pi/dist-packages/",
                },
                "_site-packages": {
                    "src_path": "/home/pi/site-packages/",
                },
            }
            sw_versions = self._get_software_versions()

            if self._analytics_handler.is_analytics_enabled():
                for name, conf in folders.iteritems():
                    cmd = 'find "{folder}" -type f -exec md5sum {{}} \; | sort -k 2 | md5sum'.format(
                        folder=conf.get("src_path")
                    )
                    out, code = exec_cmd_output(cmd, shell=True)
                    if out:
                        if name not in sw_versions:
                            sw_versions[name] = {}
                        sw_versions[name]["checksum"] = out.replace("  -", "").strip()

            self._logger.info("_software_versions_and_checksums: %s", sw_versions)
            self._plugin.analytics_handler.add_software_versions(sw_versions)
        except:
            self._logger.exception("Exception in _software_versions_and_checksums(): ")

    def _get_software_versions(self):
        result = dict()
        software_info = None

        try:
            plugin_info = self._plugin._plugin_manager.get_plugin_info("softwareupdate")
            impl = plugin_info.implementation
            # using the method get_current_versions() is OK as it is threadsafe
            software_info, _, _ = impl.get_current_versions()
            self._logger.debug("Software_info: \n {}".format(software_info))
        except Exception as e:
            self._logger.exception(
                "Exception while reading software_info from softwareupdate plugin. Error:{} ".format(e)
            )
            return result

        if isinstance(software_info, dict) is False:
            self._logger.warn(
                "get_current_versions() Can't read software version from softwareupdate plugin."
            )
            return result

        # Reaching this section means we are OK so far
        for name, info in software_info.iteritems():
            commit_hash = info["information"]["local"].get("name", None)
            if commit_hash is not None:
                # regex: "Commit 89nhfbffnf7f8fbfgfndhf" --> "89nhfbffnf7f8fbfgfndhf"
                regex_match = re.match(r"Commit (\S+)", commit_hash)
                if regex_match is not None:
                    commit_hash = regex_match.group(1)
            result[name] = dict(
                version=info.get("displayVersion", None),
                commit_hash=commit_hash,
            )
        return result

    def _num_files(self):
        try:
            all_files = self._plugin._file_manager.list_files(path="", recursive=True)[
                "local"
            ]

            file_counter = {}
            for name, info in all_files.iteritems():

                file_type = info.get("type", None)
                # All the design files are called model (everything's that not gcode) but we want to know the exact type
                if file_type == "model":
                    file_type = info.get("typePath", [None])[-1]

                if file_type in file_counter:
                    file_counter[file_type] += 1
                else:
                    file_counter[file_type] = 1

            self._plugin.analytics_handler.add_num_files(file_counter)

        except Exception as e:
            self._logger.exception(
                "Exception during the _num_files check: {}".format(e)
            )
