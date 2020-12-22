from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from .. import uiUtils
from .. import webdriverUtils
import time


class TestFillingsInDefs:
    def setup_method(self, method):

        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.critical_svg = "Fillings-in-defs.svg"

        # self.driver = webdriver.Chrome(service_log_path="/dev/null")
        self.driver = webdriverUtils.get_chrome_driver()

    def teardown_method(self, method):
        self.driver.quit()

    def test_convert_svg(self):

        wait = WebDriverWait(self.driver, 10)

        # load ui
        url = "localhost:5000"  # should be configurable or static resolved on each dev laptop to the current mr beam
        uiUtils.load_webapp(self.driver, url)

        # login
        uiUtils.login(self.driver)

        # close notifications
        uiUtils.close_notifications(self.driver)

        # add a remote svg
        svgUrl = self.resource_base + self.critical_svg
        uiUtils.add_svg_url(self.driver, svgUrl)
        print("FETCHED: " + svgUrl)

        # TODO check dimensions & position

        # start conversion
        print("  CONVERTING: " + self.critical_svg)
        uiUtils.start_conversion(self.driver)

        # check result
        success_notification = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
            )
        )
        print("  SUCCESS: " + self.critical_svg)

        uiUtils.cleanup_after_conversion(self.driver)

        uiUtils.clear_working_area(self.driver)
        # uiUtils.cancel_job(self.driver)

        # TODO check gcode

        # self.driver.delete_all_cookies()
