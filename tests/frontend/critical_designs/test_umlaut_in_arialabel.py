import logging
from tests.frontend import webdriverUtils
from tests.frontend.critical_designs.base_procedure import BaseProcedure


class TestUmlautInArialabel(BaseProcedure):
    def setup_method(self, method):

        # test config
        self.critical_svg = "umlaut_in_arialabel.svg"
        self.doConversion = True

        # expectations (None means skip)
        self.expected_gcode = "umlaut_in_arialabel.gco"
        self.expectedBBox = {
            "x": 5.796566963195801,
            "y": 27.573705673217773,
            "w": 149.99998474121094,
            "h": 149.99998474121094,
        }

        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}
