import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import configparser
import time
import random
from datetime import datetime
import json
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.support.ui import WebDriverWait

from automation import WebAutomation


BASE_URL = "https://www.skelbiu.lt"
LOGIN_URL = "https://www.skelbiu.lt/users/signin"
MY_ADS_URL = "https://www.skelbiu.lt/mano-skelbimai/"

# to pretend im human, for random (uniform) delay (in s) in given range after actions
CLICK_DELAY_MIN = 2.0
CLICK_DELAY_MAX = 4.0

DEFAULT_LOAD_WAIT_TIME_S = 10

#
# currently this is simply a dict with the unique item idx as keys and last updated
# datetime (iso format) as values, stored in json format.
#

THIS_DIR_PATH = Path(__file__).resolve().parent 
MY_ITEMS_STORE_FPATH = THIS_DIR_PATH / "my_items.json"

