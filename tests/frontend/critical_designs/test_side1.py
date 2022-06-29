import logging
from .. import webdriverUtils
from ..critical_designs.base_procedure import BaseProcedure


class TestNamespaceWeirdBBox(BaseProcedure):
    def setup_method(self, method):

        # test config
        self.critical_svg = "Side 1.svg"
        self.doConversion = True

        # expectations (None means skip)
        self.expected_gcode = "Side 1.gco"
        self.expectedBBox = {
            "x": 0,
            "y": 0,
            "w": 144.73701,
            "h": 273.0379,
        }

        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}
