from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import logging

selenium_logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
selenium_logger.setLevel(logging.WARNING)  # Only display possible problems

import uiUtils
import time


class TestConvertSvg:
    def setup_method(self, method):

        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.critical_svgs = [
            #            "Display-none.svg",
            "Fillings-in-defs.svg",
            "Schild_Olga_Geb_druckfertig_2.svg",
            "Elements-without-id.svg",
            "Namespace_references_to_ENTITYs_outside_the_xml.svg",
            "Wichtel_neu.svg",
        ]

        self.driver = webdriver.Chrome()

    def teardown_method(self, method):
        self.driver.quit()

    def test_convert_svg(self):

        wait = WebDriverWait(self.driver, 10)

        for svg in self.critical_svgs:
            print("CONVERSION: " + svg)

            # load ui
            url = "localhost:5000"  # should be configurable or static resolved on each dev laptop to the current mr beam
            uiUtils.load_webapp(self.driver, url)

            # login
            uiUtils.login(self.driver)

            # close notifications
            uiUtils.close_notifications(self.driver)

            url = self.resource_base + svg
            # add a remote svg
            uiUtils.add_svg_url(self.driver, url)

            # start conversion
            uiUtils.start_conversion(self.driver)

            # check result
            success_notification = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
                )
            )
            print("  SUCCESS: " + svg)

            uiUtils.clear_working_area(self.driver)

            # uiUtils.cancel_job(self.driver)
