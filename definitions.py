import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import threading
import typing
import configparser
import time


BASE_DIR = Path(__file__).resolve().parent

LOG_LEVEL_DEFAULT = logging.DEBUG
LOG_FORMATTER_DEFAULT = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] - %(levelname)s - %(message)s"
)
LOG_HANDLER_SUFFIX_DEFAULT = "%Y%m%d"
LOG_NUM_DAYS_BACKUP_DEFAULT = 7

LOGS_DIR_PATH = BASE_DIR / "logs"

controller_log_dir_path = LOGS_DIR_PATH / "controller"
controller_log_dir_path.mkdir(parents=True, exist_ok=True)
CONTROLLER_LOG_PATH = controller_log_dir_path / "log"

config_fpath = Path.home() / "automation_configs" / "controller" / "config.ini"
configfile = configparser.ConfigParser(interpolation=None)
configfile.read(config_fpath)
APP_EMAIL = configfile["DEFAULT"]["APP_EMAIL"].strip()
GMAIL_APP_PASS = configfile["DEFAULT"]["GMAIL_APP_PASS"].strip()
UNHANDLED_EXCEPTION_EMAIL = configfile["DEFAULT"]["UNHANDLED_EXCEPTION_EMAIL"].strip()

XVFB_DISPLAY_WIDTH = 2560
XVFB_DISPLAY_HEIGHT = 1600


