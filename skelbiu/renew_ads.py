from skelbiu.definitions import *
from skelbiu.utils import click_delay, attempt_click


# this assumes we are already at MY_ADS_URL (redirected by default after logging in)
def renew_ads(driver: ChromeDriver, logger: logging.Logger):

    table = driver.find_element(By.ID, "adsList")
    rows = table.find_elements(By.TAG_NAME, "tr")
    item_idx = [
        row.get_attribute("data-id")
        for row in rows
        if row.get_attribute("data-id") is not None
    ]

    for item_id in item_idx:
        target = driver.find_element(By.ID, "renewID{}".format(item_id))
        inner = target.get_attribute("innerHTML").strip()
        if inner == "Atnaujintas":
            logger.debug(f"item with id {item_id} is already renewed.")
            continue
        elif inner == "Atnaujinti":
            logger.debug(f"will renew item with id {item_id}")
        else:
            logger.error(f"inner = {inner}")
            continue

        clicked = attempt_click(driver, target, logger)
        if not clicked:
            target = driver.find_element(By.ID, "renewID{}".format(item_id))
            # print(f're-attempting click on target: {target}')
            target.click()
        click_delay()

        try:
            WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "slot")) >= 2
            )
        except TimeoutException:
            logger.warning('couldnt find by class_name "slot"')
            continue

        targets = driver.find_elements(By.CLASS_NAME, "slot")
        if len(targets) != 2:
            logger.warning(f"len(targets) = {len(targets)}")
            item_href = f"{BASE_URL}/ad/renew/{str(item_id).strip()}"
            driver.get(item_href)
            #
            # TO DO: wait until slots loaded instead of click delay
            #
            click_delay()

        else:
            targets[-1].click()
            click_delay()

        # click "uzsakyti nemokamai" (click target id=full-price)
        target = driver.find_element(By.ID, "full-price")
        target.click()
        logger.debug(f"item with id {item_id} renewed")
        click_delay()
