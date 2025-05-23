
from llm_server.external_utils import llm_request
from linkedin.prompts_comment import PROMPTS_COMMENT
from linkedin.prompts_posts import ALL_POSTS


#for qwen 2.5 7B this worked ok
def prep_comment_prompt(post_text: str):
    prompt_base = random.choice(PROMPTS)
    prompt = prompt_base + "\nPOST: {}\nRESPONSE: ".format(post_text)
    return prompt


#
# TO DO: need proper exception to signal to caller (respond_comments()) that we need to stop trying as llm server probably off
#
def try_generate_comment(post_text: str, logger: logging.Logger):
    
    num_tries_max = 1
    
    prompt = prep_comment_prompt(post_text)
    logger.debug(f"will submit llm request with prompt:\n{prompt}")        
    result = llm_request(
        prompt, LLM_PARAMS_COMMENTS, num_tries_max, logger
    )
    if result.status != LLMRequestResultStatus.OK:
        logger.warning(f"resp status: {result.status}")
        raise Exception("problem with llm server?")

    cleaned_response_text = remove_non_bmp(result.response).replace("\n", " ")
    
    return cleaned_response_text
