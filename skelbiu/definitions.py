import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import configparser
import time
import random
from datetime import datetime
import json

from web_automation import *


THIS_DIR_PATH = Path(__file__).resolve().parent

BASE_URL = "https://www.skelbiu.lt"
LOGIN_URL = "https://www.skelbiu.lt/users/signin"
MY_ADS_URL = "https://www.skelbiu.lt/mano-skelbimai/"

#
# currently this is simply a dict with the unique item idx as keys and last updated
# datetime (iso format) as values, stored in json format.
#
MY_ITEMS_STORE_FPATH = THIS_DIR_PATH / "my_items.json"
