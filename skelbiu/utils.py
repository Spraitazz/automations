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
 
# check if I want to go to site
def check_need_renew(stored_items: dict) -> bool:  

    check_renew = False        
    
    if len(stored_items) == 0:
        check_renew = True
    else:
        now = datetime.now()
        for item_id_str, last_updated_str in stored_items.items():
            if len(last_updated_str) < 2: 
                check_renew = True
                break
            datetime_last_updated = datetime.fromisoformat(last_updated_str)
            if (now-datetime_last_updated).total_seconds() > 90000.:
                check_renew = True
                break
    return check_renew
        
               
    
def update_items_store(stored_items: dict, result: dict):
    stored_items_cur = {}            
    for item_id, status_dict in result.items():
        if status_dict["status"] == "renewed":
            # item freshly renewed
            stored_items_cur[item_id] = status_dict["last_renewed"]
        else:
            # has already been renewed when checking
            if item_id in stored_items:
                stored_items_cur[item_id] = stored_items[item_id]
            else:
                stored_items_cur[item_id] = "-"
    with open(MY_ITEMS_STORE_FNAME, "w", encoding="utf-8") as f:
        json.dump(stored_items_cur, f)
