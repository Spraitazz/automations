from linkedin.definitions import *
from linkedin.prompts import *


def send_unhandled_exception_email(bot_name: str):

    from_email = APP_EMAIL
    to_email = UNHANDLED_EXCEPTION_EMAIL

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = f"{bot_name} unhandled exception"

    body = "look at logs"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(APP_EMAIL, GMAIL_APP_PASS)
        server.sendmail(from_email, to_email, msg.as_string())


def click_delay(min=2.0, max=4.0):
    time.sleep(random.uniform(min, max))


def launch_browser() -> webdriver:
    driver = webdriver.Chrome(options=DEFAULT_BROWSER_OPTIONS)
    return driver


def login(driver: webdriver):
    driver.get(LOGIN_URL)
    click_delay()

    # get "Remember me" checkbox, CHECKED BY DEFAULT
    # <input name="rememberMeOptIn" id="rememberMeOptIn-checkbox" class="large-input" checked="" value="true" type="checkbox">
    # if value="true" - click to uncheck, wait a sec, check that value="false", if true: proceed

    username_inp = driver.find_element(By.ID, "username")
    username_inp.clear()
    username_inp.send_keys(EMAIL)
    click_delay()

    pass_inp = driver.find_element(By.ID, "password")
    pass_inp.clear()
    pass_inp.send_keys(PASS)
    click_delay()

    submit_btn = driver.find_element(By.CSS_SELECTOR, ".btn__primary--large")
    submit_btn.click()


def remove_non_bmp(text: str) -> str:
    return "".join(c for c in text if ord(c) <= 0xFFFF)


#
# TO DO: in case I go to different pages on linkedn, here I should:
# 1. Go to feed url
# 2. wait (max 10s?) for activity divs to be visible
#
#
# IMPORTANT: num_responded only counts in between sleep periods, while responded_posts ensures we dont respond to duplicates
#
def respond_comments(
    driver: webdriver, num_responded: int = 0, responded_posts: list[str] = []
):

    logger = logging.getLogger("logger")

    for _ in range(random.choice([3, 5, 10])):
        scroll_y = random.randint(50, 300)
        driver.execute_script(f"window.scrollBy(0, {scroll_y});")
        time.sleep(random.uniform(0.25, 3.0))

    this_elem = None
    try:
        this_elem = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@data-id, 'urn:li:activity')]")
            )
        )

    except:
        logger.warning(
            f"activity divs on feed page did not load in {DEFAULT_LOAD_WAIT_TIME_S} seconds"
        )
        return

    try:
        driver.execute_script(
            """
            try {
                window.focus();
                if (arguments[0] && typeof arguments[0].focus === 'function') {
                    arguments[0].focus();
                }
            } catch (e) {
                console.warn('Focus failed:', e);
            }
        """,
            this_elem,
        )

    except:
        logger.exception("")

    activity_divs = driver.find_elements(
        By.XPATH, "//div[contains(@data-id, 'urn:li:activity')]"
    )


    logger.debug(f"{len(activity_divs)} posts visible")

    responded_count = num_responded
    
    #
    # respond only to "suggested" spam
    #
    activity_divs_suggested = []
    for activity_div in activity_divs:
        try:
            suggested_span = activity_div.find_element(By.XPATH,
                              './/span[contains(@class, "update-components-header__text-view")]')
            if 'Suggested' in suggested_span.text.strip():
                activity_divs_suggested.append(activity_div)
        except:
            continue
    
    if len(activity_divs_suggested) == 0:
        logger.warning("could not find any 'Suggested' divs")
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )
        
    logger.debug(f"{len(activity_divs_suggested)} 'Suggested' posts visible")
    
    activity_div = random.choice(activity_divs_suggested)

    comment_btn = []
    try:
        comment_spans = activity_div.find_elements(
            By.XPATH,
            ".//span[contains(@class, 'artdeco-button') and normalize-space(text())='Comment']",
        )

        comment_btn = activity_div.find_elements(
            By.XPATH, ".//button[@aria-label='Comment']"
        )
    except:
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )

    if len(comment_btn) != 1:
        logger.warning(f"comment btn has len: {len(comment_btn)}")
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )

    ActionChains(driver).move_to_element(activity_div).perform()
    # ALTERNATIVE:
    # var element = Driver.FindElement(By.Id("element-id"));
    # ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", element);

    # can comment: get text, feed to llm, get comment
    # text is inside div with class containing "feed-shared-inline-show-more-text"
    text_div = activity_div.find_element(
        By.XPATH, ".//div[contains(@class, 'feed-shared-inline-show-more-text')]"
    )
    # text is inside span which has dir="ltr" attribute
    text_span = text_div.find_element(By.XPATH, ".//span[@dir='ltr']")

    post_text = text_span.text.strip()
    # logger.debug(f'POST:\n{post_text}')

    post_text_cleaned = remove_non_bmp(post_text)
    logger.debug(f"POST (CLEANED):\n{post_text_cleaned}")

    if post_text_cleaned in responded_posts:
        logger.debug("Already responded")
        # continue
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )

    logger.debug("Will respond to post")

    #
    # TO DO: wait until loaded
    #
    try:
        # comment_btn[0].click()
        ActionChains(driver).move_to_element(comment_btn[0]).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        click_delay()
    except:
        logger.exception("")
        # continue
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )

    try:
        comment_div = activity_div.find_element(
            By.XPATH,
            ".//div[contains(@class, 'ql-editor ql-blank') and @data-placeholder='Add a comment…']",
        )
        first_p = comment_div.find_element(By.XPATH, "./p[1]")

        # appendage = 'Your RESPONSE must be in the same language as the POST. '
        # prompt = appendage + random.choice(PROMPTS_FMT).format(post_text)
        prompt = random.choice(PROMPTS_FMT).format(post_text)

        logger.debug(f"will submit llm request with prompt:\n{prompt}")
        response_status, response_text, num_tries = llm_request(
            prompt, LLM_PARAMS, logger
        )
        if response_status != 0:
            logger.warning(f"resp status: {response_status}")
            # continue
            return respond_comments(
                driver, num_responded=responded_count, responded_posts=responded_posts
            )

        cleaned_response_text = remove_non_bmp(response_text)
        cleaned_response_text = cleaned_response_text.replace("\n", " ")

        first_p.send_keys(cleaned_response_text)
        click_delay()

        submit_comment_btn = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    ".//button[contains(@class, 'comments-comment-box__submit-button')]",
                )
            )
        )
        logger.debug(f"Commenting response:\n{cleaned_response_text}")

        # submit_comment_btn.click()
        ActionChains(driver).move_to_element(submit_comment_btn).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        responded_count += 1
        responded_posts.append(post_text_cleaned)
        click_delay()

    except NoSuchElementException:
        logger.warning("add comment element not found")
        # continue
    except:
        logger.exception("")
        # continue

        # if responded_count == NUM_COMMENTS_ONE_GO:
        # break

    if responded_count < NUM_COMMENTS_ONE_GO:
        logger.debug("Have to refresh")
        click_delay()
        driver.refresh()
        time.sleep(DEFAULT_LOAD_WAIT_TIME_S)
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )
    else:
        logger.debug(f"Done responding with {responded_count} comments")

    return responded_posts
