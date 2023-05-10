# coding=utf-8
import subprocess
from sys import platform
from datetime import timedelta
from octoprint_mrbeam.mrb_logger import mrb_logger


def get_uptime():
    try:
        if platform == "darwin":
            output = (
                subprocess.check_output(["sysctl", "-n", "kern.boottime"])
                .decode()
                .strip()
            )
            boot_time = int(output.split()[3].split(",")[0])
            uptime_seconds = (
                int(subprocess.check_output(["date", "+%s"]).decode().strip())
                - boot_time
            )

            return uptime_seconds
        else:
            with open("/proc/uptime", "r") as f:
                uptime = float(f.readline().split()[0])
            return uptime
    except Exception as e:
        mrb_logger("octoprint.plugins.mrbeam.util.uptime").exception(
            "Exception during get_uptime: {}".format(e), analytics=False
        )
        return None


def get_uptime_human_readable(uptime_seconds=None):
    uptime_seconds = uptime_seconds or get_uptime()
    if uptime_seconds is not None:
        return str(timedelta(seconds=int(uptime_seconds)))
