
from skelbiu.definitions import *


#
# TO DO: pass automation (SkelbiuAutomation?) as need driver_try_click
#           and also need logger
#
class LoginPage:
    """Page Object for Login functionality"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S)
        
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
            cookies_reject_btn = self.wait.until(EC.presence_of_element_located(self.COOKIES_FORM_REJECT_BUTTON))
            cookies_reject_btn.click()
            print("clicked 'reject all cookies'")
            #logger.debug("clicked 'reject all cookies'")
        except:
            print("did not need to reject cookies")
            #logger.warning("did not need to reject cookies")
            pass
        click_delay()
        return self
    
    def enter_email(self, email):
        """Enter email in the email field"""
        email_field = self.wait.until(EC.presence_of_element_located(self.USERNAME_INPUT))
        email_field.clear()
        email_field.send_keys(email)
        click_delay()
        return self
    
    def enter_password(self, password):
        """Enter password in the password field"""
        password_field = self.wait.until(EC.presence_of_element_located(self.PASSWORD_INPUT))
        password_field.clear()
        password_field.send_keys(password)
        click_delay()
        return self
    
    def click_login_button(self):
        """
        Click the login button, the current behaviour of the website is to
        then go to MY_ADS_URL
        """
        login_btn = self.wait.until(EC.element_to_be_clickable(self.LOGIN_BUTTON))
        login_btn.click()
        click_delay()
        return self
    
    #
    # TODO: ideally should wait for username, pass and login btn to be visible OR url not having signin
    #    
    def check_logged_in(self):
        #automation.driver_try_get(LOGIN_URL)
        self.navigate_to_login()
        # check if logged in already, then bypass
        try:
            self.wait.until(lambda driver: "signin" not in driver.current_url.lower())
            #logger.debug("already logged in")
            return True
        except TimeoutException:
            return False
    
    #
    # TODO: return True if logged in ok, false otherwise
    #
    def login(self, email, password):
        """Complete login flow"""
        self.enter_email(email)
        self.enter_password(password)
        self.click_login_button()        
        return self
    
    def get_error_message(self):
        """Get error message text if present"""
        try:
            error_element = self.wait.until(EC.presence_of_element_located(self.ERROR_MESSAGE))
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


"""
def login(automation: WebAutomation):

    logger = automation.logger
    driver = automation.driver
    config = automation.config

    logger.info("logging in")
    automation.driver_try_get(LOGIN_URL)
    click_delay()

    # check if logged in already, then bypass
    if "signin" not in driver.current_url:
        logger.debug("already logged in")
        return True

    # reject cookies first
    try:
        target = driver.find_element(By.ID, "onetrust-reject-all-handler")
        target.click()
        click_delay()
        logger.debug("clicked 'reject all cookies'")
    except:
        logger.warning("did not need to reject cookies")

    username_inp = driver.find_element(By.ID, "nick-input")
    username_inp.clear()
    username_inp.send_keys(config["EMAIL"])
    click_delay()

    pass_inp = driver.find_element(By.ID, "password-input")
    pass_inp.clear()
    pass_inp.send_keys(config["PASS"])
    click_delay()

    submit_btn = driver.find_element(By.ID, "submit-button")
    clicked = automation.driver_try_click(submit_btn)  # .click()
    #
    # TO DO: can also add check if offending elem was deleted, or keep trying to click
    #        until all offending elems are gone
    #
    if not clicked:
        # the offending element should be deleted now, try click again
        try:
            submit_btn.click()
        except:
            logger.exception("still could not click login on 2nd try")
            return False

    logger.debug("clicked login")
    click_delay()
    return True
"""
