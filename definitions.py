import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import threading
import typing
from enum import IntEnum
import configparser
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from xvfbwrapper import Xvfb


BASE_DIR = Path(__file__).resolve().parent 

DEFAULT_URL = "http://diedai.lt"

SOCKET_PATH = os.environ.get("AUTOMATIONS_SOCKET_PATH", None)
if SOCKET_PATH is None:
    print(
        "AUTOMATIONS_SOCKET_PATH environment variable was not set by systemd.service,\
 did you forget to source ~/.bashrc after running ./setup.sh?"
    )
    exit(0)


LOGS_DIR_PATH = BASE_DIR / "logs"

controller_log_dir_path = LOGS_DIR_PATH / "controller"
controller_log_dir_path.mkdir(parents=True, exist_ok=True)      
CONTROLLER_LOG_PATH = controller_log_dir_path / "log"

#
# TO DO: already need logger here to notify of bad config?
#
config_fpath = Path.home() / "automation_configs" / "controller" / "config.ini"
configfile = configparser.ConfigParser(interpolation=None)
configfile.read(config_fpath)
APP_EMAIL = configfile["DEFAULT"]["APP_EMAIL"].strip()
GMAIL_APP_PASS = configfile["DEFAULT"]["GMAIL_APP_PASS"].strip()
UNHANDLED_EXCEPTION_EMAIL = configfile["DEFAULT"]["UNHANDLED_EXCEPTION_EMAIL"].strip()
#
# TO DO: move to config
#
LOG_LEVEL_DEFAULT = logging.DEBUG
LOG_FORMATTER_DEFAULT = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] - %(levelname)s - %(message)s"
)
LOG_HANDLER_SUFFIX_DEFAULT = "%Y%m%d"
LOG_NUM_DAYS_BACKUP_DEFAULT = 7


# set default browser options
DEFAULT_BROWSER_OPTIONS = webdriver.ChromeOptions()
DEFAULT_BROWSER_OPTIONS.add_argument("--start-maximized")
DEFAULT_BROWSER_OPTIONS.add_argument("--incognito")
DEFAULT_BROWSER_OPTIONS.add_argument("--window-size=1024x768")
## move window off screen
# options.add_argument("--window-position=-32000,-32000")
# options.add_argument('--incognito')
## for headless browser
# options.add_argument('--headless')
# options.add_argument('--disable-gpu')
# options.add_argument('--no-sandbox')  #needed for headless mode
# options.add_argument('--disable-dev-shm-usage')
## extras to simulate a non-headless environment
# options.add_argument('--remote-debugging-port=9221')
# options.add_argument('--disable-software-rasterizer')





