import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from frontend import webdriverUtils

selenium_logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
selenium_logger.setLevel(logging.WARNING)  # Only display possible problems

import uiUtils
import time


class TestConvertQuickShape:
    def setup_method(self, method):
        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_convert_quick_shape(self):

        wait = WebDriverWait(self.driver, 10)

        # load ui
        url = "localhost:5000"  # should be configurable or static resolved on each dev laptop to the current mr beam
        # url = "http://mrbeam-axel.local"  # should be configurable or static resolved on each dev laptop to the current mr beam
        uiUtils.load_webapp(self.driver, url)

        # login
        uiUtils.login(self.driver)

        # close notifications
        uiUtils.close_notifications(self.driver)

        # add quick shape heart
        uiUtils.add_quick_shape_heart(self.driver)

        # start conversion
        uiUtils.start_conversion(self.driver)

        # check result
        success_notification = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
            )
        )

        print("CONVERSION_SUCCESS")
