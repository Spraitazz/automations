

class SkelbiuAutomation:
    """Main automation class for marketplace operations"""
    
    def __init__(self, automation: WebAutomation):
        self.driver = None
        self.automation = AutomationController(
            check_interval_hours=24,  # Check every 24 hours
            renewal_days_threshold=7   # Renew items older than 7 days
        )
        self.login_page = None
        self.items_page = None
        
        """
        # Configuration - Update these with your actual values
        self.config = {
            'login_url': 'https://marketplace.example.com/login',
            'items_url': 'https://marketplace.example.com/my-ads',
            'email': 'your_email@example.com',
            'password': 'your_password',
            'headless': True  # Set to False for debugging
        }
        """
        
    def load_config(self):
        pass
    
    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = Options()
            if self.config['headless']:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Initialize page objects
            self.login_page = LoginPage(self.driver)
            self.items_page = ItemsPage(self.driver)
            
            logger.info("WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def cleanup_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up WebDriver: {e}")
    
    def perform_login(self):
        """Perform login operation"""
        try:
            logger.info("Attempting to login...")
            self.login_page.navigate_to_login(self.config['login_url'])
            
            success = self.login_page.login(
                self.config['email'], 
                self.config['password']
            )
            
            if success:
                logger.info("Login successful")
                return True
            else:
                logger.error("Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Exception during login: {e}")
            return False
    
    def check_and_renew_items(self):
        """Check items and renew if necessary"""
        try:
            logger.info("Navigating to items page...")
            self.items_page.navigate_to_items(self.config['items_url'])
            
            # Get all items details and update cache
            all_items = []
            page_count = 1
            
            while True:
                logger.info(f"Processing page {page_count}")
                items_on_page = self.items_page.get_all_items_details()
                all_items.extend(items_on_page)
                
                if not self.items_page.has_next_page():
                    break
                    
                if not self.items_page.go_to_next_page():
                    break
                    
                page_count += 1
            
            # Update stored items cache
            self.automation.update_stored_items(all_items)
            
            # Renew eligible items
            renewed_count = 0
            for page_num in range(1, page_count + 1):
                if page_num > 1:
                    # Navigate back to specific page if needed
                    self.items_page.navigate_to_items(self.config['items_url'])
                
                page_renewed = self.items_page.renew_all_eligible_items(
                    self.automation.renewal_days_threshold
                )
                renewed_count += page_renewed
            
            logger.info(f"Total items renewed: {renewed_count}")
            return True
            
        except Exception as e:
            logger.error(f"Exception during item renewal: {e}")
            TestHelpers.take_screenshot(self.driver, "renewal_error")
            return False
    
    def run_automation_cycle(self):
        """Run a single automation cycle"""
        try:
            if not self.setup_driver():
                return False
            
            if not self.perform_login():
                logger.error("Could not login, will retry later")
                return False
            
            if not self.check_and_renew_items():
                logger.error("Failed to check/renew items")
                return False
            
            logger.info("Automation cycle completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Exception in automation cycle: {e}")
            return False
        finally:
            self.cleanup_driver()
    
    def run(self):
        """Main automation loop"""
        logger.info("Starting marketplace automation...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        while not self.automation.stop_event.is_set():
            try:
                if check_need_renew(self.automation.stored_items):
                    logger.info("Going to check my ads")
                    
                    success = self.run_automation_cycle()
                    
                    if not success:
                        logger.error("Automation cycle failed, sleeping for 60s before retry")
                        self.automation.sleep(60.0)
                        continue
                    
                    # Sleep for the configured interval
                    sleep_hours = self.automation.check_interval_hours
                    logger.info(f"Sleeping for {sleep_hours} hours until next check")
                    self.automation.sleep(sleep_hours * 3600)  # Convert to seconds
                else:
                    logger.info("No renewal needed, sleeping for 1 hour")
                    self.automation.sleep(3600)  # Sleep for 1 hour
                    
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                self.automation.sleep(60.0)  # Sleep for 1 minute on error
        
        logger.info("Automation stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.automation.stop()
        self.cleanup_driver()
