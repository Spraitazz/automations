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

from spires.definitions import *
from spires.utils import load_config, get_supported_currencies, login
from spires.bids import bid_jobs
from spires.messages import check_messages


if __name__ == "__main__":
    print("not supposed to be ran like this")
    exit(0)


def run(automation: WebAutomation):

    logger = automation.logger
    config = {}
    try:
        config = load_config(automation)
    except:
        logger.exception(f"config not ok")
        return
    

    automation.set_config(config)
    logger.debug(f"automation started")

    #
    # TO DO: supported_currencies = get_supported_currencies(logger) ???
    #
    supported_currencies = []
    num_tries_max = 3
    retry_sleep_s = 10.
    i_try = 0    
    while i_try < num_tries_max:
        try:
            supported_currencies = get_supported_currencies(logger)
            break
        except requests.ConnectionError:
            logger.warning(f"connection error on try {i_try}/{num_tries_max}, will retry in {retry_sleep_s} s")
            automation.interruptable_sleep(retry_sleep_s)
            i_try += 1       

    if len(supported_currencies) == 0:
        logger.error("supported currencies were not retrieved, cannot bid")
        return

    driver = automation.init_webdriver()

    login(automation)

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
                automation.driver_try_get(MESSAGES_URL)
                chats_seen = check_messages(automation, chats_seen=chats_seen)
            except:
                logger.exception("")

        automation.driver_try_get(DEFAULT_URL)
        sleep_s = random.uniform(config["MIN_SLEEP_S"], config["MAX_SLEEP_S"])
        logger.debug("returned home and going to sleep for {:.1f} s".format(sleep_s))
        automation.interruptable_sleep(sleep_s)
        automation.driver_try_get(HOME_URL)

    logger.debug("stop event set by controller, returning")
