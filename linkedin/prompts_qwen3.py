#
# this format was tested to work for qwen3-14B (gguf) downloaded from
# https://huggingface.co/bartowski/Qwen_Qwen3-14B-GGUF
#
import re
import logging

#from llm_server.external_utils import llm_request
from linkedin.definitions import *
from linkedin.prompts_comment import PROMPTS_COMMENT
from linkedin.prompts_posts import ALL_POSTS

#
# TO DO: this should probably be defined in llm_server and raised already by llm_request()
#
class GenerateError(Exception):
    """Custom exception for specific errors."""
    pass

def ends_with_punct_or_hashtag(s):
    return bool(re.search(r'([.?!]$|#\w+$)', s))

def trim_to_valid_ending(s):
    while s and not ends_with_punct_or_hashtag(s):
        s = s[:-1]  # remove one character from the end
    return s
    
def remove_think_block(s: str):
    ret = s
    if "</think>" in ret:
        ret = ret.split("</think>", 1)[1].strip()
    return ret
    
def prep_comment_prompt(post_text: str) -> str:
    system_prompt = random.choice(PROMPTS_COMMENT)
    user_prompt = f"/no_think Write a comment to the following post:\n\n{post_text}"
    
    prompt = f""" 
    <|im_start|>system
    {system_prompt}<|im_end|>
    <|im_start|>user
    {user_prompt}<|im_end|>
    <|im_start|>assistant
    """
    
    return prompt


def prep_post_prompt() -> str:

    system_prompt = "You are a linkedin tech-fiend: a founder, an entrepreneur, a visionary even.\
 Here are just a select few of your previous posts:\n\n" 
    for i, post in enumerate(ALL_POSTS):
        system_prompt += f"POST {i+1}:\n{post}\n\n"
        
    user_prompt = "/no_think Your followers are hungry for another post, and you are going to either\
 tell them more about your recent work on Diedai, or simply share some of your tech\
 wisdom with these lunatics, or both. You must write a single post only. You must not\
 write anything after the post ends. Do not discuss the instructions or write anything\
 other than the post. Make the post a few paragraphs long, but at the same time concise\
 and not too long."

    prompt = f""" 
    <|im_start|>system
    {system_prompt}<|im_end|>
    <|im_start|>user
    {user_prompt}<|im_end|>
    <|im_start|>assistant
    """
    
    return prompt
 

#
# TO DO: LLMParams should be the object defined in llm_server.definitions
#
#
# TO DO: need proper exception to signal to caller (respond_comments()) that we need to stop trying as llm server probably off
#
def submit_wait_clean(prompt: str, llm_params: dict, logger: logging.Logger, num_tries_generate_max: int = 1) -> str:
    """(Blocking) submit prompt to llm, wait for it to respond,
    clean up response and return. For Qwen3 need to do some post-cleaning:
    removing <think> (the prompt includes /no_think at the start of the
    user part of prompt)"""  
 
    logger.debug(f"will submit llm request with prompt:\n{prompt}")        
    result = llm_request(
        prompt, llm_params, num_tries_generate_max, logger
    )
    if result.status != LLMRequestResultStatus.OK:
        logger.error(f"resp status: {result.status}")
        raise Exception("problem with llm server?")    
    
    cleaned_response = remove_think_block(result.response)    
    cleaned_response = trim_to_valid_ending(cleaned_response)
    
    if len(cleaned_response) == 0:
        raise GenerateError("could not generate comment")
        
    return cleaned_response
    

def try_generate_comment(post_text: str, logger: logging.Logger) -> str:    
    prompt = prep_comment_prompt(post_text)
    cleaned_response = submit_wait_clean(prompt, LLM_PARAMS_COMMENTS, logger)        
    return cleaned_response

def try_generate_post(logger: logging.Logger) -> str:
    prompt = prep_post_prompt()
    cleaned_response = submit_wait_clean(prompt, LLM_PARAMS_POSTS, logger)        
    return cleaned_response
    
    
