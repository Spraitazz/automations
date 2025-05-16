from skelbiu.definitions import *


def click_delay(min: float = CLICK_DELAY_MIN, max: float = CLICK_DELAY_MAX):
    time.sleep(random.uniform(min, max))


def attempt_click(driver: ChromeDriver, elem: WebElement, logger: logging.Logger):
    try:
        elem.click()
        return True

    except ElementClickInterceptedException as e:
        # print("Click intercepted:", e)
        pass

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
                # print(f"Trying to hide: {selector}")
                driver.execute_script(
                    f"""
                    var el = document.querySelector("{selector}");
                    if (el) {{
                        el.style.display = "none";
                        el.remove();
                    }}
                """
                )
                time.sleep(0.5)
            else:
                pass
                # print("Could not construct a selector from the intercepted element.")
        else:
            # print("Could not extract element from exception.")
            pass

        return False


def login(
    automation: WebAutomation,
):  # driver: ChromeDriver, config: dict, logger: logging.Logger):

    # logger = logging.getLogger(f"{AUTOMATION_NAME}_logger")
    logger = automation.logger
    driver = automation.driver
    config = automation.config

    logger.debug("logging in")
    driver.get(LOGIN_URL)
    click_delay()

    # check if logged in already, then bypass
    if "signin" not in driver.current_url:
        # driver.current_url == MY_ADS_URL
        logger.debug("already logged in")
        return

    # reject cookies first
    target = driver.find_element(By.ID, "onetrust-reject-all-handler")
    target.click()
    click_delay()

    username_inp = driver.find_element(By.ID, "nick-input")
    username_inp.clear()
    username_inp.send_keys(config["EMAIL"])
    click_delay()

    pass_inp = driver.find_element(By.ID, "password-input")
    pass_inp.clear()
    pass_inp.send_keys(config["PASS"])
    click_delay()

    submit_btn = driver.find_element(By.ID, "submit-button")
    submit_btn.click()
    logger.debug("clicked login")
    click_delay()
