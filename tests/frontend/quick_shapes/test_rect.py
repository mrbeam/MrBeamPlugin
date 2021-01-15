import logging
from frontend import webdriverUtils
from frontend import uiUtils
from frontend.quick_shapes.base_procedure import BaseProcedure


class TestRect(BaseProcedure):
    def setup_method(self, method):

        # expectations (None means skip)
        self.expectedPaths = ["M0,0l99,0 0,77 -99,0 z"]
        self.expectedBBox = {"x": 200, "y": 113.333297729, "w": 99, "h": 77}

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_shape(self):
        return uiUtils.add_quick_shape_rect(self.driver)
