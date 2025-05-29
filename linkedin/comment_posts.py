#
#
# TO DO: repackage everything useful (common utils like smooth_click etc.)
#        under SeleniumAutomation class, passing it around instead of the logger
#        explicitly
#
#
from linkedin.definitions import *
from linkedin.utils import click_delay, go_to_feed, remove_non_bmp
from linkedin.llm import generate_comment

'''  
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
'''  

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


#
# TO DO: also add "Promoted" spam
# 
#
# TO DO: improve func def to allow return None
#
def pick_random_activity_div(automation: WebAutomation, commented_posts: list[str]) -> WebElement:
    """Pick a random activity div on the feed, where one activity div corresponds to
    one post, and return it. Preferentially picking "Suggested" spam posts to comment
    on."""
    
    logger = automation.logger
    driver = automation.driver
    
    activity_divs = driver.find_elements(
        By.XPATH, "//div[contains(@data-id, 'urn:li:activity')]"
    )

    logger.debug(f"{len(activity_divs)} posts visible")   
    
    if len(activity_divs) == 0:
        return None   
      
    # prioritise responding to "suggested" spam    
    activity_divs_suggested = filter_activity_suggested(activity_divs)    
    activity_divs_available = []
    if len(activity_divs_suggested) == 0:
        logger.warning("could not find any 'Suggested' divs")
    else:
        logger.debug(f"{len(activity_divs_suggested)} 'Suggested' posts visible") 
        for activity_div in activity_divs_suggested:        
            post_text_cleaned = ""
            try:
                post_text_cleaned = get_post_text(activity_div)
            except:
                logger.exception("Could not get cleaned post text")
                continue
            
            if post_text_cleaned not in commented_posts:
                activity_divs_available.append(activity_div)
                
    if len(activity_divs_available) > 0:  
        return random.choice(activity_divs_available)
        
    # no 'suggested' spam, so pick from remainder
    logger.debug("no suggested spam to comment on, picking from the rest")
    
    for activity_div in activity_divs:        
        post_text_cleaned = ""
        try:
            post_text_cleaned = get_post_text(activity_div)
        except:
            logger.exception("Could not get cleaned post text")
            continue
        
        if post_text_cleaned not in commented_posts:
            activity_divs_available.append(activity_div)
       
    if len(activity_divs_available) > 0:  
        return random.choice(activity_divs_available)
        
    return None
    
    
def get_post_text(activity_div: WebElement) -> str:
    """Returns the post text, without non-bmp characters, given the activity div"""

    text_div = activity_div.find_element(
        By.XPATH, ".//div[contains(@class, 'feed-shared-inline-show-more-text')]"
    )
    text_span = text_div.find_element(By.XPATH, ".//span[@dir='ltr']")
    post_text = text_span.text.strip()
    post_text_cleaned = remove_non_bmp(post_text)
    return post_text_cleaned
    
#
# To DO: provide prompt with more details:
#    
## who posted (person/org?)
# first select span by CONTAINS class="update-components-actor__title"
# then go into FIRST children spans recursively until end, get text
#    
## their org (if person)
# first select span by CONTAINS class "update-components-actor__description"
# go into FIRST children spans recursive until end, get text
#
def comment_on(automation: WebAutomation, activity_div: WebElement) -> bool:
    """Simply return True if commented ok, otherwise return False.
    
    
    How to make error more clear???
    
    
    """
    
    logger = automation.logger
    driver = automation.driver

    # move to element - looks more realistic    
    ActionChains(driver).move_to_element(activity_div).perform()
    # ALTERNATIVE:
    # var element = Driver.FindElement(By.Id("element-id"));
    # ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", element);
    
    # try find "Comment" button    
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
        return ""

    if len(comment_btn) != 1:
        logger.warning(f"comment btn has len: {len(comment_btn)}")
        return ""
    
    # can comment
    
   
    
    
    # can comment: get text, feed to llm, get comment
    post_text_cleaned = ""
    try:
        post_text_cleaned = get_post_text(activity_div)
    except:
        logger.exception("Could not get cleaned post text")
        return ""
    
    logger.debug(f"responding to POST (CLEANED):\n{post_text_cleaned}")

    #
    # TO DO: wait until loaded
    #
    try:
        ActionChains(driver).move_to_element(comment_btn[0]).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        click_delay()
    except:
        logger.exception("")
        return ""

    try:
        comment_div = activity_div.find_element(
            By.XPATH,
            ".//div[contains(@class, 'ql-editor ql-blank') and @data-placeholder='Add a comment…']",
        )
        first_p = comment_div.find_element(By.XPATH, "./p[1]")

        my_comment = generate_comment(automation, post_text_cleaned)
        # ChromeDriver doesnt support non-bmp
        my_comment = remove_non_bmp(my_comment)
        
        if len(my_comment) == 0:
            #logger.warning("Failed to generate comment")
            return ""
        
        logger.debug(f"Commenting response:\n{my_comment}")
        first_p.send_keys(my_comment)
        click_delay()
        #
        # TO DO: not clear here whether the button is searched only as
        #        a descendent of the comment_div
        #
        submit_comment_btn = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    ".//button[contains(@class, 'comments-comment-box__submit-button')]",
                )
            )
        )
        
        ActionChains(driver).move_to_element(submit_comment_btn).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        
        return post_text_cleaned

    except NoSuchElementException:
        logger.warning("add comment element not found")
    except GenerateError:
        #retry?
        logger.exception("")
    except:
        logger.exception("")
        
        
    return ""

   

#
# TO DO: add check and log warning if not on feed when called
#
def comment_random_post(automation: WebAutomation, commented_posts: list[str]) -> bool:
    """Try to comment on a random (prioritizing "Suggested" spam) post and return bool
    indicating whether the comment was made"""   
        
    if not go_to_feed(automation):
        return ""
        
    activity_div = pick_random_activity_div(automation, commented_posts)
    if activity_div is None:
        return ""

    return comment_on(automation, activity_div)

    
