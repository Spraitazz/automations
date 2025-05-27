import os
from pathlib import Path
import configparser
import logging
from logging.handlers import TimedRotatingFileHandler
import typing
from typing import Tuple
import time
import random
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.action_chains import ActionChains
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from web_automation import *
from llm_server.external_utils import LLMParams, llm_request, LLMRequestResult, LLMRequestResultStatus


LOGIN_URL = "https://www.linkedin.com/login/"
FEED_URL = "https://www.linkedin.com/feed/"

DEFAULT_LOAD_WAIT_TIME_S = 10


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config_path = (
    Path.home() / "automation_configs" / "linkedin" / "config.ini"
) 
config = configparser.ConfigParser(interpolation=None)
config.read(config_path)
EMAIL = config["DEFAULT"]["EMAIL"]
PASS = config["DEFAULT"]["PASS"].strip('"')

#
# TO DO: move to config
#
GMAIL_APP_PASS = "xdoh ieyj kqgo ipii"
APP_EMAIL = "robolavicius@gmail.com"
UNHANDLED_EXCEPTION_EMAIL = "jonas.paulavicius@protonmail.com"
#
# TO DO: move to config
#

LLM_PARAMS_COMMENTS = LLMParams(**{
    "max_tokens": int(config["COMMENTS"]["LLM_MAX_TOKENS"]),
    "temperature": float(config["COMMENTS"]["LLM_TEMPERATURE"]),
    "top_k": int(config["COMMENTS"]["LLM_TOP_K"]),
    "top_p": float(config["COMMENTS"]["LLM_TOP_P"]),
    "repeat_penalty": float(config["COMMENTS"]["LLM_REPEAT_PENALTY"]),
})

LLM_PARAMS_POSTS = LLMParams(**{
    "max_tokens": int(config["POSTS"]["LLM_MAX_TOKENS"]),
    "temperature": float(config["POSTS"]["LLM_TEMPERATURE"]),
    "top_k": int(config["POSTS"]["LLM_TOP_K"]),
    "top_p": float(config["POSTS"]["LLM_TOP_P"]),
    "repeat_penalty": float(config["POSTS"]["LLM_REPEAT_PENALTY"]),
})






#
# TO DO: this should probably be defined in llm_server and raised already by llm_request()
#
class GenerateError(Exception):
    """Custom exception for specific errors."""
    pass






