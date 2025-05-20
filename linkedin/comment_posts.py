
from linkedin.definitions import *
from linkedin.utils import click_delay, random_scroll, wait_feed_loaded, remove_non_bmp
from linkedin.prompts import *




def filter_activity_suggested(activity_divs: list[WebElement]):
"""Filter out only feed activity divs for activity which is "Suggested" for you"""

    activity_divs_suggested = []
    
    for activity_div in activity_divs:
        try:
            suggested_span = activity_div.find_element(By.XPATH,
                              './/span[contains(@class, "update-components-header__text-view")]')
            if 'Suggested' in suggested_span.text.strip():
                activity_divs_suggested.append(activity_div)
        except:
            continue
            
    return activity_divs_suggested
    
    
def try_focus(driver, logger, this_elem):    
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
    
    
    
def get_post_text(activity_div: WebElement):
"""Returns the post text, without non-bmp characters, given the activity div"""

    text_div = activity_div.find_element(
        By.XPATH, ".//div[contains(@class, 'feed-shared-inline-show-more-text')]"
    )
    text_span = text_div.find_element(By.XPATH, ".//span[@dir='ltr']")
    post_text = text_span.text.strip()
    post_text_cleaned = remove_non_bmp(post_text)
    return post_text_cleaned

#
# TO DO: in case I go to different pages on linkedn, here I should:
# 1. Go to feed url
# 2. wait (max 10s?) for activity divs to be visible
#
#
# IMPORTANT: num_responded only counts in between sleep periods, while responded_posts ensures we dont respond to duplicates
#
def respond_comments(
    driver: ChromeDriver, num_responded: int = 0, responded_posts: list[str] = []
):

    responded_count = num_responded

    logger = logging.getLogger("logger")   
    
    #this_elem = None
    try:
        wait_feed_loaded(driver)  
    except:
        logger.warning(
            f"activity divs on feed page did not load in {DEFAULT_LOAD_WAIT_TIME_S} seconds"
        )
        return responded_posts

    random_scroll(driver)    
    
    activity_divs = driver.find_elements(
        By.XPATH, "//div[contains(@data-id, 'urn:li:activity')]"
    )


    logger.debug(f"{len(activity_divs)} posts visible")

        
    # respond only to "suggested" spam    
    activity_divs_suggested = filter_activity_suggested(activity_divs)
    
    if len(activity_divs_suggested) == 0:
        logger.warning("could not find any 'Suggested' divs")
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )
        
    logger.debug(f"{len(activity_divs_suggested)} 'Suggested' posts visible")
    #
    # pick at random a post to comment on
    #
    activity_div = random.choice(activity_divs_suggested)

    #
    # try find "Comment" button
    #
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

    # move to element - looks more realistic    
    ActionChains(driver).move_to_element(activity_div).perform()
    # ALTERNATIVE:
    # var element = Driver.FindElement(By.Id("element-id"));
    # ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", element);




    # can comment: get text, feed to llm, get comment
    post_text_cleaned = ""
    try:
        post_text_cleaned = get_post_text(activity_div)
    except:
        logger.exception("Could not get cleaned post text")
        return respond_comments(
            driver, num_responded=responded_count, responded_posts=responded_posts
        )
    
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
