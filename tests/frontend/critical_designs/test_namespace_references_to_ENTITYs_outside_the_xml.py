import logging
from tests.frontend import webdriverUtils
from tests.frontend.critical_designs.base_procedure import BaseProcedure


class TestNamespaceReferencesToEntitysOutsideTheXML(BaseProcedure):
    def setup_method(self, method):

        # test config
        self.critical_svg = "Namespace_references_to_ENTITYs_outside_the_xml.svg"
        self.doConversion = True

        # expectations (None means skip)
        self.expected_gcode = "Namespace_references_to_ENTITYs_outside_the_xml.gco"
        self.expectedBBox = {
            "x": -0.282227277756,
            "y": 14.1026182175,
            "w": 159.28918457,
            "h": 144.65737915,
        }

        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}
