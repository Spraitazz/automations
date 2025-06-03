#
#
# TODO: common things for web automations -> better place in WebAutomations?
#
#

import os
from pathlib import Path
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#import logging

from skelbiu.definitions import THIS_DIR_PATH

#logger = logging.getLogger(__name__)

class TestHelpers:
    """Utility class for common test operations"""
    
    @staticmethod
    def take_screenshot(driver, test_name):
        """Take screenshot for debugging failed tests"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{test_name}_{timestamp}.png"
        
        screenshots_dir_path = THIS_DIR_PATH / "screenshots"
        # Create screenshots directory if it doesn't exist
        os.makedirs(screenshots_dir_path, exist_ok=True)
        
        filepath = screenshots_dir_path / filename
        driver.save_screenshot(filepath)
        return filepath
    
    @staticmethod
    def wait_for_page_load(driver, timeout=10):
        """Wait for page to fully load"""
        wait = WebDriverWait(driver, timeout)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    
    @staticmethod
    def scroll_to_element(driver, element):
        """Scroll element into view"""
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
