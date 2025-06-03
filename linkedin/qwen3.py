#
#
# this format was tested to work for qwen3-14B (gguf) downloaded from
# https://huggingface.co/bartowski/Qwen_Qwen3-14B-GGUF
#
#
import re
import random

from linkedin.definitions import GenerateError
from linkedin.prompts_diedai_posts import POSTS_DIEDAI
from linkedin.prompts_posts import POSTS_TRASH


# for system prompt
num_diedai_posts = 5
num_trash_posts = 3

system_prompt = """You are a linkedin tech-fiend: a founder, a destroyer, an entrepreneur,
 a builder, a madman, a roadman, you don't pay taxes, you're a creator, a visionary even.
 You only speak English and Lithuanian, preferably English unless you are writing a comment
 to a post that is in Lithuanian. Here are just a select few of your previous posts:\n\n""" 
for i, post in enumerate(random.sample(POSTS_DIEDAI, num_diedai_posts)):
    system_prompt += f"POST {i+1}:\n{post}\n\n"
for i, post in enumerate(random.sample(POSTS_TRASH, num_trash_posts)):
    system_prompt += f"POST {i+num_diedai_posts+1}:\n{post}\n\n"


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
        
    user_prompt = """/no_think Your followers are hungry for another post, and they are
 going to gobble up any tech wisdom you might have, either generic, or specific to Diedai.
 You have the choice to either tell them more about your recent work on Diedai, or to
 share what inspires you, drives you. You must write a single post only. You must not
 write anything after the post ends. Do not discuss the instructions or write anything
 other than the post. Make the post a few paragraphs long and concise."""
    prompt = f""" 
    <|im_start|>system
    {system_prompt}<|im_end|>
    <|im_start|>user
    {user_prompt}<|im_end|>
    <|im_start|>assistant
    """    
    return prompt



