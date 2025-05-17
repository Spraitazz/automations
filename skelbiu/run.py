from definitions import DEFAULT_URL, DEFAULT_BROWSER_OPTIONS
from skelbiu.definitions import *
from skelbiu.utils import login
from skelbiu.renew_ads import renew_ads

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
        config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
        config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
        config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
        config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
    except:
        logger.exception(f"{automation.name} automation config not ok")
        return

    automation.set_config(config)
    logger.debug(f"{automation.name} automation started")

    driver = webdriver.Chrome(options=DEFAULT_BROWSER_OPTIONS)
    automation.set_driver(driver)

    while not automation.stop_event.is_set():
        login(automation)
        renew_ads(automation)
        automation.driver_try_get(DEFAULT_URL)
        sleep_s = random.uniform(config["MIN_SLEEP_S"], config["MAX_SLEEP_S"])
        logger.debug(
            "going to sleep for {:.1f} s until next checking ads to renew".format(
                sleep_s
            )
        )
        automation.interruptable_sleep(sleep_s)

    logger.debug("stop event set by controller, returning")
