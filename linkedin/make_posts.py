
from linkedin.definitions import *
from linkedin.utils import click_delay, random_scroll, go_to_feed, remove_non_bmp
from linkedin.llm import generate_post



def start_post_visible(driver) -> bool:
    pass



def make_post(automation: WebAutomation) -> bool:

    logger = automation.logger
    driver = automation.driver

    # first, check I am on feed
    go_to_feed(automation)
    logger.debug("finding 'start a post'")
    
    #
    # TO DO: limit scrolling up time to 1min at most, otherwise stuck in this loop
    #
    # then, scroll up until I can see Start a post thing, then ActionChain go to it:    
    make_post_button = None
    while True: # not automation.stop_event.is_set() OR not session.done_event.is_set()
        # button by class "artdeco-button artdeco-button--muted artdeco-button--4 artdeco-button--tertiary ember-view"
        # which has (go into child recursively) "Start a post" as text
        try:
            make_post_button = driver.find_element(
            "xpath",
            '//button[contains(@class, "artdeco-button") and '
            'contains(@class, "artdeco-button--muted") and '
            'contains(@class, "artdeco-button--4") and '
            'contains(@class, "artdeco-button--tertiary") and '
            'contains(@class, "ember-view")]'
            )            
            deepest_first_desc = automation.get_deepest_first_descendant(make_post_button)
            if "Start a post" not in deepest_first_desc.text:
                #found Start a post button, but some issue
                logger.error(f"text is: {deepest_first_desc.text}")
                make_post_button = None
            break
        except:
            #
            # TO DO: automation.random_scroll
            #
            logger.exception("")
            random_scroll(driver, scroll_up=True)
    
    
    if make_post_button is None:
        return False    

    #
    # TO DO: automation.go_to() and automation.click()??
    #
    ActionChains(driver).move_to_element(make_post_button).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
    click_delay()
    logger.debug("clicked 'start a post'")
        
    #
    # TO DO: wait until this loads
    #    
    div = driver.find_element(
    "xpath",
    '//div[@class="ql-editor ql-blank" and @data-placeholder="What do you want to talk about?"]'
    )
    div.click()
    click_delay()
    
    p = div.find_element("xpath", "./p")
    
    logger.debug("going to generate post")
    my_post = generate_post(logger)    
    # ChromeDriver doesnt support non-bmp
    my_post = remove_non_bmp(my_post)
    if len(my_post) == 0:
        return False
    
    try:
        p.send_keys(my_post)
        click_delay()        
        post_button = driver.find_element(
        "xpath",
        '//span[contains(@class, "artdeco-button__text") and contains(., "Post")]'
        )        
        post_button.click()      
        logger.debug(f"posted:\n\n{my_post}")  
        return True
    except:
        logger.exception("could not post post")
        
    return False
    
    
