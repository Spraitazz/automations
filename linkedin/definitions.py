import os
from pathlib import Path
import configparser
import typing
from typing import Tuple
import time
from datetime import datetime, timedelta
import random

from web_automation import *
from llm_server.external_utils import (
    LLMParams,
    llm_request,
    LLMRequestResult,
    LLMRequestResultStatus,
)


LOGIN_URL = "https://www.linkedin.com/login/"
FEED_URL = "https://www.linkedin.com/feed/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#
# TO DO: a better place for this is config
#
LEN_COMMENT_MIN = 50
LEN_POST_MIN = 200


#
# TO DO: this should probably be defined in llm_server and raised already by llm_request()
#
class GenerateError(Exception):
    """Custom exception for specific errors."""

    pass
