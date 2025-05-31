from skelbiu.definitions import *
from skelbiu.utils import (
    load_config,
    load_item_store,
    check_need_renew,
    update_item_store,
)
from skelbiu.login import LoginPage #, login
from skelbiu.renew_ads import renew_ads


def run(automation: WebAutomation):
    """
    only go on site if:

    (A): I have no items in my item store
    (B): one of my items has not been renewed in more than 25h
    (C): one of my items has an unknown last renewed datetime ("-")

    item store is json file at [MY_ITEMS_STORE_FPATH in definitions.py]
    """

    logger = automation.logger
    try:
        load_config(automation)
    except:
        logger.exception(f"config not ok")
        return
    logger.info(f"automation started")

    driver = automation.init_webdriver()

    # load my item store: 
    stored_items = load_item_store()
    
    login_page = LoginPage(driver)

    while not automation.stop_event.is_set():

        if check_need_renew(stored_items):
            logger.info("going to check my ads")

            if not login_page.login():
                logger.error("could not login, sleeping for 60s before retry")
                automation.sleep(60.0)
                continue

            result = renew_ads(automation)
            #
            # TO DO: SkelbiuAutomation extends WebAutomation and has func update_items_store()
            #        then will also look cleaner as wont need some of the other args (self.)
            #
            update_item_store(automation, stored_items, result)
            automation.driver_try_get(DEFAULT_URL)
        else:
            logger.info("will not check my ads this time")

        sleep_s = random.uniform(
            automation.config["MIN_SLEEP_S"], automation.config["MAX_SLEEP_S"]
        )
        logger.info("going home to sleep for {:.1f} s".format(sleep_s))
        automation.sleep(sleep_s)

    logger.debug("stop event set by controller, returning")
