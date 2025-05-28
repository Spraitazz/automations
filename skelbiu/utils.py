
from skelbiu.definitions import *


def load_config(automation: WebAutomation):
    config = {}
    configfile = configparser.ConfigParser(interpolation=None)
    configfile.read(automation.config_fpath)
    config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
    config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
    config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
    config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
    automation.set_config(config)


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


def check_need_renew(stored_items: dict) -> bool:
    """Check if I need to go on site, I go if either:

    1. Any of my items have a last updated date > 25h ago
    2. Any of my items have an unknown last updated date

    """

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
            if (now - datetime_last_updated).total_seconds() > 90000.0:
                check_renew = True
                break
    return check_renew


#
# TO DO: get rid of items which are in stored_items but not in result
#
def update_items_store(automation: WebAutomation, stored_items: dict, result: dict):

    stored_items_cur = {}
    for item_id, status_dict in result.items():
        if status_dict["status"] == "renewed":
            stored_items_cur[item_id] = status_dict["last_renewed"]
            automation.logger.debug(
                f"updating item {item_id} renewed last: {status_dict['last_renewed']}"
            )
        else:
            # was already renewed
            if item_id in stored_items:
                stored_items_cur[item_id] = stored_items[item_id]
            else:
                stored_items_cur[item_id] = "-"

    automation.logger.debug(
        f"will write stored_items_cur: {stored_items_cur} to {MY_ITEMS_STORE_FPATH}"
    )
    with open(MY_ITEMS_STORE_FPATH, "w", encoding="utf-8") as f:
        json.dump(stored_items_cur, f)
