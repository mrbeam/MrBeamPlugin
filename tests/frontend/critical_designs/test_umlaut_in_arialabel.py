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
        self.critical_svg = "umlaut_in_arialabel.svg"
        self.expected_gcode = "umlaut_in_arialabel.gco"

        # self.driver = webdriver.Chrome(service_log_path="/dev/null")
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []

    def teardown_method(self, method):
        self.driver.quit()
        pass

    def append_logs(self, logs):
        self.browserLog.extend(logs)

    def test_convert_svg(self, baseurl):

        wait = WebDriverWait(self.driver, 10)

        # load ui
        try:
            uiUtils.load_webapp(self.driver, baseurl)
        except:
            self.log.error(
                "Error: Unable to load beamOS ("
                + baseurl
                + ")\nPlease run pytest with --baseurl=http://mrbeam-7E57.local or similar pointing to your test machine."
            )

        # login
        uiUtils.login(self.driver)

        # close notifications
        uiUtils.close_notifications(self.driver)

        # add a remote svg
        svgUrl = self.resource_base + self.critical_svg
        uiUtils.add_svg_url(self.driver, svgUrl)
        self.log.info("FETCHED: " + svgUrl)

        # check dimensions & position
        bbox = uiUtils.get_bbox(self.driver)
        exp = {
            "x": 5.796566963195801,
            "y": 27.573705673217773,
            "w": 149.99998474121094,
            "h": 149.99998474121094,
        }

        ok, msg = frontendTestUtils.compare_dimensions(bbox, exp)
        assert ok, msg
        self.log.info("DIMENSIONS OK: " + self.critical_svg)

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

        generated = gcodeUtils.get_gcode(gcodeUrl)
        expected = gcodeUtils.get_gcode(self.resource_base + self.expected_gcode)
        diff = gcodeUtils.compare(generated, expected)
        assert (
            len(diff) == 0
        ), "GCode mismatch! {} lines are different. First 10 changes:\n\n{}".format(
            len(diff), "\n".join(diff[:10])
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
