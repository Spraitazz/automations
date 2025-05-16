#
#
# Login, go to feed
# Repeat forever: refresh feed, respond to a random few posts, go to sleep for random time
#
#
from linkedin.definitions import *
from linkedin.utils import (
    click_delay,
    launch_browser,
    login,
    respond_comments,
    send_unhandled_exception_email,
)
from xvfbwrapper import Xvfb

BOT_NAME = "linkedin"

# setup logger to generate a file daily, keeping last 7 days backup
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(LOG_PATH, when="midnight", backupCount=7)
handler.suffix = "%Y%m%d"
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


DEFAULT_URL = "http://diedai.lt"


def run():

    try:

        logger.debug("linkedin bot started")

        with Xvfb(display=3, width=2560, height=1600) as xvfb:
            driver = launch_browser()
            login(driver)
            click_delay()

            responded_posts = []
            while True:
                #
                # TO DO: wait until feed page is loaded
                #
                logger.debug("checking for new posts to respond to")
                responded_posts = respond_comments(
                    driver, responded_posts=responded_posts
                )
                sleep_time = random.uniform(MIN_SLEEP_S, MAX_SLEEP_S)
                logger.debug(
                    "going to sleep for {:.1f} s until next checking".format(sleep_time)
                )
                driver.get(DEFAULT_URL)
                time.sleep(sleep_time)
                driver.get(FEED_URL)
                # driver.refresh()

    except KeyboardInterrupt:
        # ctrl+c to kill still works
        return
    except:
        # send email, then restart
        logger.exception("")
        logger.debug("sending unhandled exception email")
        send_unhandled_exception_email(BOT_NAME)
        time.sleep(10.0)
        # driver.quit()
        run()


if __name__ == "__main__":
    run()
