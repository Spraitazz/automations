#
#
# TO DO: move this out to linkedin/post_test.py, also can record a few outout examples somehwere
#
#
import logging
import time
from linkedin.prompts_qwen3 import *




logger = logging.getLogger("job_test")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)



post = try_generate_post(logger)


print(post)

if len(post) < 200: #about 40 tokens?
    print("probably early terminated, try generate again")
    






