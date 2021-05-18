import logging
from tests.frontend import webdriverUtils
from tests.frontend import uiUtils
from tests.frontend.quick_text.base_procedure import BaseProcedure


class TestAlertaStencilRoundedTop(BaseProcedure):
    def setup_method(self, method):

        # expectations (None means skip)
        self.expectedText = {
            "text": "this is a Test",
            "font-family": "Allerta Stencil",
            "fill": "#9b9b9b",
        }
        self.expectedBBox = {
            "x": 198.875,
            "y": 88.890625,
            "w": 102.25,
            "h": 46.171875,
        }
        # x: 220.28125 != 198.875 y: 82.421875 != 88.890625 w: 59.65625 != 102.25 h: 52.84375 != 46.171875

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_text(self):
        return uiUtils.add_quick_text(self.driver, "this is a Test", style=3)
