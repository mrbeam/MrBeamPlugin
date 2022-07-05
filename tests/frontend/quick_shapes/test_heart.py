import logging
from tests.frontend import webdriverUtils, uiUtils
from tests.frontend.quick_shapes.base_procedure import BaseProcedure


class TestHeart(BaseProcedure):
    def setup_method(self, method):

        # expectations (None means skip)
        self.expectedPaths = [
            "M46.332,52.8C67.95360000000001,42.239999999999995 73.82232000000002,36.959999999999994 81.54432000000001,31.679999999999996C90.07380567638998,25.847873041784638 96.19182851458496,15.084190437323038 83.39760000000001,6.335999999999999C70.60337148541507,-2.41219043732304 54.86148567638996,4.7278730417846395 46.332,10.559999999999999C37.80251432361004,4.7278730417846395 22.06062851458495,-2.41219043732304 9.2664,6.335999999999999C-3.527828514584945,15.084190437323038 6.914514323610037,25.847873041784638 15.444,31.679999999999996C23.166,36.959999999999994 37.065599999999996,42.239999999999995 46.332,52.8z"
        ]
        self.expectedBBox = {
            "x": 203.28575372695923,
            "y": 115.57996881561279,
            "w": 87.44877624511719,
            "h": 50.55332946777345,
        }

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_shape(self):
        return uiUtils.add_quick_shape_heart(self.driver)
