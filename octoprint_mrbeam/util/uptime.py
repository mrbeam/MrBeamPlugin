# coding=utf-8
import os
from sys import platform
from datetime import timedelta
from octoprint_mrbeam.mrb_logger import mrb_logger

# http://planzero.org/blog/2012/01/26/system_uptime_in_python,_a_better_way
def get_uptime():
    try:
        if platform == 'darwin':
            return os.system("uptime")
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
