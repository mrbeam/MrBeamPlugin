import logging
from tests.frontend import webdriverUtils
from tests.frontend.critical_designs.base_procedure import BaseProcedure


class TestNamespaceReferencesToEntitysOutsideTheXML(BaseProcedure):
    def setup_method(self, method):

        # test config
        self.critical_svg = "undeclared_namespace.svg"
        self.doConversion = True

        # expectations (None means skip)
        self.expected_gcode = "undeclared_namespace.gco"
        self.expectedBBox = {
            "x": 8.46249389648,
            "y": 8.36135959625,
            "w": 82.8678207397461,
            "h": 83.33135986328125,
        }

        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}
