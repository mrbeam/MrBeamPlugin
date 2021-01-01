import logging
from frontend import webdriverUtils
from frontend import uiUtils
from frontend.quick_shapes.base_procedure import BaseProcedure


class TestStar(BaseProcedure):
    def setup_method(self, method):

        # expectations (None means skip)
        self.expectedPaths = [
            "M77,0L77 0 43.60601599680967 31.6816250985643 23.794308566870953 73.23135175472682 -16.65601599680966 51.26194622830878 -62.294308566870946 45.25946442652044 -53.9 6.600846247404233e-15 -62.29430856687095 -45.259464426520424 -16.656015996809675 -51.26194622830877 23.794308566870935 -73.23135175472683 43.60601599680966 -31.681625098564314z"
        ]
        self.expectedBBox = {
            "x": 137.705688477,
            "y": 40.1019439697,
            "w": 139.294311523,
            "h": 146.46270752,
        }

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_shape(self):
        return uiUtils.add_quick_shape_star(self.driver)
