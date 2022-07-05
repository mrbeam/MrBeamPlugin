import logging
from tests.frontend import webdriverUtils, uiUtils
from tests.frontend.quick_shapes.base_procedure import BaseProcedure


class TestCircle(BaseProcedure):
    def setup_method(self, method):

        # expectations (None means skip)
        self.expectedPaths = [
            "M38.5,0L38.5,0C59.7629628684935,0 77,17.2370371315065 77,38.5L77,38.5C77,59.7629628684935 59.7629628684935,77 38.5,77L38.5,77C17.2370371315065,77 0,59.7629628684935 0,38.5L0,38.5C0,17.2370371315065 17.2370371315065,0 38.5,0z"
        ]
        self.expectedBBox = {"x": 200, "y": 113.333297729, "w": 77, "h": 77}

        # basics
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        self.browserLog = []
        self.testEnvironment = {}

    def get_quick_shape(self):
        return uiUtils.add_quick_shape_circle(self.driver)
