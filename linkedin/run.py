"""
linkedin/run.py

Current behaviour:

#
# FLOW: find next session, sleep until next session, login at random time during session,
#       make between (min, max) comments, then make a post with probability session_post_chance,
#       but no more than num_max_posts_per_day.
#


TO DO: make behaviour appear more random by picking from a list of actions,
and not being so strictly attached to "sessions"


-----------------------------------------------------------------------
This module contains the high-level functionality of the linkedin automation: 
there are three main times to go to the site - morning (with x % chance),
afternoon (with y % chance) and evening (with z % chance). During one visit
to the site, the automation will perform a random number (N) of actions from
the following list of actions: 

* scroll and "read"
* comment under a post
* make a post
* TO DO: accept connection
* TO DO: respond to messages
* TO DO: upload image with post

Functions:
----------
- run(automation: Automation):
    start the persistent automation
    
Example:
--------
>>> from utils.data_processing import load_csv, clean_missing_values, normalize_columns
>>> df = load_csv("data/my_dataset.csv")
"""
from linkedin.definitions import *
from linkedin.utils import (
    load_config,
    get_session_name,
    time_until_next_session,
    go_to_feed,
    scroll_pretend_read
)
from linkedin.login import login
from linkedin.comment_posts import comment_random_post 
from linkedin.make_posts import make_post


# {session_name: valid session start time range in 24h format}
start_time_range = {
"morning": (8, 10),
"afternoon": (13, 15),
"evening": (18, 20)
} 

# this combination gives a chance of about 0.5 per day
post_probability = {
"morning": 0.1,
"afternoon": 0.2,
"evening": 0.3
}

min_comments_per_session = 0 
max_comments_per_session = 2 

num_max_posts_per_day = 1
num_tries_max_post = 2


#
# TODO: check on starting if llm server is on, notify and stop if not
#
def run(automation: WebAutomation):
    """This linkedin automation works at normal times - morning,
    afternoon, or evening. It waits for the next working period,
    then logs in (if not logged in already), goes to your feed,
    and first comments on between {min_comments_per_session} and
    {max_comments_per_session} random posts, after which it may
    or may not make a single post."""
    
    logger = automation.logger
    try:
        load_config(automation)
    except:
        logger.exception(f"config not ok")
        return
    logger.debug(f"automation started") 

    driver = automation.init_webdriver()
    login(automation)
    
    # wait until feed is loaded
    while True:
        if go_to_feed(automation):
            break
        logger.warning(f"feed did not load in {DEFAULT_LOAD_WAIT_TIME_S} seconds, sleeping for 60s and retrying")
        automation.sleep(60.)          
        
    #
    # TO DO: finish this part in case they add some annoying popup like
    #        "buy our premium trash" on your feed
    #
    # wait for it to load and try click on "Jobs" span
    try:
        jobs_li = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//li[contains(@class, "global-nav__primary-item") and ./a[contains(@href, "linkedin.com/jobs")]]')
                )
        )    
        automation.driver_try_click(jobs_li)
        #
        # TO DO: wait for jobs loaded, if loaded, go_to_feed() and continue
        #
        automation.sleep(10.)
        go_to_feed(automation)
    except:
        logger.exception("")
        

    driver.get(DEFAULT_URL)
    
    commented_posts = []
    num_posts_today = 0
    while True:
        # entering this loop, I am at DEFAULT_URL       
        sleep_s = time_until_next_session(start_time_range)            
        logger.debug(f"sleeping for {sleep_s/3600.:.1f} h until next session")
        automation.sleep(sleep_s)              
          
        session_name = get_session_name(start_time_range)
        if len(session_name) == 0:
            logger.error(f"UNEXPECTED")
            automation.sleep(60.)
            continue
            
        logger.info(f"session '{session_name}' started")
        
        go_to_feed(automation)            

        num_comments_to_make = random.choice([i for i in range(min_comments_per_session,max_comments_per_session+1)])               
        logger.debug(f"will make {num_comments_to_make} comments this session")
        
        logger.debug("scrolling and reading")        
        scroll_pretend_read(driver)
        
        # first do the commenting
        comments_made = 0
        while comments_made < num_comments_to_make: 
            
            commented_post_text = comment_random_post(automation, commented_posts)
            if len(commented_post_text) > 0:
                #
                # TO DO: after a comment, could click button (check for if appeared)
                # "New posts"
                #
                logger.debug("comment success, going to scroll and read")
                comments_made += 1
                commented_posts.append(commented_post_text)
                scroll_pretend_read(driver)
            else:
                logger.warning("comment failed, will retry in 30s")
                automation.sleep(30.)
                continue
        
            
        # then do the posting, only one post in a session     
        if random.uniform(0., 1.) < post_probability[session_name] and num_posts_today < num_max_posts_per_day:
            logger.debug("going to make a post")
            
            num_tries_post = 0
            while num_tries_post < num_tries_max_post: 
                success = make_post(automation)
                if success:
                    logger.debug("post success")
                    break
                
                logger.warning("post failed (try {num_tries_post+1}/{num_tries_max_post}), will retry in 30s")
                num_tries_post += 1
                automation.sleep(30.)
                driver.refresh()              
        
        if session_name == "evening":
            num_posts_today = 0
        
        logger.debug(f"done with session '{session_name}', returning home")        
        driver.get(DEFAULT_URL)        


if __name__ == "__main__":
    pass   
    
    
    
    
    
