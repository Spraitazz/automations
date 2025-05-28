
from linkedin.definitions import *


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


def get_session_name(start_time_range: dict[str, Tuple[int, int]]) -> str:
    
    session_name = ""
    
    current_hour = datetime.now().hour    
    for name, hour_range in start_time_range.items():
        if hour_range[0] <= current_hour < hour_range[1]:
            session_name = name
            break
        
    return session_name


def time_until_next_session(start_time_range: dict) -> float:
    """return time to sleep (in seconds) until next session"""


    now = datetime.now()
    current_hour = now.hour

    # Sort sessions by start hour ascending
    sessions_sorted = sorted(start_time_range.items(), key=lambda x: x[1][0])
    num_sessions = len(sessions_sorted)

    # Find the next session start after now
    next_session = None
    for i, (name, (start_hour, end_hour)) in enumerate(sessions_sorted):
        if current_hour < start_hour:
            next_session = (name, start_hour, end_hour)
            break
        elif start_hour <= current_hour < end_hour:
            if i != num_sessions - 1:
                next_session = (sessions_sorted[i+1][0], *sessions_sorted[i+1][1])
                break

    # If no next session today, pick the first session tomorrow
    if next_session is None:
        name, (start_hour, end_hour) = sessions_sorted[0]
        # Calculate next session start as tomorrow at start_hour
        next_session_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
        sleep_seconds = (next_session_start - now).total_seconds()
        # Then add a random offset within the session duration (in seconds)
        sleep_seconds += random.uniform(0, (end_hour - start_hour) * 3600)
        return sleep_seconds
        

    # get time to sleep until next session start + random offset
    name, start_hour, end_hour = next_session
    next_session_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    sleep_seconds = (next_session_start - now).total_seconds()
    sleep_seconds += random.uniform(0, (end_hour - start_hour) * 3600)

    return sleep_seconds




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



