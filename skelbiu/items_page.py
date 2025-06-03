
from skelbiu.definitions import *

#
# TODO: make it work also if only webdriver is passed, instead of WebAutomation
#       in that case I am using driver.get and elem.click instead of try_get and
#       try_click
#
class ItemsPage:
    """Page Object for Item listing functionality"""
    
    def __init__(self, automation: WebAutomation):
        self.automation = automation
        self.logger = automation.logger
        self.driver = automation.driver
        self.wait = WebDriverWait(self.driver, DEFAULT_LOAD_WAIT_TIME_S)
        
    # Locators (MY_ADS_URL)    
    ITEMS_TABLE = (By.ID, "adsList")  # Container for all items
    RENEW_ITEM_DIV = lambda self, item_id: (By.ID, f"renewID{item_id}")
    
    # Locators (renew page, {BASE_URL}/ad/renew/{item_id}), after clicking "atnaujinti"
    RENEW_PAGE_CHOICES = (By.CLASS_NAME, "slot")       
    FREE_RENEW_DIV = (By.ID, "full-price") # "uzsakyti nemokamai" -> click
    
    # Fallback url if cannot click "Atnaujinti" on ads page for some reason
    ITEM_RENEW_URL_FORMATTER = BASE_URL + "/ad/renew/{}"
    


    def navigate_to_items(self):
        """Navigate to items/ads page"""
        self.automation.driver_try_get(MY_ADS_URL)
        self.wait_for_items_to_load()
        return self
    
    
    def wait_for_items_to_load(self):
        """Wait for items container to be present"""
        try:
            self.wait.until(EC.presence_of_element_located(self.ITEMS_TABLE))
            return True
        except TimeoutException:
            self.logger.warning("Items container not found, page might not have loaded properly")
            return False
    
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

    
    def get_items_states(self) -> dict[str, bool]:
        """
        Return, for each item in my ads, whether the item needs renewal
        as a dict with (key, value) = (item_id, needs_renewal_bool)
        """
        items_need_renewal = {}
        items_idx = self.get_all_items()        
        for item_id in items_idx:                
            item_div = self.driver.find_element(*self.RENEW_ITEM_DIV(item_id))
            item_div_html = item_div.get_attribute("innerHTML").strip()
            if "Atnaujintas" in item_div_html:
                items_need_renewal[item_id] = False
            elif "Atnaujinti" in item_div_html:
                items_need_renewal[item_id] = True
            else:
                self.logger.error(f"inner = {item_div_html}")
                continue
        return items_need_renewal
    
    
    #
    # TODO: check to ensure that after calling this, I am back at MY_ADS_URL
    #
    def _renew_item(self):
        """this function starts on the item renewal url"""
        #
        # TODO: must have exactly =2 below?
        #
        try:
            self.wait.until(
                lambda driver: len(driver.find_elements(*self.RENEW_PAGE_CHOICES)) >= 2
            )
        except TimeoutException:
            self.logger.error("couldnt find renew page choices")
            return False

        renew_page_choices = self.driver.find_elements(*self.RENEW_PAGE_CHOICES)        
        if len(renew_page_choices) == 2:        
            self.automation.driver_try_click(renew_page_choices[-1])
            click_delay()            
            free_renew_div = self.driver.find_element(*self.FREE_RENEW_DIV)
            self.automation.driver_try_click(free_renew_div)
            return True            
            
        return False

    #
    # TODO: needs refactoring
    #
    def renew_item(self, item_id: str):
        """Renew a specific item"""
        
        renew_item_div = self.driver.find_element(*self.RENEW_ITEM_DIV(item_id))        
        clicked = self.automation.driver_try_click(renew_item_div)
        if clicked:
            click_delay()            
            try:
                self.wait.until(lambda driver: item_id in driver.current_url.lower())
                return self._renew_item()
            except TimeoutException:            
                self.logger.warning(f"could not go to item (id = {item_id}) renew page by click, trying direct url")
        
        # could not go by clicking for some reason, then just go directly to item renew url
        self.automation.driver_try_get(self.ITEM_RENEW_URL_FORMATTER.format(item_id))
        try:
            self.wait.until(lambda driver: item_id in driver.current_url.lower())
            return self._renew_item()
        except TimeoutException:
            # could not go by clicking for some reason, then just go directly to item renew url
            self.logger.error(f"could not go to item (id = {item_id}) renew page by direct url, cannot renew")
          
            
        return False
        
        
    def check_and_renew(self) -> dict[str, dict]:
        """
        Check if any of my ads need renewing, and renew them.

        Returns dict with items like {item id: status_dict}, where
        status_dict is either:

        1. {"status": "renewed", "last_renewed": datetime_renewed}
        2. {"status": "already_renewed"}
        """
        result = {}
        
        items_need_renewal = self.get_items_states()
        
        for item_id, needs_renewal in items_need_renewal.items():
            if not needs_renewal:
                self.logger.debug(f"item with id {item_id} is already renewed.")
                result[item_id] = {
                    "status": "already_renewed"
                }
                continue

            if self.renew_item(item_id):
                self.logger.info(f"Successfully renewed item: {item_id}")
                result[item_id] = {
                    "status": "renewed",
                    "last_renewed": datetime.now().isoformat(),
                }
            else:
                self.logger.error(f"Failed to renew item: {item_id}")

        return result 
        
        
        
        

