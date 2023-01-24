import logging
from tests.frontend import webdriverUtils
from tests.frontend.critical_designs.base_procedure import BaseProcedure


class TestElementsWithoutId(BaseProcedure):
    def setup_method(self, method):

        # test config
        self.critical_svg = "Elements-without-id.svg"
        self.doConversion = True

        # expectations (None means skip)
        self.expected_gcode = "Elements-without-id.gco"
        self.expectedBBox = {"x": 0, "y": 0, "w": 499.959625244, "h": 399.967712402}

        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}
