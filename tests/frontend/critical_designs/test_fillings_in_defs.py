import logging
from .. import webdriverUtils
from ..critical_designs.base_procedure import BaseProcedure


class TestFillingsInDefs(BaseProcedure):
    def setup_method(self, method):

        # test config
        self.critical_svg = "Fillings-in-defs.svg"
        self.doConversion = True

        # expectations (None means skip)
        self.expected_gcode = "Fillings-in-defs.gco"
        self.expectedBBox = {
            "x": 76.14178466796875,
            "y": 51.783084869384766,
            "w": 159.1521759033203,
            "h": 251.14407348632812,
        }

        # basics
        self.log = logging.getLogger()
        self.resource_base = "https://mrbeam.github.io/test_rsc/critical_designs/"
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}
