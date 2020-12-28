import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import logging

from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger

seleniumLogger.setLevel(logging.WARNING)

# avoid communication between selenium and webdriver beeing logged on debug level.
from urllib3.connectionpool import log as urllibLogger

urllibLogger.setLevel(logging.WARNING)


def get_chrome_driver(debugTest=False):
    opt = webdriver.ChromeOptions()
    opt.add_argument("--log-level=3")
    if debugTest:
        opt.add_argument("start-maximized")
        opt.add_argument("--auto-open-devtools-for-tabs")
    # opt.add_experimental_option("excludeSwitches", ["enable-logging"])
    # opt.add_experimental_option("w3c", False)
    caps = DesiredCapabilities.CHROME
    caps["loggingPrefs"] = {"browser": "ALL"}  # access to console.log output
    caps["goog:loggingPrefs"] = {
        "browser": "ALL"
    }  # access to console.log output incl. log levels below warning

    # caps["loggingPrefs"] = {"performance": "ALL"}
    driver = webdriver.Chrome(
        service_log_path=os.devnull, desired_capabilities=caps, options=opt
    )
    return driver
