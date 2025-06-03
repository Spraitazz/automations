
from skelbiu.definitions import *
from skelbiu.login_page import LoginPage 
from skelbiu.items_page import ItemsPage
from skelbiu.test_helpers import TestHelpers

class SkelbiuAutomation(WebAutomation):
    """Main automation class for skelbiu operations"""
    
    AUTOMATION_NAME = "skelbiu"
    
    def __init__(self, config_fpath: Path, own_xvfb_display: bool, xvfb_display: int):
    
        super().__init__(
            name = self.AUTOMATION_NAME,
            config_fpath=config_fpath,
            own_xvfb_display=own_xvfb_display,
            xvfb_display=xvfb_display
        )   
        
        try:
            self.load_config() 
        except:
            self.logger.exception("config not ok")
            return        

    
    def load_config(self):                     
        config = {}
        configfile = configparser.ConfigParser(interpolation=None)
        configfile.read(self.config_fpath)
        config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
        config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
        config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
        config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
        self.config = config
        
        
    #
    # TODO: ideally return ItemStore, as values are not just str, but datetime in iso format
    #
    def load_item_store(self):
        """
        Load my item store, items for which I have a record already when each item
        was last renewed, from MY_ITEMS_STORE_FPATH, currently a json formatted dict
        defined in skelbiu.definitions
        """

        stored_items = {}
        with open(MY_ITEMS_STORE_FPATH, "r", encoding="utf-8") as f:
            try:
                stored_items = json.load(f)
            except:
                # no items stored yet
                pass
        self.stored_items = stored_items
        
        
    def check_need_renew(self) -> bool:
        """
        Check if I need to go on site, I go if either:

        1. Any of my items have a last updated date > 25h ago
        2. Any of my items have an unknown last updated date
        """
        check_renew = False
        if len(self.stored_items) == 0:
            check_renew = True
        else:
            now = datetime.now()
            for item_id_str, last_updated_str in self.stored_items.items():
                if len(last_updated_str) < 2:
                    check_renew = True
                    break
                datetime_last_updated = datetime.fromisoformat(last_updated_str)
                if (now - datetime_last_updated).total_seconds() > 90000.0:
                    check_renew = True
                    break
        return check_renew
        
    #
    # TODO: better name for result from self.items_page.check_and_renew()
    #
    def update_item_store(self, result: dict):
        """
        Update my items based on return result of calling renew_ads(), passed as
        result arg, as well as my stored_items loaded in run.py
        """

        stored_items_cur = {}
        for item_id, status_dict in result.items():
            if status_dict["status"] == "renewed":
                stored_items_cur[item_id] = status_dict["last_renewed"]
                self.logger.debug(
                    f"updating item {item_id} renewed last: {status_dict['last_renewed']}"
                )
            else:
                # was already renewed
                if item_id in self.stored_items:
                    stored_items_cur[item_id] = self.stored_items[item_id]
                else:
                    stored_items_cur[item_id] = "-"

        self.logger.debug(
            f"will write stored_items_cur: {stored_items_cur} to {MY_ITEMS_STORE_FPATH}"
        )
        with open(MY_ITEMS_STORE_FPATH, "w", encoding="utf-8") as f:
            json.dump(stored_items_cur, f)
            
        #
        # TODO: dont need to load again really, can be done better
        #
        self.load_item_store()  
        

    def check_logged_in(self):
        self.driver_try_get(MY_ADS_URL)
        try:
            self.wait.until(lambda driver: "signin" not in driver.current_url.lower())
            self.logger.debug("already logged in")
            return True
        except TimeoutException:
            return False
    
    
    def perform_login(self):
        try:
            self.logger.info("Attempting to login...")
            self.login_page.navigate_to_login()
            
            success = self.login_page.login(
                self.config['EMAIL'], 
                self.config['PASS']
            )
            
            if success:
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during login: {e}")
            return False
   
    
    def check_and_renew_items(self):
        """Check items and renew if necessary"""
        try:
            self.logger.info("Navigating to items page...")
            self.items_page.navigate_to_items()         
            renew_result = self.items_page.check_and_renew()
            self.update_item_store(renew_result)          
            return True            
        except Exception as e:
            self.logger.error(f"Exception during item renewal: {e}")
            TestHelpers.take_screenshot(self.driver, "renewal_error")
            return False
    
    
    def run_automation_cycle(self):
        """Run a single automation cycle"""
        self.logger.info("Starting automation cycle") 
        try:                    
            if not self.check_logged_in():              
                if not self.perform_login():
                    self.logger.error("Could not login, will retry later")
                    return False
            else:
                self.logger.debug("Already logged in")
            
            if not self.check_and_renew_items():
                self.logger.error("Failed to check/renew items")
                return False
            
            self.logger.info("Automation cycle completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Exception in automation cycle: {e}")
            return False
           
    
    def run(self):
        """
        Main automation loop:
        
        1. check need renew
        

        only go on site if:

        (A): I have no items in my item store
        (B): one of my items has not been renewed in more than 25h
        (C): one of my items has an unknown last renewed datetime ("-")

        item store is json file at [MY_ITEMS_STORE_FPATH in definitions.py]
        
        
        """        
        self.logger.info("Starting automation...")     
        self.init_webdriver()
        self.wait = WebDriverWait(self.driver, DEFAULT_LOAD_WAIT_TIME_S) 
        self.load_item_store()        
        self.login_page = LoginPage(self)
        self.items_page = ItemsPage(self)                 
        while not self.stop_event.is_set():
            if self.check_need_renew():
                self.logger.info("Going to check my ads")                
                success = self.run_automation_cycle()                
                if not success:
                    self.logger.error("Automation cycle failed, sleeping for 60s before retry")
                    self.sleep(60.0)
                    continue
            else:
                self.logger.info("will not check my ads this time")
                
            sleep_s = random.uniform(
                self.config["MIN_SLEEP_S"], self.config["MAX_SLEEP_S"]
            )
            self.logger.info("going home to sleep for {:.1f} s".format(sleep_s))
            self.driver_try_get(DEFAULT_URL)
            self.sleep(sleep_s)       
        self.logger.info("Automation stopped")
    
 
