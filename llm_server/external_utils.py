#
#
# functions for bots to request (CURRENTLY ONLY BLOCKING) and wait for llm response
#
# TO DO: change to asyncio
#
#
from llm_server.definitions import *


#
# if max_wait_time < 0., then will wait until job is DONE
#
# status = 0 is OK, otherwise failed:
#
# TO DO: need to VALIDATE (so pydantic?) llm_params
#
# TO DO: if max_wait_s > 0., need to also add checking for time
#
# TO DO: failed reason: did not generate in num max tries, OR llm server went off
#
#
#
def llm_request(
    prompt: str,
    llm_params: LLMParams,
    logger: logging.Logger,
    max_wait_s: float = -1.0,
    result_request_retry_time_s: float = 10.0,
):

    job_id = str(uuid.uuid4())
    payload = {"prompt": prompt, "job_id": job_id, "llm_params": llm_params}

    try:
        response = requests.post(LLM_API_SUBMIT_URL, json=payload)

        if response.status_code != 200:
            # llm server off?
            logger.warning(
                f"LLM job request failed, response status code: {response.status_code}"
            )
            return -2, None, None
        else:
            json = response.json()

            if json["status"] == JobSubmitStatus.ERROR:
                if "status_msg" in json:
                    logger.warning(
                        f'LLM job request declined, status message: {json["status_msg"]}'
                    )
                else:
                    logger.warning(
                        f'LLM job request declined, errors: {json["errors"]}'
                    )
                return -2, None, None

            if json["status"] == JobSubmitStatus.SUCCESS:
                logger.debug(
                    f'LLM job request submitted successfully, order in queue: {json["order"]}'
                )
    except:
        #
        # MOST LIKELY LLM SERVER OFF?
        #
        logger.exception("llm server likely is off")
        return -2, None, None

    result_json = None
    while True:
        response = None
        try:
            response = requests.get(f"{LLM_API_RESULT_URL}/{job_id}")
        except:
            #
            # MOST LIKELY LLM SERVER OFF?
            #
            logger.exception("llm server likely is off")
            return -2, None, None

        if response.status_code == 200:
            json = response.json()
            result_json = json

            if json["status"] == "badid":
                logger.warning(
                    f"LLM with id {job_id} not found. Possibly LLM server restarted."
                )
                return -2, None, None

            if json["status"] == JobStates.DONE:
                break

            if json["status"] == JobStates.QUEUED:
                logger.debug(
                    f'LLM job (id = {job_id}) is queued, order: {json["order"]}'
                )
            elif json["status"] == JobStates.PROCESSING:
                logger.debug(f"LLM job (id = {job_id}) is currently being processed")

        else:
            logger.warning(
                f"Request failed, response status code: {response.status_code}"
            )
            return -2, None, None

        time.sleep(result_request_retry_time_s)

    result = result_json["result"]
    num_tries = result["num_tries"]

    if result["status"] == -1:
        logger.warning(
            f"llm failed to generate in {num_tries} tries for prompt:\n{prompt}"
        )
        return -1, None, None

    response_text = result["response"]

    return 0, response_text, num_tries
