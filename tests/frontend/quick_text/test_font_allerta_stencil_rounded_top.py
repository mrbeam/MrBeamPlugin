import logging
from frontend import webdriverUtils
from frontend import uiUtils
from frontend.quick_text.base_procedure import BaseProcedure


class TestAlertaStencil(BaseProcedure):
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

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_text(self):
        return uiUtils.add_quick_text_alerta_stencil(
            self.driver, "this is a Test", style=3
        )
