import logging

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from automations.skelbiu.definitions import LOGIN_URL
from core.extended_chrome_driver import ExtendedChromeDriver


class LoginPage:
    """
    Page object for login functionality.
    """

    # Locators
    USERNAME_INPUT = (By.ID, "nick-input")
    PASSWORD_INPUT = (By.ID, "password-input")
    LOGIN_BUTTON = (By.ID, "submit-button")
    # <p> with text "Neteisingi prisijungimo duomenys"
    ERROR_MESSAGE = (By.CLASS_NAME, "message")
    COOKIES_FORM_REJECT_BUTTON = (By.ID, "onetrust-reject-all-handler")

    def __init__(self, driver: ExtendedChromeDriver, logger: logging.Logger):
        self.driver = driver
        self.logger = logger

    def login(self, email, password):
        """
        Complete login flow - returns True if successful, False otherwise.
        """
        self.logger.info("Attempting to login...")
        self.navigate_to_login()
        self.enter_email(email)
        self.enter_password(password)
        self.click_login_button()
        return self.is_login_successful()

    def navigate_to_login(self):
        """
        Navigate to login page and reject cookies.
        """
        self.driver.get(LOGIN_URL)

        try:
            cookies_reject_btn = self.driver.wait.until(
                EC.presence_of_element_located(self.COOKIES_FORM_REJECT_BUTTON)
            )
            cookies_reject_btn.click()
            print("clicked 'reject all cookies'")
            self.logger.info("clicked 'reject all cookies'")
        except Exception:
            self.logger.exception("error when trying to reject cookies")

        self.driver.click_delay()

    def enter_email(self, email):
        """
        Enter email in the email field.
        """
        username_input = self.driver.wait.until(
            EC.visibility_of_element_located(self.USERNAME_INPUT)
        )
        username_input.clear()
        username_input.send_keys(email)
        self.driver.click_delay()

    def enter_password(self, password):
        """
        Enter password in the password field.
        """
        password_input = self.driver.wait.until(
            EC.visibility_of_element_located(self.PASSWORD_INPUT)
        )
        password_input.clear()
        password_input.send_keys(password)
        self.driver.click_delay()

    def click_login_button(self):
        """
        Click the login button, the current behaviour of the website is to
        then go to MY_ADS_URL.
        """
        login_btn = self.driver.wait.until(
            EC.visibility_of_element_located(self.LOGIN_BUTTON)
        )
        self.driver.move_to_and_click_element(login_btn)
        self.driver.click_delay()

    def is_login_successful(self) -> bool:
        """
        Check if login was successful by checking URL change.
        """
        try:
            self.driver.wait.until(
                lambda driver: "signin" not in driver.current_url.lower()
            )
            return True
        except TimeoutException:
            return False

    def get_error_message(self):
        """
        Get error message text if present.
        """
        try:
            error_element = self.driver.wait.until(
                EC.presence_of_element_located(self.ERROR_MESSAGE)
            )
            return error_element.text.strip()
        except TimeoutException:
            return None
