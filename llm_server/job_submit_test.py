import logging
import time
from llm_server.external_utils import llm_request

#
# TO DO: modify (async await) to submit 2 or 3, awaiting for them
#

logger = logging.getLogger("job_test")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

prompt = "Write a short story using only 10 words."
llm_params = {"max_tokens": 200, "temperature": 5.0}

st = time.time()
status, resp, num_tries = llm_request(prompt, llm_params, logger)
et = time.time()
print(f"done in {et-st:.1f} s")
print(num_tries)
print(resp)
