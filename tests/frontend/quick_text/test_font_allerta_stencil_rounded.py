# coding=utf-8
import logging
from frontend import webdriverUtils
from frontend import uiUtils
from frontend.quick_text.base_procedure import BaseProcedure


class TestAlertaStencil(BaseProcedure):
    text = "umlaute äüöß"

    def setup_method(self, method):

        # expectations (None means skip)
        # print(self.text.encode("ISO-8859-1"))
        self.expectedText = {
            "text": unicode(self.text.decode("utf-8")),
            "font-family": "Allerta Stencil",
            "fill": "#9b9b9b",
        }
        self.expectedBBox = {
            "x": 187.3125,
            "y": 109.765625,
            "w": 125.390625,
            "h": 63.921875,
        }

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_text(self):

        return uiUtils.add_quick_text_alerta_stencil(self.driver, self.text, style=2)
