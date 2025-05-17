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
from xvfbwrapper import Xvfb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_URL = "about:blank"

SOCKET_PATH = os.environ.get("AUTOMATIONS_SOCKET_PATH", None)
if SOCKET_PATH is None:
    print(
        "AUTOMATIONS_SOCKET_PATH environment variable was not set by systemd.service, did you forget to source ~/.bashrc after running ./setup.sh?"
    )
    exit(0)

controller_log_dir_abspath = os.path.join(BASE_DIR, "logs", "controller")
CONTROLLER_LOG_PATH = os.path.join(controller_log_dir_abspath, "log")
if not os.path.exists(CONTROLLER_LOG_PATH):
    os.makedirs(CONTROLLER_LOG_PATH)

# set default browser options
DEFAULT_BROWSER_OPTIONS = webdriver.ChromeOptions()
DEFAULT_BROWSER_OPTIONS.add_argument("--start-maximized")
DEFAULT_BROWSER_OPTIONS.add_argument("--incognito")
DEFAULT_BROWSER_OPTIONS.add_argument("--window-size=1024x768")

config_fpath = (Path.home() / "automation_configs" / "controller" / "config.ini",)
configfile = configparser.ConfigParser(interpolation=None)
configfile.read(config_fpath)
APP_EMAIL = configfile["DEFAULT"]["APP_EMAIL"].strip()
GMAIL_APP_PASS = configfile["DEFAULT"]["GMAIL_APP_PASS"].strip()
UNHANDLED_EXCEPTION_EMAIL = configfile["DEFAULT"]["UNHANDLED_EXCEPTION_EMAIL"].strip()


# generate a log file daily, keeping last 7 days backup
LOG_LEVEL_DEFAULT = logging.DEBUG
LOG_FORMATTER_DEFAULT = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] - %(levelname)s - %(message)s"
)
LOG_HANDLER_SUFFIX_DEFAULT = "%Y%m%d"
LOG_NUM_DAYS_BACKUP_DEFAULT = 7


