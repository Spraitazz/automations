import os
import logging
from logging.handlers import TimedRotatingFileHandler
import typing
from pydantic import BaseModel, Field, conint, confloat, ValidationError
from enum import IntEnum
from threading import Thread
from collections import deque
import uuid
import requests
import time
from datetime import datetime
from llama_cpp import Llama
import fastapi
from fastapi import FastAPI, HTTPException
import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#
# TO DO: automations toolkit should handle logs
#
LOG_PATH = os.path.join(BASE_DIR, "logs/log")


# set this to False to not save prompt/response pairs
SAVE_WORK = True
# where to store prompts (and responses)
PROMPT_DIR = os.path.join(BASE_DIR, "prompts")
# where to store prompt info - request id (links to prompts dir) and llm params
PROMPT_STORE_FPATH = os.path.join(BASE_DIR, "prompt_info.csv")

# @app.post("/submit/")
LLM_API_SUBMIT_URL = "http://localhost:8000/submit"
# @app.get("/result/{job_id}")
LLM_API_RESULT_URL = "http://localhost:8000/result"

# https://www.modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF
LLM_GGUF_FPATH = os.path.join(BASE_DIR, "llm_ggufs", "qwen2.5-7b-instruct-q6_k.gguf")
MODEL_NAME = "qwen2.5-7b-instruct-q6_k"

NUM_THREADS_LLM = 8
CONTEXT_LEN_LLM = 2048

NUM_JOBS_MAX = 3
NUM_TOKENS_PROMPT_MAX = 1024
LEN_PROMPT_MAX = NUM_TOKENS_PROMPT_MAX * 5

NUM_MAX_TRIES_GENERATE_DEFAULT = 2

MAX_TOKENS_MIN = 10
MAX_TOKENS_MAX = 512

TEMPERATURE_MIN = 0.1
TEMPERATURE_MAX = 10.0

TOP_K_MIN = 5
TOP_K_MAX = 200

TOP_P_MIN = 0.1
TOP_P_MAX = 1.0

REPEAT_PENALTY_MIN = 0.1
REPEAT_PENALTY_MAX = 2.0

# default values to use unless the request specifies either
MAX_TOKENS_DEFAULT = 100
TEMPERATURE_DEFAULT = 0.9
TOP_K_DEFAULT = 50
TOP_P_DEFAULT = 0.9
REPEAT_PENALTY_DEFAULT = 1.2


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
