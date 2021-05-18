import logging
from tests.frontend import webdriverUtils
from tests.frontend import uiUtils
from tests.frontend.quick_text.base_procedure import BaseProcedure


class TestComforta(BaseProcedure):
    text = "Test"

    def setup_method(self, method):
        # expectations (None means skip)
        self.expectedText = {
            "text": unicode(self.text.decode("utf-8")),
            "font-family": "Comfortaa",
            "fill": "#9b9b9b",
        }
        self.expectedBBox = {
            "x": 229.90625,
            "y": 112.8125,
            "w": 40.1875,
            "h": 21.65625,
        }

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_text(self):
        return uiUtils.add_quick_text(self.driver, self.text, font=3)
