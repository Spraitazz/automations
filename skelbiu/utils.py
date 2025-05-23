from skelbiu.definitions import *


def click_delay(min: float = CLICK_DELAY_MIN, max: float = CLICK_DELAY_MAX):
    time.sleep(random.uniform(min, max))


def login(automation: WebAutomation):

    logger = automation.logger
    driver = automation.driver
    config = automation.config

    logger.debug("logging in")
    automation.driver_try_get(LOGIN_URL)
    click_delay()

    # check if logged in already, then bypass
    if "signin" not in driver.current_url:
        logger.debug("already logged in")
        return

    # reject cookies first
    target = driver.find_element(By.ID, "onetrust-reject-all-handler")
    target.click()
    click_delay()

    username_inp = driver.find_element(By.ID, "nick-input")
    username_inp.clear()
    username_inp.send_keys(config["EMAIL"])
    click_delay()

    pass_inp = driver.find_element(By.ID, "password-input")
    pass_inp.clear()
    pass_inp.send_keys(config["PASS"])
    click_delay()

    submit_btn = driver.find_element(By.ID, "submit-button")
    submit_btn.click()
    logger.debug("clicked login")
    click_delay()
