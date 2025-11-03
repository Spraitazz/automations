import logging
import random
import re
from collections.abc import Callable

from selenium import webdriver
from selenium.common import ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

from config.extended_chrome_driver import DEFAULT_BROWSER_OPTIONS


class ExtendedChromeDriver(webdriver.Chrome):
    """
    Extended Chrome driver implementation - tries harder to get() and
    click() as well as contains some convenience functions such as
    move_to_and_click_element()

    The extended chrome driver always belongs to some SeleniumAutomation,
    whose instance is passed in to __init__()
    """

    DEFAULT_LOAD_WAIT_TIME_S = 10

    CLICK_DELAY_MIN = 2.0
    CLICK_DELAY_MAX = 4.0

    def __init__(
        self,
        sleep: Callable,
        logger: logging.Logger,
        options: webdriver.ChromeOptions = DEFAULT_BROWSER_OPTIONS,
    ):
        super().__init__(options=options)

        self.sleep = sleep
        self.logger = logger

        self.wait = WebDriverWait(super(), self.DEFAULT_LOAD_WAIT_TIME_S)

    def get(self, url: str):

        if url == self.current_url:
            return

        num_tries_max = 3
        retry_sleep_s = 10.0

        for i_try in range(num_tries_max):
            try:
                super().get(url)
                return
            except Exception:
                self.logger.debug(f"connection error on try {i_try + 1}...")
                self.sleep(retry_sleep_s)

        exc_fstr = f"driver could not get {url} after {num_tries_max} tries"
        self.logger.error(exc_fstr)
        raise Exception(exc_fstr)

    # TODO: on some sites might have multiple offenders - try up to Nmax times
    def click(self, elem: WebElement, second_try=False):
        """
        Make two attempts to click, in the first instance removing any
        offending elements in the way, and then re-trying.
        """

        try:
            elem.click()
            return True
        except ElementClickInterceptedException as e:
            # Extract the intercepting element
            match = re.search(r"Other element would receive the click: (.+?)\n", str(e))

            if match:
                html_snippet = match.group(1)
                # Build a selector from id > class > tag
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
                    self.execute_script(
                        f"""
                        var el = document.querySelector("{selector}");
                        if (el) {{
                            el.style.display = "none";
                            el.remove();
                        }}
                        """
                    )
                    self.sleep(1.0)

                    # one more try
                    if not second_try:
                        return self.click(elem, second_try=True)
                else:
                    # Could not construct a selector from the intercepted
                    # element
                    pass
            else:
                # Could not extract element from exception
                pass

            return False

    def click_delay(self, _min: float = CLICK_DELAY_MIN, _max: float = CLICK_DELAY_MAX):
        self.sleep(random.uniform(_min, _max))

    def move_to_element(self, elem: WebElement):
        ActionChains(self).move_to_element(elem).perform()

    def move_to_and_click_element(self, elem: WebElement):
        self.move_to_element(elem)
        self.click(elem)
        self.click_delay()

    def random_scroll(self, scroll_up: bool = False):
        """
        Scroll up or down a random amount, function can run anywhere from 3s
        to 60s.
        """

        for _ in range(random.choice([1, 3, 5])):
            scroll_y = random.randint(50, 300)
            if scroll_up:
                scroll_y *= -1
            self.execute_script(f"window.scrollBy(0, {scroll_y});")
            self.sleep(random.uniform(1.0, 4.0))

    def get_deepest_first_descendant(self, element: WebElement) -> WebElement:
        """
        Recursively follows the first child of the given WebElement
        until the deepest such descendant is reached.
        """
        try:
            first_child = element.find_element("xpath", "./*")
            return self.get_deepest_first_descendant(first_child)
        except Exception:
            # No child found, this is the deepest element
            return element

    def get_deepest_div(self, element: WebElement) -> WebElement:
        """
        Recursively go into the first direct descendent div of a given element,
        returning the deepest div.
        """
        divs = element.find_elements(By.XPATH, "./div")
        if divs:
            return self.get_deepest_div(divs[0])
        else:
            return element
