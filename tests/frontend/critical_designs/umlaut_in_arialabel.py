from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from .. import uiUtils
from .. import webdriverUtils
import time


class TestFillingsInDefs:
    def setup_method(self, method):

        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.critical_svg = "umlaut_in_arialabel.svg"

        # self.driver = webdriver.Chrome(service_log_path="/dev/null")
        self.driver = webdriverUtils.get_chrome_driver()

    def teardown_method(self, method):
        self.driver.quit()

    def test_convert_svg(self, baseurl):

        wait = WebDriverWait(self.driver, 10)

        # load ui
        baseurl = "localhost:5000"  # should be configurable or static resolved on each dev laptop to the current mr beam
        uiUtils.load_webapp(self.driver, baseurl)

        # login
        uiUtils.login(self.driver)

        # close notifications
        uiUtils.close_notifications(self.driver)

        # add a remote svg
        svgUrl = self.resource_base + self.critical_svg
        uiUtils.add_svg_url(self.driver, svgUrl)
        print("FETCHED: " + svgUrl)

        # check dimensions & position
        bbox = uiUtils.get_bbox(self.driver)
        {
            "y": 51.783084869384766,
            "x": 76.14178466796875,
            "w": 159.1521759033203,
            "h": 251.14407348632812,
        }

        assert bbox[u"x"] == 76.14178466796875, "BBox mismatch: X-Position" + str(bbox)
        assert bbox[u"y"] == 51.783084869384766, "BBox mismatch: Y-Position" + str(bbox)
        assert bbox[u"w"] == 159.1521759033203, "BBox mismatch: Width" + str(bbox)
        assert bbox[u"h"] == 251.14407348632812, "BBox mismatch: Height" + str(bbox)

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
