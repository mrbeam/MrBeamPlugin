import logging
from tests.frontend import webdriverUtils
from tests.frontend import uiUtils
from tests.frontend.quick_text.base_procedure import BaseProcedure


class TestMrBedfort(BaseProcedure):
    text = "Test"

    def setup_method(self, method):
        # expectations (None means skip)
        self.expectedText = {
            "text": unicode(self.text.decode("utf-8")),
            "font-family": "Mr Bedfort",
            "fill": "#9b9b9b",
        }
        self.expectedBBox = {
            "x": 228.40625,
            "y": 110.265625,
            "w": 35.46875,
            "h": 32.78125,
        }

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_text(self):
        return uiUtils.add_quick_text(self.driver, self.text, font=8)
