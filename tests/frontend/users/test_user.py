import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By

from frontend.users.base_procedure import BaseProcedure


class TestUser(BaseProcedure):

    @pytest.mark.parametrize("username, password", [
        ('sherif@gmail.com', 'secret'),
        # ('hussien', 'secret'),
    ])
    @pytest.mark.usefixtures('enable_firstrun', as_attrs=False)
    def test_add_user(self, username, password):

        self.driver.find_element(By.NAME, 'next').click()

        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_username').send_keys(username)
        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_pw1').send_keys(password)
        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_pw2').send_keys(password)

        self.driver.find_element(By.NAME, 'next').click()


