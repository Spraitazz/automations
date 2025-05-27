#
#
# this module should localise everything related to llm generation, so that any change
# to the model used should affect this file only
#
#
from linkedin.definitions import *
from linkedin.qwen3 import prep_comment_prompt, prep_post_prompt, clean_output


#
# TO DO: a better place for this is definitions and even better config?
#
LEN_COMMENT_MIN = 50
LEN_POST_MIN = 200

#
# TO DO: this is not specific to qwen3. Is this basically just calling llm_request??
#
#
# TO DO: need proper exception to signal to caller (respond_comments()) that we need to stop trying as llm server probably off
#
def prompt_llm(prompt: str, llm_params: LLMParams, logger: logging.Logger, num_tries_generate_max: int = 1) -> str:
    """(Blocking) submit prompt to llm, wait for it to respond and return cleaned"""    
 
    logger.debug(f"will submit llm request with prompt:\n{prompt}")        
    result = llm_request(
        prompt, llm_params, num_tries_generate_max, logger
    )
    if result.status != LLMRequestResultStatus.OK:
        logger.error(f"resp status: {result.status}")
        raise Exception("problem with llm server?")    
    
    cleaned_response = clean_output(result.response)        
    return cleaned_response
    
    
def generate_comment(post_text: str, logger: logging.Logger) -> str:    
    prompt = prep_comment_prompt(post_text)
    cleaned_response = prompt_llm(prompt, LLM_PARAMS_COMMENTS, logger)  
    if len(cleaned_response) < LEN_COMMENT_MIN:
        return ""      
    return cleaned_response 

def generate_post(logger: logging.Logger) -> str:
    prompt = prep_post_prompt()
    cleaned_response = prompt_llm(prompt, LLM_PARAMS_POSTS, logger)        
    if len(cleaned_response) < LEN_POST_MIN:
        return ""      
    return cleaned_response
