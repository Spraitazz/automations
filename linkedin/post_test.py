#
#
# TO DO: move this out to linkedin/post_test.py, also can record a few outout examples somehwere
#
#
import logging
import time
from linkedin.llm import generate_post




logger = logging.getLogger("job_test")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)



post = generate_post(logger)


print(post)

if len(post) < 200: #about 40 tokens?
    print("probably early terminated, try generate again")
    






