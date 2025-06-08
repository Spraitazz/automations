from linkedin.definitions import *


def login(automation: WebAutomation):

    logger = automation.logger
    driver = automation.driver
    config = automation.config

    logger.debug("going to log in")
    automation.driver_try_get(LOGIN_URL)
    click_delay()

    #
    # TO DO: wait for either "username" element, or for feed activity divs
    # then check url, driver.current_url: MUST BE EITHER LOGIN_URL OR FEED_URL,
    # otherwise raise exception?
    #

    # get "Remember me" checkbox, CHECKED BY DEFAULT
    # <input name="rememberMeOptIn" id="rememberMeOptIn-checkbox" class="large-input" checked="" value="true" type="checkbox">
    # if value="true" - click to uncheck, wait a sec, check that value="false", if true: proceed

    username_inp = driver.find_element(By.ID, "username")
    username_inp.clear()
    username_inp.send_keys(config["EMAIL"])
    click_delay()

    pass_inp = driver.find_element(By.ID, "password")
    pass_inp.clear()
    pass_inp.send_keys(config["PASS"])
    click_delay()

    submit_btn = driver.find_element(By.CSS_SELECTOR, ".btn__primary--large")
    submit_btn.click()
    logger.debug("clicked log in")
