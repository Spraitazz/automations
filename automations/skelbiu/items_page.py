import logging
from datetime import datetime

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from automations.skelbiu.definitions import BASE_URL, MY_ADS_URL
from automations.skelbiu.renewal_status import RenewalStatus
from core.extended_chrome_driver import ExtendedChromeDriver


def get_renew_item_div_selector(item_id: str) -> tuple[str, str]:
    return By.ID, f"renewID{item_id}"


class ItemsPage:
    """
    Page object for item listing functionality.
    """

    # Locators
    ITEMS_TABLE = (By.ID, "adsList")  # Container for all items

    # Locators (renew page, {BASE_URL}/ad/renew/{item_id})
    RENEW_PAGE_CHOICES = (By.CLASS_NAME, "slot")
    # "uzsakyti nemokamai" -> click
    FREE_RENEW_DIV = (By.ID, "full-price")

    # Fallback url if cannot click "Atnaujinti" on ads page for some reason
    ITEM_RENEW_URL_FORMATTER = BASE_URL + "/ad/renew/{}"

    def __init__(self, driver: ExtendedChromeDriver, logger: logging.Logger):
        self.driver = driver
        self.logger = logger

    def check_and_renew(self) -> dict[str, dict]:
        """
        Check if any of my ads need renewing, and renew them.

        Returns dict with items like {item_id: status_dict}, where
        status_dict contains:
        - 'status': RenewalStatus enum value
        - 'last_renewed': ISO format datetime string (only if status is RENEWED)
        """
        result = {}

        self.logger.info("Navigating to items page...")
        self.navigate_to_items()

        items_need_renewal = self.get_items_states()

        for item_id, needs_renewal in items_need_renewal.items():
            if not needs_renewal:
                self.logger.debug(f"item with id {item_id} is already renewed.")
                result[item_id] = {"status": RenewalStatus.ALREADY_RENEWED}
                continue

            if self.renew_item(item_id):
                self.logger.info(f"Successfully renewed item: {item_id}")
                result[item_id] = {
                    "status": RenewalStatus.RENEWED,
                    "last_renewed": datetime.now().isoformat(),
                }
            else:
                self.logger.error(f"Failed to renew item: {item_id}")
                result[item_id] = {"status": RenewalStatus.FAILED}

        return result

    def navigate_to_items(self) -> bool:
        """
        Navigate to items/ads page

        Returns: bool indicating whether items are loaded
        """
        self.driver.get(MY_ADS_URL)
        return self.wait_for_items_to_load()

    def wait_for_items_to_load(self) -> bool:
        """
        Wait for items container to be present

        Returns: bool indicating whether items are loaded
        """
        try:
            self.driver.wait.until(EC.presence_of_element_located(self.ITEMS_TABLE))
            return True
        except TimeoutException:
            self.logger.warning(
                "Items container not found, page might not have loaded properly"
            )
            return False

    def get_items_states(self) -> dict[str, bool]:
        """
        Return, for each item in my ads, whether the item needs renewal
        as a dict with (key, value) = (item_id, needs_renewal_bool)
        """
        items_need_renewal = {}
        items_idx = self.get_all_items()

        for item_id in items_idx:
            item_div = self.driver.find_element(*get_renew_item_div_selector(item_id))
            item_div_html = item_div.get_attribute("innerHTML").strip()
            if "Atnaujintas" in item_div_html:
                items_need_renewal[item_id] = False
            elif "Atnaujinti" in item_div_html:
                items_need_renewal[item_id] = True
            else:
                self.logger.error(f"inner = {item_div_html}")
                continue
        return items_need_renewal

    def get_all_items(self) -> list[str]:
        """Get all my items' ad idx"""
        items_container = self.driver.find_element(*self.ITEMS_TABLE)
        item_rows = items_container.find_elements(By.TAG_NAME, "tr")
        item_idx = [
            row.get_attribute("data-id").strip()
            for row in item_rows
            if row.get_attribute("data-id") is not None
        ]
        self.logger.info(f"Found {len(item_idx)} items")
        return item_idx

    def renew_item(self, item_id: str) -> bool:
        """Renew a specific item"""

        renew_item_div = self.driver.find_element(*get_renew_item_div_selector(item_id))
        clicked = self.driver.click(renew_item_div)

        if clicked:
            self.driver.click_delay()
            renew_page_loaded = self._wait_renew_item_loaded(item_id)

            if renew_page_loaded:
                return self._renew_item_from_its_renew_page()

        # Could not go by clicking for some reason, go directly to item renew url
        self.driver.get(self.ITEM_RENEW_URL_FORMATTER.format(item_id))
        renew_page_loaded = self._wait_renew_item_loaded(item_id)

        if renew_page_loaded:
            return self._renew_item_from_its_renew_page()

        self.logger.error(
            f"Could not go to item (id = {item_id}) renew page by direct url, "
            f"cannot renew"
        )
        return False

    def _wait_renew_item_loaded(self, item_id: str) -> bool:
        """Wait until I am at renew item url"""
        try:
            self.driver.wait.until(lambda driver: item_id in driver.current_url.lower())
            return True
        except TimeoutException:
            self.logger.error(f"Item (id = {item_id}) renew page did not load")
            return False

    def _renew_item_from_its_renew_page(self) -> bool:
        """
        This function starts on the item renewal url, so item id does not
        need to be passed.

        Returns True if the item was renewed successfully, False otherwise
        """
        try:
            self.driver.wait.until(
                lambda driver: len(driver.find_elements(*self.RENEW_PAGE_CHOICES)) >= 2
            )
        except TimeoutException:
            self.logger.error("Could not find renew page choices")
            return False

        renew_page_choices = self.driver.find_elements(*self.RENEW_PAGE_CHOICES)

        if len(renew_page_choices) == 2:
            self.driver.click(renew_page_choices[-1])
            self.driver.click_delay()
            free_renew_div = self.driver.find_element(*self.FREE_RENEW_DIV)
            self.driver.click(free_renew_div)
            return True

        return False
