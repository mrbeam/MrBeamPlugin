import pytest
import octoprint.users

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from frontend.users.base_procedure import BaseProcedure


class TestUser(BaseProcedure):

    # only one user can be created
    @pytest.mark.parametrize("username, password", [
        ('dev@mr-beam.org', '1'),
    ])
    @pytest.mark.usefixtures('enable_firstrun', as_attrs=True)
    def test_add_user(self, username, password):

        self.driver.find_element(By.NAME, 'next').click()

        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_username').send_keys(username)
        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_pw1').send_keys(password)
        self.driver.find_element(By.ID, 'wizard_plugin_corewizard_acl_input_pw2').send_keys(password)

        self.driver.find_element(By.NAME, 'next').click()

        self.file_based_user_manager._load()
        assert self.file_based_user_manager.findUser(userid=username) is not None


    @pytest.mark.parametrize("username, password", [
        ('dev@mr-beam.org', '1'),
    ])
    def test_login_user(self, username, password):

        js = 'return mrbeam.viewModels.loginScreenViewModel.loginState.loggedIn();'
        assert self.driver.execute_script(js) == False

        # login
        self.driver.find_element(By.ID, 'login_screen_email_address_in').send_keys(username)
        self.driver.find_element(By.ID, 'login_screen_password_in').send_keys(password)
        self.driver.find_element(By.ID, 'login_screen_login_btn').click()

        assert self.driver.execute_script(js) == True

        # safety wizard
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, 'next'))).click()

        for checkbox in self.driver.find_elements(By.XPATH, "//div[@id='wizard_plugin_corewizard_lasersafety']//input"):
            checkbox.click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, 'next'))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, 'finish'))).click()

        # hide all alerts
        for alert in self.driver.find_elements(By.XPATH, "//div[@role='alert']"):
            self.driver.execute_script("arguments[0].style.display = 'none';", alert)

        # logout
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//li[@id='navbar_login']/a"))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@id='logout_button']"))).click()

        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@id='loginscreen_dialog']")))

        assert self.driver.execute_script(js) == False
