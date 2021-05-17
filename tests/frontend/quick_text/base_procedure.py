from frontend import uiUtils
from frontend import webdriverUtils
from frontend import frontendTestUtils


class BaseProcedure:
    def setup_method(self, method):
        # expectations (None means skip)
        self.expectedPaths = None
        self.expectedBBox = None
        raise NotImplementedError("Subclasses must override setup_method()!")

    def get_quick_text(self):
        raise NotImplementedError("Subclasses must override get_quick_text()!")

    def teardown_method(self, method):
        self.driver.quit()
        pass

    def append_logs(self, logs):
        self.browserLog.extend(logs)

    def test_quick_text(self, baseurl, rsc_folder):
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

        # add a quick text
        qsEl, listEl = self.get_quick_text()

        # check dimensions & position
        if self.expectedBBox:
            bbox = uiUtils.get_bbox(self.driver)
            ok, msg = frontendTestUtils.compare_dimensions(bbox, self.expectedBBox)
            assert ok, msg
            self.log.info("DIMENSIONS OK")

        # check path
        if self.expectedText:
            selector = "#{}".format(qsEl.get_attribute("id"))
            text = uiUtils.get_text(self.driver, selector)
            assert (
                text == self.expectedText["text"]
            ), "Quicktext text error: {} != {}".format(text, self.expectedText["text"])
            fill = uiUtils.get_text_fill(self.driver, selector)

            assert (
                fill == self.expectedText["fill"]
            ), "Quicktext fill error {} != {}".format(fill, self.expectedText["fill"])
            style = uiUtils.get_text_style(self.driver, selector)

            assert style["value"].index(
                self.expectedText["font-family"]
            ), "Quicktext font error {} != {}".format(
                style["value"], self.expectedText["font-family"]
            )

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
