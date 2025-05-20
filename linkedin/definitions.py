import os
from pathlib import Path
import configparser
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import random
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
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
from llm_server.external_utils import llm_request


BOT_NAME = "linkedin"

DEFAULT_URL = "http://diedai.lt"

LOGIN_URL = "https://www.linkedin.com/login/"
FEED_URL = "https://www.linkedin.com/feed/"

#
# TO DO: move to config
#
GMAIL_APP_PASS = "xdoh ieyj kqgo ipii"
APP_EMAIL = "robolavicius@gmail.com"
UNHANDLED_EXCEPTION_EMAIL = "jonas.paulavicius@protonmail.com"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "logs/log")

config_path = (
    Path.home() / "automation_configs" / "linkedin" / "config.ini"
) 
config = configparser.ConfigParser(interpolation=None)
config.read(config_path)
EMAIL = config["DEFAULT"]["EMAIL"]
PASS = config["DEFAULT"]["PASS"].strip('"')
LLM_MAX_TOKENS = int(config["DEFAULT"]["LLM_MAX_TOKENS"])
LLM_TEMPERATURE = float(config["DEFAULT"]["LLM_TEMPERATURE"])
LLM_TOP_K = int(config["DEFAULT"]["LLM_TOP_K"])
LLM_TOP_P = float(config["DEFAULT"]["LLM_TOP_P"])
LLM_REPEAT_PENALTY = float(config["DEFAULT"]["LLM_REPEAT_PENALTY"])



# set browser options
DEFAULT_BROWSER_OPTIONS = webdriver.ChromeOptions()
DEFAULT_BROWSER_OPTIONS.add_argument("--start-maximized")
DEFAULT_BROWSER_OPTIONS.add_argument("--incognito")

# respond to num_to_respond in one go
NUM_COMMENTS_ONE_GO = 1
# and sleep for random (uniform) time between
MIN_SLEEP_S = 10.0 * 60.0  # 15 min
MAX_SLEEP_S = 30.0 * 60.0  # 30 min

DEFAULT_LOAD_WAIT_TIME_S = 10

LLM_PARAMS = {
    "max_tokens": LLM_MAX_TOKENS,
    "temperature": LLM_TEMPERATURE,
    "top_k": LLM_TOP_K,
    "top_p": LLM_TOP_P,
    "repeat_penalty": LLM_REPEAT_PENALTY,
}
