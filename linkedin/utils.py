
from linkedin.definitions import *


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


def click_delay(min=2.0, max=4.0):
    time.sleep(random.uniform(min, max))


def launch_browser() -> webdriver:
    driver = webdriver.Chrome(options=DEFAULT_BROWSER_OPTIONS)
    return driver

def random_scroll(driver: ChromeDriver):    
    """Scroll down a random amount, function can run anywhere from 0.75s to 30s"""
    for _ in range(random.choice([3, 5, 10])):
        scroll_y = random.randint(50, 300)
        driver.execute_script(f"window.scrollBy(0, {scroll_y});")
        time.sleep(random.uniform(0.25, 3.0))
        
        



def login(driver: webdriver):
    #
    # TO DO: replace with automation.driver_try_get(LOGIN_URL)
    #
    driver.get(LOGIN_URL)
    click_delay()
    
    #
    # TO DO: wait for either "username" element, or for feed activity divs
    # then check url, driver.current_url: MUST BE EITHER LOGIN_URL OR FEED_URL, 
    # otherwise raise exception?
    #
    
    """
    try:
        WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "slot")) >= 2
        )
    except TimeoutException:
        logger.warning("couldnt find by class_name 'slot'")
        
    """

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


def wait_feed_loaded(driver: ChromeDriver):
    """Wait up to DEFAULT_LOAD_WAIT_TIME_S for FEED_URL to be loaded 
    (for activities like posts, comments etc. to appear)"""

    this_elem = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@data-id, 'urn:li:activity')]")
            )
    )

def remove_non_bmp(text: str) -> str:
    return "".join(c for c in text if ord(c) <= 0xFFFF)



