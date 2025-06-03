import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
from enum import IntEnum
import typing
from typing import Tuple
from pydantic import BaseModel, Field, conint, confloat, ValidationError
import threading
from collections import deque
import uuid
import requests
import time
from datetime import datetime
import llama_cpp
import asyncio
import uvicorn
import fastapi
from fastapi import FastAPI, HTTPException
import pandas as pd

from definitions import LLM_SERVER_PORT

# DO NOT DELETE ME
BASE_DIR = Path(__file__).resolve().parent

#LLM_CONFIG_PATH = Path.home() / "automation_configs" / "llm_server" / "config.ini"

LOGGER_NAME = "llm_server"

MODEL_NAME = "Qwen3-14B-Q6_K"

LLM_GGUF_PATH = Path.home() / "llm_ggufs" / "Qwen3-14B-Q6_K.gguf"
NUM_THREADS_LLM = 8
CONTEXT_LEN_LLM = 4096

LLM_SERVER_HOST = "0.0.0.0"
# 
# TODO: move to controller.py as only used there?
#
LLM_SERVER_BASE_URL = f"{LLM_SERVER_HOST}:{LLM_SERVER_PORT}"

# set this to False to not save prompt/response pairs
SAVE_WORK = True
# where to store prompts (and responses)
PROMPT_DIR = BASE_DIR / "prompts"
# where to store prompt info - request id (links to prompts dir) and llm params
PROMPT_STORE_FPATH = BASE_DIR / "prompt_info.csv"


NUM_JOBS_MAX = 3
#
# TODO: as not seeing failed generation much (qwen3-14B), and also because it
#       did not make sense on server-side to retry for same job (too long)
#       need to check to make sure this is not hardcoded anywhere
#
NUM_MAX_TRIES_GENERATE_DEFAULT = 1

#https://tokencounter.org/
NUM_CHARACTERS_PER_TOKEN = 4

NUM_TOKENS_PROMPT_MAX = CONTEXT_LEN_LLM
LEN_PROMPT_MAX = NUM_TOKENS_PROMPT_MAX * NUM_CHARACTERS_PER_TOKEN


# default values to use unless the request specifies either
MAX_TOKENS_MIN = 10
MAX_TOKENS_MAX = 1000
MAX_TOKENS_DEFAULT = 100

TEMPERATURE_MIN = 0.1
TEMPERATURE_MAX = 10.0
TEMPERATURE_DEFAULT = 1.0

TOP_K_MIN = 10
TOP_K_MAX = 200
TOP_K_DEFAULT = 50

TOP_P_MIN = 0.1
TOP_P_MAX = 1.0
TOP_P_DEFAULT = 0.9

REPEAT_PENALTY_MIN = 0.1
REPEAT_PENALTY_MAX = 2.0
REPEAT_PENALTY_DEFAULT = 1.2


job_queue = deque()
job_states = {}  # {str uuid: JobStates}
job_history = {}  # {str uuid: JobRequest}
# {str uuid: dict(['status'] = JobResultStatus, ["num_tries"]: int, ["response"]: str)}
job_results = {} 


class LLMParams(BaseModel):
    max_tokens: conint(ge=MAX_TOKENS_MIN, le=MAX_TOKENS_MAX) = MAX_TOKENS_DEFAULT
    temperature: confloat(ge=TEMPERATURE_MIN, le=TEMPERATURE_MAX) = TEMPERATURE_DEFAULT
    top_k: conint(ge=TOP_K_MIN, le=TOP_K_MAX) = TOP_K_DEFAULT
    top_p: confloat(ge=TOP_P_MIN, le=TOP_P_MAX) = TOP_P_DEFAULT
    repeat_penalty: confloat(ge=REPEAT_PENALTY_MIN, le=REPEAT_PENALTY_MAX) = (
        REPEAT_PENALTY_DEFAULT
    )


class JobRequest(BaseModel):
    job_id: str
    prompt: str = Field(min_length=1, max_length=LEN_PROMPT_MAX)
    llm_params: LLMParams = LLMParams()
    num_tries_max: conint(ge=1, le=3) = 1


class JobStates(IntEnum):
    DONE = 0
    QUEUED = 1
    PROCESSING = 2
    CANCELLED = 3


class JobSubmitStatus(IntEnum):
    SUCCESS = 0
    ERROR = 1


class JobResultStatus(IntEnum):
    SUCCESS = 0
    FAILED = -1
   

class ServerThread(threading.Thread):
    def __init__(self, config: uvicorn.Config):
        super().__init__(daemon=True)
        self.config = config
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        asyncio.run(self.server.serve())

    def shutdown(self):
        self.server.should_exit = True
        
        
class StoppableThread:
    def __init__(self, target: callable = lambda: None, args=(), daemon=True):
        self._stop_event = threading.Event()
        args_with_stopevent = list(args)
        args_with_stopevent.append(self._stop_event)
        args_with_stopevent = tuple(args_with_stopevent)
        self._thread = threading.Thread(target=target, args=args_with_stopevent, daemon=daemon)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        #self._thread.join()
    

    
