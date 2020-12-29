import time
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from frontend import uiUtils
from frontend import webdriverUtils
from frontend import gcodeUtils
from frontend import frontendTestUtils


class TestFillingsInDefs:
    def setup_method(self, method):

        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.critical_svg = "Namespace_references_to_ENTITYs_outside_the_xml.svg"
        self.expected_gcode = "Namespace_references_to_ENTITYs_outside_the_xml.gco"

        # self.driver = webdriver.Chrome(service_log_path="/dev/null")
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def teardown_method(self, method):
        self.driver.quit()
        pass

    def append_logs(self, logs):
        self.browserLog.extend(logs)

    def test_convert_svg(self, baseurl):

        wait = WebDriverWait(self.driver, 10)

        # load ui
        try:
            self.testEnvironment = uiUtils.load_webapp(self.driver, baseurl)
        except:
            self.log.error(
                "Error: Unable to load beamOS ("
                + baseurl
                + ")\nPlease run pytest with --baseurl=http://mrbeam-7E57.local or similar pointing to your test machine."
            )

        # login
        apikey = uiUtils.login(self.driver)
        self.testEnvironment["APIKEY"] = apikey

        # close notifications
        uiUtils.close_notifications(self.driver)

        # add a remote svg
        svgUrl = self.resource_base + self.critical_svg
        uiUtils.add_svg_url(self.driver, svgUrl)
        self.log.info("FETCHED: " + svgUrl)

        # check dimensions & position
        bbox = uiUtils.get_bbox(self.driver)
        exp = {
            "x": -0.282227277756,
            "y": 14.1026182175,
            "w": 159.28918457,
            "h": 144.65737915,
        }

        ok, msg = frontendTestUtils.compare_dimensions(bbox, exp)
        self.log.info("DIMENSIONS OK: {} {} {}".format(ok, msg, self.critical_svg))
        assert ok, msg

        # start conversion
        uiUtils.start_conversion(self.driver)

        # check result
        success_notification = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
            )
        )

        # check gcode
        # payload example
        # {u'gcode_location': u'local', u'gcode': u'httpsmrbeam.github.iotest_rsccritical_designsFillings-in-defs.8.gco', u'stl': u'local/temp.svg', u'stl_location': u'local', u'time': 3.1736087799072266}
        payload = uiUtils.wait_for_slicing_done(self.driver, self.append_logs)
        gcodeUrl = baseurl + "/downloads/files/local/" + payload[u"gcode"]
        expUrl = self.resource_base + self.expected_gcode

        generated = gcodeUtils.get_gcode(gcodeUrl)
        self.log.info("GEN: " + generated[:50])
        assert (
            len(generated) > 0
        ), "Generated gcode was empty or not downloadable. {}\n{}".format(
            gcodeUrl, generated[:100]
        )
        expected = gcodeUtils.get_gcode(expUrl)
        self.log.info("EXP: " + expected[:50])
        assert (
            len(expected) > 0
        ), "Expected gcode was empty or not downloadable. {}\n{}".format(
            expUrl, expected[:100]
        )
        diff = gcodeUtils.compare(generated, expected)
        assert (
            len(diff) == 0
        ), "GCode mismatch! {} lines are different. First 30 changes:\n\n{}".format(
            len(diff), "\n".join(diff[:30])
        )

        self.log.info("SUCCESS: " + self.critical_svg)
        self.append_logs(self.driver.get_log("browser"))
        msg, warningsInLogs, summary = webdriverUtils.get_console_log_summary(
            self.browserLog
        )
        if warningsInLogs:
            self.log.warn(msg)
        else:
            self.log.info(msg)

        # TODO assert no js errors
        # assert summary["WARNING"] == 0, "{} Javascript warnings occured".format(summary["WARNING"])
        # assert summary["SEVERE"] == 0, "{} Javascript errors occured".format(summary["SEVERE"])
