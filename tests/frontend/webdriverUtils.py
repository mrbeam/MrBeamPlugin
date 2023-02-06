import os
import logging

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# reduce log output
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger

# avoid communication between selenium and webdriver beeing logged on debug level.
from urllib3.connectionpool import log as urllibLogger

seleniumLogger.setLevel(logging.WARNING)
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
    chromedriver_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "chromedriver",
    )
    driver = webdriver.Chrome(
        executable_path=chromedriver_path, service_log_path=os.devnull, desired_capabilities=caps, options=opt
    )
    return driver


def get_console_log_summary(logs):
    # log entry example
    # {u'source': u'console-api',
    #  u'message': u'http://localhost:5000/?1609167298.58 110:33 "Could not instantiate the following view models due to unresolvable dependencies:"',
    #  u'timestamp': 1609167299977,
    #  u'level': u'SEVERE'}
    d = {}
    for entry in logs:
        # self.log.info(entry[u'message'])
        level = entry[u"level"]
        if not level in d:
            d[level] = 0

        d[level] += 1

    showWarning = "SEVERE" in d or "WARNING" in d or "ERROR" in d
    str = "console.log contains:"
    for lvl in d:
        str += " {}x {}".format(d[lvl], lvl)

    return (str, showWarning, d)
