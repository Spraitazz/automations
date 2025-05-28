
from spires.definitions import *
from spires.utils import click_delay, round_to_nearest_5, update_exchange_rate



def bid_jobs(automation: WebAutomation, supported_currencies: list[str]):
    """
    For each job get: student_name, degree, subject, currency
    convert MY_CURRENCY to student currency to correctly bid as in MY_BIDS
    apply with prepared generic bid message
    """
    
    logger = automation.logger
    config = automation.config
    driver = automation.driver

    # allow the site to load possible jobs to bid, if any
    try:
        WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui form"))
        )
        logger.debug("Have new jobs to bid on")
    except:
        # having waited enough, finally check if have "no new jobs" div
        try:
            driver.find_element(
                By.XPATH, './/div[contains(@class, "jobOpportunitiesEmptyBox")]'
            )
            logger.debug("No new jobs")
        except:
            logger.warning(
                'Cannot see any bid forms AND cannot see the message "no new jobs"'
            )
        return

    bid_forms = driver.find_elements(By.CLASS_NAME, "ui form")
    for form in bid_forms:
        subject_div = None
        try:
            subject_div = form.find_element(
                By.XPATH, './/*[contains(@class, "jobSubjectLevel")]'
            )
        except:
            #
            # TO DO: click close job icon on this? Or wait until after a few retries?
            #
            logger.warning(
                'Could not find element with class containing "jobSubjectLevel"'
            )
            continue

        subject_info = subject_div.get_attribute("innerHTML").strip()
        # IB - Maths: Analysis and Approaches - <span style="color: grey;">4 Bids </span>
        degree_level = subject_info[: subject_info.index(" ")]
        remain_info = subject_info[subject_info.index(" ") :].strip()
        # - Maths: Analysis and Approaches -
        subject = remain_info[2 : 2 + remain_info[2:].index("-")].strip()

        if degree_level.lower() not in [
            d.lower() for d in config["MY_DEGREES"]
        ] or subject.lower() not in [s.lower() for s in config["MY_SUBJECTS"]]:
            # delete job and go to next potential customer
            logger.debug(
                f"{subject}, {degree_level} not part of my competences, removing job"
            )
            try:
                icon = form.find_element(By.CSS_SELECTOR, "i.red.remove.icon")
                icon.click()
                click_delay()
            except:
                # could not click red "remove job" icon. Two options:
                # 1. Continue to other jobs, then will try to remove on next refresh
                # 2. Refresh page and go to start of this function
                logger.exception("could not remove job")

            continue

        # subject good, continue
        try:
            # Find <div> with exact text "More info" that is one of the descendents (direct?) of this form
            more_info_div = form.find_element(
                By.XPATH, './/div[normalize-space(text())="More info"]'
            )
            more_info_div.click()
            click_delay()
        except:
            logger.exception('No "More info" div found in this form:')
            continue

        desc_divs = form.find_elements(By.CLASS_NAME, "description")
        if len(desc_divs) < 2:
            logger.warning("desc_divs has length of {}".format(len(desc_divs)))
            # continue

        paragraphs = None
        for info_div in desc_divs:
            info_div = info_div.find_element(By.TAG_NAME, "div")  # mid
            children = info_div.find_elements(By.XPATH, "./*")
            if len(children) == 0:
                continue
            info_div = info_div.find_element(By.TAG_NAME, "div")
            paragraphs = info_div.find_elements(By.TAG_NAME, "p")
            if len(paragraphs) < 4:
                continue
            break

        student_name = ""
        currency = ""
        for p in paragraphs:
            inner = p.get_attribute("innerHTML")
            if "First Name" in inner:
                student_name = (
                    inner.replace("<b>First Name:</b>", "").replace('""', "").strip()
                )
            elif "Currency" in inner:
                currency = (
                    inner.replace("<b>Currency:</b>", "").replace('""', "").strip()
                )

        if currency not in supported_currencies:
            logger.debug("{} is not a supported currency".format(currency))
            continue

        # prep generic msg with student name, enter into text field
        generic_bid_msg = GENERIC_BID_MSG_PLACEHOLDER.format(
            student_name, config["TUTOR_NAME"]
        )
        textarea = form.find_element(By.CSS_SELECTOR, 'textarea[name="jobApplication"]')
        textarea.send_keys(generic_bid_msg)
        click_delay()

        #
        # TO DO: change to try except here and make update_exchange_rate return exceptions
        #
        res = update_exchange_rate(currency, config, logger)
        if res == -1:
            # could not update, must skip?
            logger.warning(
                "couldnt update exchange rate for currency: {}. Must skip this student".format(
                    currency
                )
            )
            continue
        #
        # TO DO: add else to logger.debug if update successfully? Or should do inside update_exchange_rate?
        #

        # convert currency and enter bid (ROUND TO NEAREST 5) e.g. exchange_rates[EUR] = 0.855 (24-04-2025)
        bid_amount = config["MY_BIDS"][degree_level.lower()] / EXCHANGE_RATES[currency]
        bid_amount *= 1.05  # spires uses currency in their favour
        bid_amount = int(round_to_nearest_5(bid_amount))

        first_span = form.find_element(By.CSS_SELECTOR, "span.react-numeric-input")
        input_field = first_span.find_element(By.XPATH, "./input")
        input_field.send_keys(str(bid_amount))
        click_delay()

        # click Submit Bid
        submit_btn = form.find_element(
            By.XPATH,
            './/button[contains(@class, "ui green tiny button") and normalize-space(text())="Submit Bid"]',
        )
        submit_btn.click()
        click_delay()

        logger.debug(
            f"bidded {bid_amount} {currency}/h on job by student: {student_name}, subject: {subject}, level: {degree_level}"
        )
        time.sleep(3.0)
