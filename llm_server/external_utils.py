
from definitions import LLM_API_SUBMIT_URL, LLM_API_RESULT_URL
from llm_server.definitions import *

class LLMRequestResultStatus(IntEnum):
    OK = 0
    NOTOK = -2

class LLMRequestResult(BaseModel):
    status: LLMRequestResultStatus
    response: str
    num_tries: int

#
# TO DO: need to add check that llm_params is LLMParams instance, then model_dump()
#
# TO DO: if max_wait_s > 0., need to also add checking for time
#
# TO DO: return failed reason: did not generate in num max tries, OR llm server went off
#
def llm_request(
    prompt: str,
    llm_params: LLMParams,
    num_tries_max: int,
    logger: logging.Logger,
    max_wait_s: float = -1.0,
    result_request_retry_time_s: float = 10.0,
) -> LLMRequestResult:
    """Make call to LLM server with given {prompt} and {llm_params}, first submitting on
    the /submit endpoint and afterwards calling the /result endpoint every 
    {result_request_retry_time_s}, waiting for up to {max_wait_s} (if > 0, currently
    not implemented) for response."""
    

    job_id = str(uuid.uuid4())
    payload = {"prompt": prompt, "job_id": job_id, "llm_params": llm_params.model_dump(), "num_tries_max": num_tries_max}

    try:
        response = requests.post(LLM_API_SUBMIT_URL, json=payload)

        if response.status_code != 200:
            # llm server off?
            logger.warning(
                f"LLM job request failed, response status code: {response.status_code}"
            )
            return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)
        else:
            json = response.json()

            if json["status"] == JobSubmitStatus.ERROR:
                if "status_msg" in json:
                    logger.warning(
                        f'LLM job request declined, status message: {json["status_msg"]}'
                    )
                else:
                    logger.error(
                        f'LLM job request failed, errors: {json["errors"]}'
                    )
                return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)

            if json["status"] == JobSubmitStatus.SUCCESS:
                logger.debug(
                    f'LLM job request submitted successfully, order in queue: {json["order"]}'
                )
    except:
        #
        # MOST LIKELY LLM SERVER OFF?
        #
        logger.exception("llm server likely is off")
        return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)

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
            return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)

        if response.status_code == 200:
            json = response.json()
            result_json = json

            if json["status"] == "badid":
                logger.warning(
                    f"LLM with id {job_id} not found. Possibly LLM server restarted."
                )
                return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)

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
            return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)

        time.sleep(result_request_retry_time_s)

    result = result_json["result"]
    num_tries = result["num_tries"]
    
    #
    # TO DO: this info can be passed more clearly in reqresstatus for calling function to act on
    #
    if result["status"] == -1:
        logger.warning(
            f"llm failed to generate in {num_tries} tries for prompt:\n{prompt}"
        )
        return LLMRequestResult(status=LLMRequestResultStatus.NOTOK, response="", num_tries=-1)

    return LLMRequestResult(status=LLMRequestResultStatus.OK, response=result["response"], num_tries=num_tries)

