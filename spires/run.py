#
# This bot lurks on the bids (default) page, bidding on jobs of interest the correct amount in the client's given currency
# and sends a generic message (GENERIC_BID_MSG_PLACEHOLDER formatted with student name)
# apply/remove bids until none, then random sleep (5-10 mins), refresh and repeat
#


#
# login (if not logged in already)
#
# repeat
# go to bids
# go to messages
# leave
# repeat
#
from definitions import DEFAULT_URL, DEFAULT_BROWSER_OPTIONS
from spires.definitions import *
from spires.utils import get_supported_currencies, login
from spires.bids import bid_jobs
from spires.messages import check_messages


if __name__ == "__main__":
    print("not supposed to be ran like this")
    exit(0)


def run(automation: WebAutomation):

    logger = automation.logger
    config = {}

    # try load config
    configfile = configparser.ConfigParser(interpolation=None)
    configfile.read(automation.config_fpath)
    try:
        config["TUTOR_NAME"] = configfile["DEFAULT"]["TUTOR_NAME"].strip().strip('"')
        config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
        config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
        config["CURRENCY_API_KEY"] = (
            configfile["DEFAULT"]["CURRENCY_API_KEY"].strip().strip('"')
        )
        config["MY_CURRENCY"] = configfile["DEFAULT"]["MY_CURRENCY"].strip().strip('"')
        config["MY_DEGREES"] = json.loads(configfile["DEFAULT"]["MY_DEGREES"])
        config["MY_SUBJECTS"] = json.loads(configfile["DEFAULT"]["MY_SUBJECTS"])
        config["MY_BIDS"] = json.loads(configfile["DEFAULT"]["MY_BIDS"])
        config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
        config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
        config["RESPOND_MESSAGES"] = configfile.getboolean(
            "DEFAULT", "RESPOND_MESSAGES", fallback=False
        )
    except:
        logger.exception(f"{AUTOMATION_NAME} automation config not ok")
        return

    automation.set_config(config)
    logger.debug(f"{AUTOMATION_NAME} automation started")

    supported_currencies = get_supported_currencies(logger)
    if len(supported_currencies) == 0:
        logger.error("supported currencies were not retrieved, cannot bid")
        return

    driver = webdriver.Chrome(options=DEFAULT_BROWSER_OPTIONS)
    automation.set_driver(driver)

    login(driver, config, logger)

    #
    # TO DO: I couldnt be doing this forever, RAM runs out, what do?
    #
    chats_seen = []

    while not automation.stop_event.is_set():

        logger.debug("checking for new jobs")
        try:
            bid_jobs(driver, supported_currencies, config, logger)
        except:
            logger.exception("")
        #
        # TO DO: from bids page, it would look more natural if we click on messages instead of go to url
        #
        if config["RESPOND_MESSAGES"]:
            try:
                logger.debug("checking for new messages from students")
                driver.get(MESSAGES_URL)
                chats_seen = check_messages(automation, chats_seen=chats_seen)
            except:
                logger.exception("")

        driver.get(DEFAULT_URL)
        sleep_s = random.uniform(config["MIN_SLEEP_S"], config["MAX_SLEEP_S"])
        logger.debug("returned home and going to sleep for {:.1f} s".format(sleep_s))
        automation.interruptable_sleep(sleep_s)
        driver.get(HOME_URL)

    logger.debug("stop event set by controller, returning")
