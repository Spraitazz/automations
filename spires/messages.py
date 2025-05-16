from spires.definitions import *
from spires.utils import deepest_div, click, click_delay


#
# TO DO: class is overkill, just pass these to select()?
#
class ElemSelector:

    def __init__(self, descendent_of, by: By, selector: str):

        self.descendent_of = descendent_of
        self.by = by
        self.selector = selector

        self.num_max_retries = 10

        #
        #
        # TO DO: this is bad, as if name here does not match automation name in
        # controller.py, logging does not work. Better: pass logger (dont want to fully
        # pass Automation object around because still want to be able to run this independently??)
        #
        #
        self.logger = logging.getLogger(f"{AUTOMATION_NAME}_logger")

    def select(self, i_try=0):

        #
        # TO DO: add all info (
        #
        if i_try == self.num_max_retries:
            raise Exception(f"too many retries ({self.num_max_retries})")

        if i_try > 0:
            self.logger.debug(
                f"trying to select ({self.descendent_of}, {self.by}, {self.selector}), try no {i_try+1}"
            )

        try:
            elem = self.descendent_of.find_element(self.by, self.selector)
            return elem
        except StaleElementReferenceException:
            return self.select(i_try=i_try + 1)
        except Exception:
            raise

        """
        for i_try in range(self.num_max_retries + 1):
            try:
                return self.descendent_of.find_element(self.by, self.selector)
            except StaleElementReferenceException:
                if i_try == self.num_max_retries:
                    raise Exception(f'Too many retries ({self.num_max_retries}) due to stale element.')
            except Exception:
                raise
        """


def extract_student_data(a, logger):
    try:
        name_elem_selector = ElemSelector(
            a, By.CSS_SELECTOR, 'h3[class*="conversationName"]'
        )
        name_elem = name_elem_selector.select()
        # name_elem = a.find_element(By.CSS_SELECTOR, 'h3[class*="conversationName"]')
        text = name_elem.text.strip()
        parts = text.split(" - ")
        if len(parts) != 3:
            logger.warning(f"Unexpected student data format: '{text}'")
            return None
        full_name, degree, subject = map(str.strip, parts)
        name = full_name.split()[0] if " " in full_name else full_name

        student_data = StudentData(
            full_name=full_name, name=name, degree=degree, subject=subject
        )
        return student_data

    except:
        logger.exception("Failed to extract student data")
        return None


#
# TO DO: studentData should be a dataclass/StrEnum?
#
# get visible last message preview of i-th chat, compare to i-th preview from before
def check_chat_seen(
    chat_a: WebElement,
    student_data: StudentData,
    chats_seen: list[dict],
    logger: logging.Logger,
):

    seen = False
    visible_last_msg = ""

    try:
        elem = chat_a.find_element(By.CSS_SELECTOR, 'p[class*="conversationPreview"]')
        visible_last_msg = elem.text.strip()
        max_chars = MAX_CHARS_VISIBLE_LAST_MSG
        if len(visible_last_msg) < max_chars:
            max_chars = len(visible_last_msg)
            logger.warning(
                f"visible_last_msg (= {visible_last_msg}) has length of {max_chars}\
 which is below MAX_CHARS_VISIBLE_LAST_MSG (= {MAX_CHARS_VISIBLE_LAST_MSG})"
            )
        #
        # TO DO: what if everything identical?
        #
        for chat in chats_seen:
            if (
                chat["student_data"] == student_data
                and visible_last_msg[:max_chars] in chat["msg_preview"]
            ):
                seen = True
                break
    except:
        logger.exception("")

    return seen, visible_last_msg


def check_last_msg_student(messages_divs: list[WebElement], logger: logging.Logger):

    last_msg_student = False

    for message_div in messages_divs[::-1]:
        # this order of checking ensures all exclusive:
        # my messages are in divs with class like _owmLine_q33a9_262
        # new email message sent in wmLineAM
        # student messages in divs with class like _wmLine_q33a9_327
        reached_msg = False
        last_msg_student = False
        this_div = message_div
        while not reached_msg:
            if "Scroll or click here to load more messages" in this_div.get_attribute(
                "innerHTML"
            ):
                # did not reach any msgs as have a scroll-worthy amount with this client already
                logger.warning(f"UNEXPECTED")
                reached_msg = True
                break

            # first check for mine as owmLine not contained in other div classes
            with_my_class = this_div.find_elements(
                By.XPATH, './*[contains(@class, "owmLine")]'
            )
            if len(with_my_class) == 1:
                reached_msg = True
                msg_subdiv = with_my_class[0]
                break

            # next, check for "new email message sent" div
            with_email_sent_class = this_div.find_elements(
                By.XPATH, './*[contains(@class, "wmLineAM")]'
            )
            if len(with_email_sent_class) > 0:
                # Skip "New message email sent to {student_name}" div'
                break

            # finally, check for message from student
            with_student_class = this_div.find_elements(
                By.XPATH, './*[contains(@class, "wmLine")]'
            )
            if len(with_student_class) == 1:
                last_msg_student = True
                reached_msg = True
                msg_subdiv = with_student_class[0]
                break

            # go deeper
            try:
                this_div = this_div.find_element(By.XPATH, "./div")
            except:
                # no messages in this message_div
                break

        if reached_msg:
            break

    return last_msg_student


#
# TO DO: check if i am not at messages url
#
# assuming started at MESSAGES_URL,
# check if any unseen chats, go into them, check if needs response.
# after all checked, driver will be at MESSAGES_URL
#
# FLOW:
# 1. select div [CHAT_DIV] which has "ui segments" as part of its class attribute
# 2. select descendent <a> tags of [CHAT_DIV], [CHAT_A_TAGS]
#
def check_messages(automation: WebAutomation, chats_seen: list[dict[Any, Any]] = []):

    logger = automation.logger
    driver = automation.driver

    # wait for messages page to load
    chats_segments_div = None
    try:
        chats_segments_div = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="ui segments"]'))
        )
    except TimeoutException:
        logger.warning(
            f"{MESSAGES_URL} did not load in {DEFAULT_LOAD_WAIT_TIME_S} seconds"
        )
        return chats_seen

    individual_chat_a_tags = chats_segments_div.find_elements(By.XPATH, "./a")
    for i_a, a in enumerate(individual_chat_a_tags):

        student_data = extract_student_data(a, logger)
        if student_data is None:
            continue

        # skip chat if no change from last time it was checked
        seen, visible_last_msg = check_chat_seen(a, student_data, chats_seen, logger)
        if seen:
            continue

        # chat with student_data.full_name not checked, or has new messages: go into chat
        logger.debug(f"Going into chat with {student_data.full_name}")
        click(driver, a)

        # wait for div containing messages to load, retrieving it
        messages_divs = []
        try:
            messages_container = WebDriverWait(driver, DEFAULT_LOAD_WAIT_TIME_S).until(
                EC.presence_of_element_located((By.ID, "announcement-list"))
            )
            messages_divs = messages_container.find_elements(By.XPATH, "./div")
        except TimeoutException:
            logger.warning(
                f"in messages with {student_data.full_name}, page did not load in {DEFAULT_LOAD_WAIT_TIME_S} seconds"
            )
            return chats_seen

        # check if the last message is from the student
        last_msg_student = check_last_msg_student(messages_divs, logger)

        # if last msg is student's, respond
        if last_msg_student:
            # feed student msgs to prompt, get response, send and return to msgs
            logger.debug(f"{student_data.full_name} needs an automatic response")
            # ensure that I have the textbox and send button
            try:
                text_field = driver.find_element(
                    By.XPATH, '//*[contains(@class, "spellMessenger")]'
                )
                send_icon = driver.find_element(
                    By.CSS_SELECTOR, "i.ui.large.paper.plane.icon"
                )
                # pick random response
                response = random.choice(GENERIC_RESPONSES)
                text_field.send_keys(response)
                click_delay()
                click(driver, send_icon)
                logger.debug(f"Sent {student_data.full_name} my response:\n{response}")
            except:
                logger.exception(f"Cannot respond")
                continue
        else:
            logger.debug(f"{student_data.full_name} no need for response")

        # done with this student
        chat = {}
        chat["student_data"] = student_data
        chat["msg_preview"] = visible_last_msg
        chats_seen.append(chat)
        logger.debug(f"returning to messages after checking {student_data.full_name}")
        driver.back()
        click_delay()
        return check_messages(automation, chats_seen=chats_seen)

    return chats_seen
