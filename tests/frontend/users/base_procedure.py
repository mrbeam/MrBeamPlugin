import os
import pytest

from octoprint.settings import settings
from octoprint.users import FilebasedUserManager
from frontend import uiUtils
from frontend import webdriverUtils

settings(init=True)
base_folder = settings().getBaseFolder("base")
user_file_path = os.path.join(base_folder, 'users.yaml')

class BaseProcedure:

    @pytest.fixture()
    def enable_firstrun(self):
        settings().setBoolean(["server", "firstrun"], True)
        settings().save()

    def setup_class(self):
        self.file_based_user_manager = FilebasedUserManager()

    def teardown_class(selfself):
        if os.path.exists(user_file_path):
            os.remove(user_file_path)

    def setup(self):
        self.driver = webdriverUtils.get_chrome_driver()
        uiUtils.load_webapp(self.driver, 'http://0.0.0.0:5000/')

    def teardown(self):
        self.driver.quit()

