
from linkedin.definitions import *

"""
def send_unhandled_exception_email(bot_name: str):

    from_email = APP_EMAIL
    to_email = UNHANDLED_EXCEPTION_EMAIL

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = f"{bot_name} unhandled exception"

    body = "look at logs"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(APP_EMAIL, GMAIL_APP_PASS)
        server.sendmail(from_email, to_email, msg.as_string())
"""

#
# TO DO: automation.click_delay
#           ALSO IF READING THIS: centralise all convenience funcs like this, use interruptable here
#
def click_delay(min=2.0, max=4.0):
    time.sleep(random.uniform(min, max))

#
# TO DO: pass WebAutomation instance and use automation.sleep
#
def random_scroll(driver: ChromeDriver, scroll_up: bool = False):    
    """Scroll up or down a random amount, function can run anywhere from 3s to 60s"""
    
    for _ in range(random.choice([3, 5, 10])):
        scroll_y = random.randint(50, 300)
        if scroll_up:
            scroll_y *= -1
        driver.execute_script(f"window.scrollBy(0, {scroll_y});")
        time.sleep(random.uniform(1.0, 6.0))

#
# TO DO: pass WebAutomation instance
#
def scroll_pretend_read(driver: ChromeDriver):
    """random scroll either up (p = 0.4) or down (p = 0.6) a few
    (currently hardcoded 6) times, pretending to read"""
    
    for _ in range(6):
        if random.uniform(0., 1.) > 0.4:
            random_scroll(driver)
        else:
            random_scroll(driver, scroll_up=True)


def remove_non_bmp(text: str) -> str:
    return "".join(c for c in text if ord(c) <= 0xFFFF)        



def login(automation: WebAutomation):
    
    logger = automation.logger
    driver = automation.driver
    
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
    username_inp.send_keys(EMAIL)
    click_delay()

    pass_inp = driver.find_element(By.ID, "password")
    pass_inp.clear()
    pass_inp.send_keys(PASS)
    click_delay()

    submit_btn = driver.find_element(By.CSS_SELECTOR, ".btn__primary--large")
    submit_btn.click()
    logger.debug("clicked log in")

#
# TO DO: probably dont need this as a separate func?
#
def wait_feed_loaded(driver: ChromeDriver):
    """Wait up to DEFAULT_LOAD_WAIT_TIME_S for FEED_URL to be loaded 
    (for activities like posts, comments etc. to appear)"""

    this_elem = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@data-id, 'urn:li:activity')]")
            )
    )


def go_to_feed(automation: WebAutomation) -> bool:
    """Check if I am not on feed, then go to feed, returning bool
    indicating whether I am finally on feed (or otherwise, if returned
    False, might indicate internet problems)."""
    
    # check I am actually at feed page
    if automation.driver.current_url.strip() == FEED_URL:
        return True
    else:
        automation.driver_try_get(FEED_URL)
    
    # make sure feed is loaded
    try:
        wait_feed_loaded(automation.driver)  
        return True
    except:
        logger.warning(f"feed did not load in {DEFAULT_LOAD_WAIT_TIME_S} seconds")
        return False



