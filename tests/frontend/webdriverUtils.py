import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import logging

# selenium_logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
# selenium_logger.setLevel(logging.WARNING)  # Only display possible problems

from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger

seleniumLogger.setLevel(logging.WARNING)
from urllib3.connectionpool import log as urllibLogger

urllibLogger.setLevel(logging.WARNING)


def get_chrome_driver():
    opt = webdriver.ChromeOptions()
    opt.add_argument("--log-level=3")
    # opt.add_experimental_option("excludeSwitches", ["enable-logging"])
    # opt.add_experimental_option("w3c", False)
    caps = DesiredCapabilities.CHROME
    # caps["loggingPrefs"] = {"performance": "ALL"}
    driver = webdriver.Chrome(
        service_log_path=os.devnull, desired_capabilities=caps, options=opt
    )
    return driver
