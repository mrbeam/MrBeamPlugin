import logging
from frontend import webdriverUtils
from frontend import uiUtils
from frontend.quick_shapes.base_procedure import BaseProcedure


class TestStar(BaseProcedure):
    def setup_method(self, method):

        # expectations (None means skip)
        self.expectedPaths = [
            "M50,0L50 0 28.31559480312316 20.57248383023656 15.450849718747373 47.552825814757675 -10.815594803123156 33.28697807033038 -40.450849718747364 29.38926261462366 -35 4.2862637970157365e-15 -40.45084971874737 -29.38926261462365 -10.815594803123165 -33.28697807033037 15.450849718747362 -47.55282581475768 28.315594803123158 -20.572483830236568z"
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
