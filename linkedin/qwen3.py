#
#
# this format was tested to work for qwen3-14B (gguf) downloaded from
# https://huggingface.co/bartowski/Qwen_Qwen3-14B-GGUF
#
#
import re
from linkedin.prompts_posts import ALL_POSTS
from linkedin.more_posts import ALL_TRASH_POSTS

system_prompt = "You are a linkedin tech-fiend: a founder, a destroyer, an entrepreneur,\
 a builder, a madman, a roadman, you don't pay taxes, you're a creator, a visionary even.\
 Here are just a select few of your previous posts:\n\n" 
for i, post in enumerate(ALL_POSTS[:4]):
    system_prompt += f"POST {i+1}:\n{post}\n\n"
for i, post in enumerate(ALL_TRASH_POSTS[:4]):
    system_prompt += f"POST {i+4+1}:\n{post}\n\n"

def ends_with_punct_or_hashtag(s: str) -> bool:
    return bool(re.search(r'([.?!]$|#\w+$)', s))


def trim_to_valid_ending(s: str) -> str:
    """a valid ending for a response is a punctuation mark or hashtag followed by
    a word"""
    
    while s and not ends_with_punct_or_hashtag(s):
        s = s[:-1]
    return s
    
    
def remove_think_block(s: str) -> str:
    """qwen3 returns <think> </think> block (empty if /no_think added at start
    of user prompt) that needs to be removed"""
    
    ret = s
    if "</think>" in ret:
        ret = ret.split("</think>", 1)[1].strip()
    return ret
    
    
def clean_output(response: str) -> str:
    """clean up response and return. For Qwen3 need to do some post-cleaning:
    removing <think> (the prompt includes /no_think at the start of the
    user part of prompt)"""  

    cleaned_response = remove_think_block(response)    
    cleaned_response = trim_to_valid_ending(cleaned_response)
    
    if len(cleaned_response) == 0:
        raise GenerateError("could not generate comment")
        
    return cleaned_response
    
      
def prep_comment_prompt(post_text: str) -> str:
    """need /no_think for qwen3 at the start of the user prompt to speed
    up generation""" 
    
    extra_system_prompt = "When writing a comment to a post, you must write a single\
 comment only. You must not write anything before or after the comment. You must not\
 discuss the instructions or write anything other than the comment."
    
    system_prompt_comment = system_prompt + extra_system_prompt
    
    user_prompt = f"/no_think Write a comment to the following post:\n\n{post_text}"   
     
    prompt = f""" 
    <|im_start|>system
    {system_prompt_comment}<|im_end|>
    <|im_start|>user
    {user_prompt}<|im_end|>
    <|im_start|>assistant
    """    
    return prompt

#
# TO DO: modify to style like comment prompt (if that worked)
#
def prep_post_prompt() -> str:
    """need /no_think for qwen3 at the start of the user prompt to speed
    up generation"""    
        
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



