
from spires.definitions import *


def load_config(automation: WebAutomation):
    config = {}        
    configfile = configparser.ConfigParser(interpolation=None)
    configfile.read(automation.config_fpath)    
    config["TUTOR_NAME"] = configfile["DEFAULT"]["TUTOR_NAME"].strip().strip('"')
    config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
    config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
    config["CURRENCY_API_KEY"] = (
        configfile["DEFAULT"]["CURRENCY_API_KEY"].strip().strip('"')
    )
    config["MY_CURRENCY"] = configfile["DEFAULT"]["MY_CURRENCY"].strip().strip('"')
    config["MY_DEGREES"] = json.loads(configfile["DEFAULT"]["MY_DEGREES"])
    config["MY_SUBJECTS"] = json.loads(configfile["DEFAULT"]["MY_SUBJECTS"])
    config["MY_BIDS"] = json.loads(configfile["DEFAULT"]["MY_BIDS"])
    config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
    config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
    config["RESPOND_MESSAGES"] = configfile.getboolean(
        "DEFAULT", "RESPOND_MESSAGES", fallback=False
    )    
    automation.set_config(config)
    


def round_to_nearest_5(x: float):
    return round(x / 5.0) * 5.0



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



#
# TO DO: should wait for some element to appear after every url load, button click?
#
def login(automation: WebAutomation):

    driver = automation.driver
    config = automation.config
    logger = automation.logger

    logger.debug("logging in")
    automation.driver_try_get(LOGIN_URL)
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
    logger.debug("clicked login")
    click_delay()
    
    
    
    
    
