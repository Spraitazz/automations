
from skelbiu.definitions import *
from skelbiu.utils import login, check_need_renew, update_items_store
from skelbiu.renew_ads import renew_ads

if __name__ == "__main__":
    print("not supposed to be ran like this")
    exit(0)

#
# only go on site if:
#                    (A): I have no items in my item store
#                    (B): one of my items has not been renewed in more than 25h
#                    (C): one of my items has an unknown last renewed datetime ("-")
#
# item store is json file at [MY_ITEMS_STORE_FPATH in definitions.py]
#
def run(automation: WebAutomation):

    logger = automation.logger

    # create items store file if it does not exist
    Path(MY_ITEMS_STORE_FPATH).touch(exist_ok=True)

    # try load config
    config = {}    
    configfile = configparser.ConfigParser(interpolation=None)
    configfile.read(automation.config_fpath)
    try:
        config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
        config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
        config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
        config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
    except:
        logger.exception("config not ok")
        return

    automation.set_config(config)
    logger.debug("automation started")
    
    #
    # TO DO: wrap in try/except in WebAutomation - check for 
    #       selenium.common.exceptions.NoSuchDriverException: Message: Unable to obtain driver for chrome; 
    #       For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors/driver_location
    #
    driver = automation.init_webdriver()
    
    # load my items store: items for which I have a record already (when each item was last renewed)    
    stored_items = {}
    with open(MY_ITEMS_STORE_FPATH, "r", encoding="utf-8") as f:
        try:
            stored_items = json.load(f)
        except:
            #no items stored yet
            pass

    while not automation.stop_event.is_set():        
        
        if check_need_renew(stored_items):
            logger.debug("going to check my ads")
            
            if not login(automation):
                logger.error("could not login, sleeping for 60s before retry")
                automation.sleep(60.)
                continue
            
            result = renew_ads(automation)
            #
            # TO DO: SkelbiuAutomation extends WebAutomation and has func update_items_store()
            #        then will also look cleaner as wont need some of the other args (self.)
            #
            update_items_store(automation, stored_items, result)                
            automation.driver_try_get(DEFAULT_URL)
        else:
            logger.debug("will not check my ads this time")
            
        sleep_s = random.uniform(config["MIN_SLEEP_S"], config["MAX_SLEEP_S"])
        logger.debug(
            "going home to sleep for {:.1f} s".format(
                sleep_s
            )
        )
        automation.interruptable_sleep(sleep_s)

    logger.debug("stop event set by controller, returning")
