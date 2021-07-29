import pytest
import octoprint.users

from selenium import webdriver
from selenium.webdriver.common.by import By

from frontend.users.base_procedure import BaseProcedure


class TestUser(BaseProcedure):

    # only one user can be created
    @pytest.mark.skip
    @pytest.mark.parametrize("username, password", [
        ('sherif@gmail.com', 'secret'),
    ])
    @pytest.mark.usefixtures('enable_firstrun', as_attrs=False)
    def test_add_user(self, username, password):

        self.driver.find_element(By.NAME, 'next').click()

        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_username').send_keys(username)
        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_pw1').send_keys(password)
        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_pw2').send_keys(password)

        self.driver.find_element(By.NAME, 'next').click()

        self.file_based_user_manager._load()
        assert self.file_based_user_manager.findUser(userid=username) is not None


    @pytest.mark.parametrize("username, password", [
        ('sherif@gmail.com', 'secret'),
    ])
    @pytest.mark.usefixtures('disable_firstrun', as_attrs=False)
    def test_login_user(self, username, password):

        self.driver.find_element(By.ID, 'login_screen_email_address_in').send_keys(username)
        self.driver.find_element(By.ID, 'login_screen_password_in').send_keys(password)

        js = 'return mrbeam.viewModels.loginScreenViewModel.loginState.loggedIn();'

        assert self.driver.execute_script(js) == False
        self.driver.find_element(By.ID, 'login_screen_login_btn').click()
        assert self.driver.execute_script(js) == True



