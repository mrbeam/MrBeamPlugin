import logging

import requests
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tests.frontend import uiUtils, webdriverUtils


class TestDevice:
    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        self.driver.quit()
        pass

    def test_homing(
        self,
        baseurl="http://mrbeam-5cf2.local",
        apikey="A4A486E0184A4407961F4CC5780E2B4C",  # api key of useraccount uiapikey don't work
    ):
        self.baseurl = baseurl

        logging.getLogger().info("baseurl %s", self.baseurl)
        self.testEnvironment = {}
        self.log = logging.getLogger()
        self.driver = webdriverUtils.get_chrome_driver()
        # try:
        # baseurl = "http://mrbeam-5cf2.local"
        self.testEnvironment = uiUtils.load_webapp(self.driver, self.baseurl)
        # except:
        #     self.log.error(
        #         "Error: No beamOS at '{}'. (Please set --baseurl=http://mrbeam-7E57.local e.g.)".format(
        #             baseurl
        #         )
        #     )

        # login
        uiapikey = uiUtils.login(self.driver)
        # close notifications
        uiUtils.close_notifications(self.driver)

        headers = {
            "Content-Type": "application/json",
            "x-api-key": apikey
            # the name may vary.  I got it from this doc: http://docs.octoprint.org/en/master/api/job.html
        }
        data = {"command": "reset"}  # notice i also removed the " inside the strings

        response = requests.post(
            self.baseurl + "/api/printer/command", headers=headers, json=data
        )
        # # if r.status_code not in (requests.codes.ok, requests.codes.no_content):
        # # laser.commands(["G90", "G0 X%.3f Y%.3f F%d" % (x, y, movement_speed)])
        # logging.getLogger().info("request {}".format(response))
        assert response.status_code == requests.codes.no_content or requests.codes.ok

        wait = WebDriverWait(self.driver, 20, poll_frequency=0.5)
        el = wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, "#mrb_state_header > span:nth-child(2) > span"),
                "Locked",
            ),
            "Waiting reset...",
        )
        assert uiUtils.ensure_device_homed(self.driver), "device homed"
