import configparser
import logging
import random
from pathlib import Path

from selenium.common.exceptions import TimeoutException

from core.selenium_automation import SeleniumAutomation, DEFAULT_URL
from automations.skelbiu.definitions import BASE_DIR, MY_ITEMS_STORE_FPATH, MY_ADS_URL
from automations.skelbiu.item_store import ItemStore
from automations.skelbiu.items_page import ItemsPage
from automations.skelbiu.login_page import LoginPage


class SkelbiuAutomation(SeleniumAutomation):
    """
    Only go on site if:

        (A): I have no items in my item store
        (B): one of my items has not been renewed in more than 25h
        (C): one of my items has an unknown last renewed datetime ("-")

    Item store is managed by the ItemStore class.
    """

    NAME = "skelbiu"

    config: dict
    item_store: ItemStore
    login_page: LoginPage
    items_page: ItemsPage

    def __init__(self, config_path: Path):
        super().__init__(
            name=self.NAME,
            base_dir=BASE_DIR,
            config_path=config_path,
        )

    def setup(self, logger: logging.Logger):
        """
        Ensure that Page objects have access to an already setup
        logger and webdriver instance.
        """
        super().setup(logger)

        self.load_config()

        self.item_store = ItemStore(MY_ITEMS_STORE_FPATH, self.logger)
        self.item_store.load()

        self.login_page = LoginPage(self.driver, self.logger)
        self.items_page = ItemsPage(self.driver, self.logger)

    def load_config(self):
        config = {}
        configfile = configparser.ConfigParser(interpolation=None)
        configfile.read(self.config_path)
        config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
        config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
        config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
        config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
        self.config = config

    def run(self):
        """
        Check if any of my ads need renewal, if they do - run a renewal cycle,
        if not - sleep for a random amount of time between
        config["MIN_SLEEP_S"] and config["MAX_SLEEP_S"] before checking again.
        """

        if self.item_store.check_needs_renewal():
            self.logger.info("Going to check my ads")
            self.run_cycle()
        else:
            self.logger.info("Not checking my ads this time")

        sleep_s = random.uniform(self.config["MIN_SLEEP_S"], self.config["MAX_SLEEP_S"])
        self.logger.info(f"going home ({DEFAULT_URL}) to sleep for {sleep_s:.1f} s")
        self.driver.get(DEFAULT_URL)
        self.sleep(sleep_s)

    def run_cycle(self):
        """
        Login, check and renew items.
        """
        self.logger.info("Starting item renewal cycle")

        if not self.check_logged_in():
            if not self.perform_login():
                self.logger.error("Could not login, will retry later")
                return False
        else:
            self.logger.debug("Already logged in")

        if not self.check_and_renew_items():
            self.logger.error("Failed to check/renew items")
            return False

        self.logger.info("Item renewal cycle completed successfully")
        return True

    def check_logged_in(self):
        self.driver.get(MY_ADS_URL)

        try:
            self.driver.wait.until(
                lambda driver: "signin" not in driver.current_url.lower()
            )
            self.logger.debug("already logged in")
            return True
        except TimeoutException:
            return False

    def perform_login(self):
        try:
            success = self.login_page.login(self.config["EMAIL"], self.config["PASS"])

            if success:
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed")
                self.take_screenshot("perform_login_error")
                return False

        except Exception:
            self.logger.exception("Exception during login")
            return False

    def check_and_renew_items(self):
        """Check items and renew if necessary"""
        try:
            renew_result = self.items_page.check_and_renew()
            self.item_store.update_from_renewal_result(renew_result)
            return True
        except Exception as e:
            self.logger.error(f"Exception during item renewal: {e}")
            self.take_screenshot("item_renewal_error")
            return False
