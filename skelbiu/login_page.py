from skelbiu.definitions import *


class LoginPage:
    """Page Object for Login functionality"""

    def __init__(self, automation: WebAutomation):
        self.logger = automation.logger
        self.driver = automation.driver
        self.wait = WebDriverWait(self.driver, DEFAULT_LOAD_WAIT_TIME_S)

    # Locators
    USERNAME_INPUT = (By.ID, "nick-input")
    PASSWORD_INPUT = (By.ID, "password-input")
    LOGIN_BUTTON = (By.ID, "submit-button")
    # <p> with text "Neteisingi prisijungimo duomenys"
    ERROR_MESSAGE = (By.CLASS_NAME, "message")
    COOKIES_FORM_REJECT_BUTTON = (By.ID, "onetrust-reject-all-handler")

    def navigate_to_login(self):
        """Navigate to login page"""
        self.driver.get(LOGIN_URL)
        # reject cookies first
        try:
            cookies_reject_btn = self.wait.until(
                EC.presence_of_element_located(self.COOKIES_FORM_REJECT_BUTTON)
            )
            cookies_reject_btn.click()
            print("clicked 'reject all cookies'")
            self.logger.info("clicked 'reject all cookies'")
        except:
            pass
        click_delay()
        return self

    def enter_email(self, email):
        """Enter email in the email field"""
        email_field = self.wait.until(
            EC.presence_of_element_located(self.USERNAME_INPUT)
        )
        email_field.clear()
        email_field.send_keys(email)
        click_delay()
        return self

    def enter_password(self, password):
        """Enter password in the password field"""
        password_field = self.wait.until(
            EC.presence_of_element_located(self.PASSWORD_INPUT)
        )
        password_field.clear()
        password_field.send_keys(password)
        click_delay()
        return self

    def click_login_button(self):
        """
        Click the login button, the current behaviour of the website is to
        then go to MY_ADS_URL.
        """

        login_btn = self.wait.until(EC.element_to_be_clickable(self.LOGIN_BUTTON))
        login_btn.click()
        click_delay()
        return self

    #
    # TODO: check if at login url?
    #
    def login(self, email, password):
        """
        Complete login flow - returns True if successful, False otherwise.

        Must start at LOGIN_URL.
        """

        try:
            self.enter_email(email)
            self.enter_password(password)
            self.click_login_button()

            # Check if login was successful
            return self.is_login_successful()
        except Exception as e:
            self.logger.error(f"Exception during login: {e}")
            return False

    def get_error_message(self):
        """Get error message text if present"""
        try:
            error_element = self.wait.until(
                EC.presence_of_element_located(self.ERROR_MESSAGE)
            )
            return error_element.text.strip()
        except TimeoutException:
            return None

    def is_login_successful(self):
        """Check if login was successful by checking URL change"""
        try:
            # Wait for URL to change
            self.wait.until(lambda driver: "signin" not in driver.current_url.lower())
            return True
        except TimeoutException:
            return False
