import unittest

from tests.frontend import uiUtils, webdriverUtils, frontendTestUtils


@unittest.skip('DEPRECATED')
class BaseProcedure(unittest.TestCase):
    def setup_method(self, method):
        # expectations (None means skip)
        self.expectedPaths = None
        self.expectedBBox = None
        raise NotImplementedError("Subclasses must override setup_method()!")

    def get_quick_shape(self):
        raise NotImplementedError("Subclasses must override get_quick_shape()!")

    def teardown_method(self, method):
        self.driver.quit()
        pass

    def append_logs(self, logs):
        self.browserLog.extend(logs)

    def test_quick_shape(self, baseurl, rsc_folder):

        # load ui
        try:
            self.testEnvironment = uiUtils.load_webapp(self.driver, baseurl)
        except:
            self.log.error(
                "Error: No beamOS at '{}'. (Please set --baseurl=http://mrbeam-7E57.local e.g.)".format(
                    baseurl
                )
            )

        # login
        apikey = uiUtils.login(self.driver)
        self.testEnvironment["APIKEY"] = apikey

        # close notifications
        uiUtils.close_notifications(self.driver)

        # ensure homing cycle
        if not baseurl.startswith("http://localhost:"):
            uiUtils.ensure_device_homed(self.driver)

        # add a quick shape
        qsEl, listEl = self.get_quick_shape()

        # check dimensions & position
        if self.expectedBBox:
            bbox = uiUtils.get_bbox(self.driver)
            ok, msg = frontendTestUtils.compare_dimensions(bbox, self.expectedBBox)
            assert ok, msg
            self.log.info("DIMENSIONS OK")

        # check path
        if self.expectedPaths:
            selector = "#{}".format(qsEl.get_attribute("id"))
            paths = uiUtils.get_paths(self.driver, selector)
            assert (
                paths == self.expectedPaths
            ), "Quickshape paths error: {} != {}".format(paths, self.expectedPaths)

        self.log.info("SUCCESS")
        self.append_logs(self.driver.get_log("browser"))
        msg, warningsInLogs, summary = webdriverUtils.get_console_log_summary(
            self.browserLog
        )
        if warningsInLogs:
            self.log.warn(msg)
        else:
            self.log.info(msg)

        # TODO assert no js errors
        # assert summary["WARNING"] == 0, "{} Javascript warnings occured".format(summary["WARNING"])
        # assert summary["SEVERE"] == 0, "{} Javascript errors occured".format(summary["SEVERE"])
