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


BASE_DIR = Path(__file__).resolve().parent 


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
# TO DO: move this to load_config in utils.py, then pass around config or define global CONFIG there
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


LLM_SERVER_LOCAL_ADDR = "http://localhost" # http://192.168.1.214
LLM_SERVER_PORT = 8000
# @app.post("/submit/")
LLM_API_SUBMIT_URL = f"{LLM_SERVER_LOCAL_ADDR}:LLM_SERVER_PORT/submit"
# @app.get("/result/{job_id}")
LLM_API_RESULT_URL = f"{LLM_SERVER_LOCAL_ADDR}:LLM_SERVER_PORT/result"


