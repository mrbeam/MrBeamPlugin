import time
import logging


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from .. import uiUtils
from .. import webdriverUtils
from .. import gcodeUtils
from .. import custom_expected_conditions as CEC


class TestFillingsInDefs:
    def setup_method(self, method):

        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.critical_svg = "Fillings-in-defs.svg"
        self.expected_gcode = "Fillings-in-defs.gco"

        # self.driver = webdriver.Chrome(service_log_path="/dev/null")
        self.driver = webdriverUtils.get_chrome_driver()

    def teardown_method(self, method):
        self.driver.quit()

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
            "y": 51.783084869384766,
            "x": 76.14178466796875,
            "w": 159.1521759033203,
            "h": 251.14407348632812,
        }

        assert bbox[u"x"] == exp["x"], "BBox mismatch: X-Position"
        assert bbox[u"y"] == exp["y"], "BBox mismatch: Y-Position"
        assert bbox[u"w"] == exp["w"], "BBox mismatch: Width"
        assert bbox[u"h"] == exp["h"], "BBox mismatch: Height"
        self.log.info("DIMENSIONS OK: " + self.critical_svg)

        # start conversion
        uiUtils.start_conversion(self.driver)

        # check result
        success_notification = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, uiUtils.SELECTOR_SUCCESS_NOTIFICATION)
            )
        )

        # print(success_notification)
        # gcode_url = success_notification.text
        # self.log.info("CONVERTED: " + self.critical_svg + " to " + gcode_url)

        # check gcode
        # payload example
        # {u'gcode_location': u'local', u'gcode': u'httpsmrbeam.github.iotest_rsccritical_designsFillings-in-defs.8.gco', u'stl': u'local/temp.svg', u'stl_location': u'local', u'time': 3.1736087799072266}
        payload = uiUtils.wait_for_slicing_done(self.driver)
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
