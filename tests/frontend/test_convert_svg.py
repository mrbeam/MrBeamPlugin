import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import uiUtils
import webdriverUtils


class TestConvertSvg(unittest.TestCase):
    def setup_method(self, method):

        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.critical_svgs = [
            #            "Display-none.svg",
            "Fillings-in-defs.svg",
            "umlaut_in_arialabel.svg",
            "Elements-without-id.svg",
            "Namespace_references_to_ENTITYs_outside_the_xml.svg",
            "Wichtel_neu.svg",
        ]

        # self.driver = webdriver.Chrome(service_log_path="/dev/null")
        self.driver = webdriverUtils.get_chrome_driver()

    def teardown_method(self, method):
        # self.driver.quit()
        pass

    def test_convert_svg(self):

        wait = WebDriverWait(self.driver, 10)

        # load ui
        url = "http://localhost:5002"  # should be configurable or static resolved on each dev laptop to the current mr beam
        uiUtils.load_webapp(self.driver, url)

        # login
        uiUtils.login(self.driver)

        # close notifications
        uiUtils.close_notifications(self.driver)

        for svg in self.critical_svgs:

            # add a remote svg
            svgUrl = self.resource_base + svg
            uiUtils.add_svg_url(self.driver, svgUrl)
            print("FETCHED: " + svgUrl)

            # start conversion
            print("  CONVERTING: " + svg)
            uiUtils.start_conversion(self.driver)

            # check result
            success_notification = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
                )
            )
            print("  SUCCESS: " + svg)

            uiUtils.cleanup_after_conversion(self.driver)

            uiUtils.clear_working_area(self.driver)
            # uiUtils.cancel_job(self.driver)

            # self.driver.delete_all_cookies()
