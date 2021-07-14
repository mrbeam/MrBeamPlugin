import os
import pytest

from octoprint.settings import settings
from frontend import uiUtils
from frontend import webdriverUtils

settings(init=True)
base_folder = settings().getBaseFolder("base")
config_file_path =  os.path.join(base_folder, 'config.yaml')
user_file_path = os.path.join(base_folder, 'users.yaml')

class BaseProcedure:

    @pytest.fixture()
    def enable_firstrun(self):
        settings().setBoolean(["server", "firstrun"], True)
        settings().save()

    @pytest.fixture()
    def disable_firstrun(self):
        settings().setBoolean(["server", "firstrun"], False)
        settings().save()

    def setup(self):
        self.driver = webdriverUtils.get_chrome_driver()
        uiUtils.load_webapp(self.driver, 'http://0.0.0.0:5000/')


    def teardown(self):
        # if os.path.exists(user_file_path):
        #     os.remove(user_file_path)
        pass
