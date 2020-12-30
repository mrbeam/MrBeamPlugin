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
        self.testEnvironment = {}

    def teardown_method(self, method):
        self.driver.quit()
        pass

    def append_logs(self, logs):
        self.browserLog.extend(logs)

    def test_convert_svg(self, baseurl):

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

        # ensure homing cycle
        uiUtils.ensure_device_homed(self.driver)

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
        wait = WebDriverWait(self.driver, 20, poll_frequency=2.0)
        success_notification = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
            ),
            message="Waiting for conversion finished PNotify",
        )

        # check gcode
        if baseurl.startswith("http://localhost:"):
            # payload example
            # {u'gcode_location': u'local', u'gcode': u'httpsmrbeam.github.iotest_rsccritical_designsFillings-in-defs.8.gco', u'stl': u'local/temp.svg', u'stl_location': u'local', u'time': 3.1736087799072266}
            payload = uiUtils.wait_for_conversion_started(self.driver, self.append_logs)
            gcode = payload[u"gcode"]
        else:
            gcode = uiUtils.wait_for_ready_to_laser_dialog(self.driver)

        uiUtils.cancel_job(self.driver)

        gcodeUrl = baseurl + "/downloads/files/local/" + gcode
        self.log.info("gcodeUrl: " + gcodeUrl)
        generated = gcodeUtils.get_gcode(gcodeUrl)
        linesGen = len(generated)
        self.log.info("GEN: " + generated[:50])
        assert (
            len(generated) > 0
        ), "Generated gcode was empty or not downloadable. {}\n{}".format(
            gcodeUrl, generated[:100]
        )

        expUrl = self.resource_base + self.expected_gcode
        expected = gcodeUtils.get_gcode(expUrl)
        linesExp = len(expected)
        self.log.info("EXP: " + expected[:50])
        assert (
            len(expected) > 0
        ), "Expected gcode was empty or not downloadable. {}\n{}".format(
            expUrl, expected[:100]
        )

        diff = gcodeUtils.compare(generated, expected)
        assert (
            len(diff) == 0
        ), "GCode mismatch! {} lines are different. First 30 changes (- generated / + expected):\n\n{}".format(
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
