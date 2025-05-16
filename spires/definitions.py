import os
import typing
from typing import Any
from dataclasses import dataclass
import logging
import configparser
import json
import time
from datetime import datetime
import random
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup

from automation import WebAutomation


AUTOMATION_NAME = "spires"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGIN_URL = "https://spires.co/login"
HOME_URL = "https://spires.co"
MESSAGES_URL = "https://spires.co/tutor/messages"

# to pretend im human, for random (uniform) delay (in s) in given range after actions
CLICK_DELAY_MIN = 2.0
CLICK_DELAY_MAX = 4.0

DEFAULT_LOAD_WAIT_TIME_S = 10

# exchange rate api: https://www.exchangerate-api.com/docs/free
SUPPORTED_CURRENCIES_URL = "https://www.exchangerate-api.com/docs/supported-currencies"
EXCHANGE_RATE_API_URL_PLACEHOLDER = "https://v6.exchangerate-api.com/v6/{}/latest/{}"
CURRENCY_UPDATED_LAST = {}
EXCHANGE_RATES = {}  # {key: value} where currency given as key is worth value GBP

# prettified with newlines for sending to students
GENERIC_BID_MSG_PLACEHOLDER = "Hi {},\n\nI would like to offer you my support as a tutor with 10 years of \
experience helping Physics, Mathematics and Programming students achieve their goals. I have two Masters' \
degrees, one in theoretical physics and one in machine learning. Look forward to hearing from you!\n\n{}"


@dataclass
class StudentData:
    full_name: str
    name: str
    degree: str
    subject: str


#
# from below for messages
#

MAX_CHARS_VISIBLE_LAST_MSG = 50

GENERIC_RESPONSES_RELPATH = "generic_responses.txt"

GENERIC_RESPONSES_FPATH = os.path.join(BASE_DIR, GENERIC_RESPONSES_RELPATH)
GENERIC_RESPONSES = []
with open(GENERIC_RESPONSES_FPATH, "r") as f:
    for line in f:
        cleaned = line.strip().strip('"')
        GENERIC_RESPONSES.append(cleaned)
