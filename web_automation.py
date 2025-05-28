from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import random
import re
from xvfbwrapper import Xvfb

from definitions import XVFB_DISPLAY_WIDTH, XVFB_DISPLAY_HEIGHT
from automation import *


DEFAULT_URL = "http://diedai.lt"

# set default browser options
DEFAULT_BROWSER_OPTIONS = webdriver.ChromeOptions()
DEFAULT_BROWSER_OPTIONS.add_argument("--start-maximized")
DEFAULT_BROWSER_OPTIONS.add_argument("--incognito")
DEFAULT_BROWSER_OPTIONS.add_argument("--window-size=1024x768")
## move window off screen
# options.add_argument("--window-position=-32000,-32000")
## for headless browser
# options.add_argument('--headless')
# options.add_argument('--disable-gpu')
# options.add_argument('--no-sandbox')  #needed for headless mode
# options.add_argument('--disable-dev-shm-usage')
## extras to simulate a non-headless environment
# options.add_argument('--remote-debugging-port=9221')
# options.add_argument('--disable-software-rasterizer')

# to pretend im human, for random (uniform) delay (in s) in given range after actions
CLICK_DELAY_MIN = 2.0
CLICK_DELAY_MAX = 4.0

DEFAULT_LOAD_WAIT_TIME_S = 10



#
# TO DO: make func of automation to use interruptable sleep (don't care as short here)
#
def click_delay(min: float = CLICK_DELAY_MIN, max: float = CLICK_DELAY_MAX):
    time.sleep(random.uniform(min, max))


def move_to_and_click(driver: ChromeDriver, elem: WebElement):
    ActionChains(driver).move_to_element(elem).pause(
        random.uniform(0.5, 1.5)
    ).click().pause(
        random.uniform(0.5, 1.5)
    ).perform()


def deepest_div(element: WebElement):
    """recursively go into the first direct descendent div of a given element,
    returning the deepest div"""
    divs = element.find_elements(By.XPATH, "./div")
    if divs:
        return deepest_div(divs[0])
    else:
        return element




class WebAutomation(Automation):
    driver: typing.Optional[ChromeDriver] = None
    own_xvfb_display: typing.Optional[bool] = False
    xvfb_display: typing.Optional[int] = -1

    def __init__(
        self,
        name: str,
        run_func: typing.Callable,
        config_fpath: str,
        own_xvfb_display: bool = False,
        xvfb_display: int = -1,
    ):
        super().__init__(name, run_func, config_fpath)
        self.driver = None
        self.own_xvfb_display = own_xvfb_display
        self.xvfb_display = xvfb_display

    #
    # TO DO: wrap in try/except - check for 
    #       selenium.common.exceptions.NoSuchDriverException: Message: Unable to obtain driver for chrome; 
    #       For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors/driver_location
    #
    def init_webdriver(self, options: webdriver.ChromeOptions() = DEFAULT_BROWSER_OPTIONS) -> ChromeDriver:
        driver = webdriver.Chrome(options=options)
        self.driver = driver
        return driver

    def cleanup(self, logger: logging.Logger):
        try:
            if self.driver is not None:
                self.driver.quit()
            else:
                logger.error("not expecting to be here")
        except:
            logger.exception("")
        finally:
            self.driver = None
            super().cleanup(logger)

    def driver_try_get(self, url: str):

        num_tries_max = 3
        retry_sleep_s = 10.0
        i_try = 0
        while i_try < num_tries_max:
            try:
                self.driver.get(url)
                return
            except:
                self.logger.debug(
                    f"connection error on try {i_try+1}/{num_tries_max}, will retry in {retry_sleep_s} s"
                )
                self.sleep(retry_sleep_s)
                i_try += 1
        exc_fstr = f"driver could not get {url} after {num_tries_max} tries"
        self.logger.error(exc_fstr)
        raise Exception(exc_fstr)

    def driver_try_click(self, elem: WebElement):

        try:
            elem.click()
            return True
        except ElementClickInterceptedException as e:
            # Try to extract the intercepting element
            match = re.search(r"Other element would receive the click: (.+?)\n", str(e))
            if match:
                html_snippet = match.group(1)
                # print("Intercepting element:", html_snippet)

                # Try to build a selector from id > class > tag
                id_match = re.search(r'id="([^"]+)"', html_snippet)
                class_match = re.search(r'class="([^"]+)"', html_snippet)
                tag_match = re.search(r"<(\w+)", html_snippet)

                selector = None
                if id_match:
                    selector = f"#{id_match.group(1)}"
                elif class_match:
                    class_selector = "." + ".".join(class_match.group(1).split())
                    selector = (
                        f"{tag_match.group(1)}{class_selector}"
                        if tag_match
                        else class_selector
                    )
                elif tag_match:
                    selector = tag_match.group(1)

                if selector:
                    # Try to hide {selector}
                    self.driver.execute_script(
                        f"""
                        var el = document.querySelector("{selector}");
                        if (el) {{
                            el.style.display = "none";
                            el.remove();
                        }}
                        """
                    )
                    time.sleep(1.0)
                else:
                    pass
                    # Could not construct a selector from the intercepted element
            else:
                # Could not extract element from exception
                pass

            return False
            
    def get_deepest_first_descendant(self, element: WebElement) -> WebElement:
        """
        Recursively follows the first child of the given WebElement
        until the deepest such descendant is reached.
        """
        try:
            first_child = element.find_element("xpath", "./*")
            return get_deepest_first_descendant(first_child)
        except:
            # No child found, this is the deepest element
            return element

    def email_exception_handling_wrapper(self, logger: logging.Logger):

        try:
            if self.own_xvfb_display:
                with Xvfb(display=self.xvfb_display, width=XVFB_DISPLAY_WIDTH, height=XVFB_DISPLAY_HEIGHT) as xvfb:
                    self._run_and_cleanup(logger)
            else:
                self._run_and_cleanup(logger)
        except:
            self._on_exception(logger)
      
