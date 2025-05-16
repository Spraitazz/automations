from spires.definitions import *


def round_to_nearest_5(x: float):
    return round(x / 5.0) * 5.0


def click_delay(min: float = CLICK_DELAY_MIN, max: float = CLICK_DELAY_MAX):
    time.sleep(random.uniform(min, max))


def click(driver: ChromeDriver, elem: WebElement):
    ActionChains(driver).move_to_element(elem).pause(
        random.uniform(0.5, 1.5)
    ).click().perform()
    click_delay()


def get_supported_currencies(logger: logging.Logger):

    supported_currencies = []

    response = requests.get(SUPPORTED_CURRENCIES_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article")
    first_div = None
    for child in article.children:
        if child.name == "div":
            first_div = child
            break
    table_count = 0
    third_table = None
    for child in first_div.children:
        if child.name == "table":
            table_count += 1
            if table_count == 3:
                third_table = child
                break

    for row in third_table.find_all("tr")[1:]:
        first_td = row.find("td")
        if first_td:
            currency = first_td.get_text(strip=True)
            supported_currencies.append(currency)
    return supported_currencies


#
# TO DO: not return numbers, but throw exceptions and log them?
#
def update_exchange_rate(currency: str, config: dict, logger: logging.Logger):

    # check if need to update this currency exchange rates, update
    needs_update = False
    if currency not in CURRENCY_UPDATED_LAST:
        needs_update = True
    elif (datetime.now() - CURRENCY_UPDATED_LAST[currency]).days > 0:
        needs_update = True

    if not needs_update:
        return 0

    url = EXCHANGE_RATE_API_URL_PLACEHOLDER.format(config["CURRENCY_API_KEY"], currency)
    data = None
    try:
        response = requests.get(url)
        data = response.json()
    except:
        logger.exception("")

    if data is None:
        return -1

    if data["result"] != "success":
        return -1

    CURRENCY_UPDATED_LAST.update({currency: datetime.now()})
    EXCHANGE_RATES.update({currency: data["conversion_rates"][config["MY_CURRENCY"]]})
    return 0


# recursively go into the first direct descendent div of a given element
def deepest_div(element: WebElement):
    divs = element.find_elements(By.XPATH, "./div")
    if divs:
        return deepest_div(divs[0])
    else:
        return element


#
# TO DO: should wait for some element to appear after every url load, button click?
#
def login(driver: ChromeDriver, config: dict, logger: logging.Logger):
    logger.debug("logging in")
    driver.get(LOGIN_URL)
    click_delay()

    xpath = '//button[p[normalize-space(text())="Login with Email"]]'
    button = driver.find_element(By.XPATH, xpath)
    button.click()
    click_delay()

    username_inp = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    username_inp.clear()
    username_inp.send_keys(config["EMAIL"])
    click_delay()

    pass_inp = driver.find_element(By.NAME, "password")
    pass_inp.clear()
    pass_inp.send_keys(config["PASS"])
    click_delay()

    submit_btn = driver.find_element(
        By.XPATH, '//*[contains(@class, "login_signupNavButton")]'
    )
    submit_btn.click()
    click_delay()
    logger.debug("clicked login")
