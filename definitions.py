import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import threading
import typing
from enum import IntEnum
import configparser
import time
import asyncio
import uvicorn
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from xvfbwrapper import Xvfb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_URL = "http://diedai.lt"

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

# set browser options
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

config_fpath = (Path.home() / "automation_configs" / "controller" / "config.ini",)
configfile = configparser.ConfigParser(interpolation=None)
configfile.read(config_fpath)
APP_EMAIL = configfile["DEFAULT"]["APP_EMAIL"].strip()
GMAIL_APP_PASS = configfile["DEFAULT"]["GMAIL_APP_PASS"].strip()
UNHANDLED_EXCEPTION_EMAIL = configfile["DEFAULT"]["UNHANDLED_EXCEPTION_EMAIL"].strip()


#
# TO DO: move to config
#
# generate a log file daily, keeping last 7 days backup
LOG_LEVEL_DEFAULT = logging.DEBUG
LOG_FORMATTER_DEFAULT = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] - %(levelname)s - %(message)s"
)
LOG_HANDLER_SUFFIX_DEFAULT = "%Y%m%d"
LOG_NUM_DAYS_BACKUP_DEFAULT = 7

LLM_SERVER_HOST = "127.0.0.1"
LLM_SERVER_PORT = 8000
LLM_SERVER_BASE_URL = f"{LLM_SERVER_HOST}:{LLM_SERVER_PORT}"


class ServerThread(threading.Thread):
    def __init__(self, config: uvicorn.Config):
        super().__init__(daemon=True)
        self.config = config
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        asyncio.run(self.server.serve())

    def shutdown(self):
        self.server.should_exit = True
