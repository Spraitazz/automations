#
#
# TO DO:
#
# 1. llm = Llama() should ideally be called only when the "start llm_server" command is issued
#
#
from queue import Queue
from llm_server.definitions import *
from llm_server.utils import generate_until_hit

# setup logger to generate a file daily, keeping last 7 days backup
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(LOG_PATH, when="midnight", backupCount=7)
handler.suffix = "%Y%m%d"
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


logger.debug("LLM server starting")


job_queue = deque()
job_states = {}  # {str uuid: JobStates}
job_history = {}  # {str uuid: JobRequest}
job_results = (
    {}
)  # {str uuid: dict(['status'] = JobResultStatus, num_tries: int, response: str)}


#
# TO DO: try except block around llm call, return status for error?
# TO DO: generate_until_hit? BUT: shitty prompt will get stuck, so make max_tries=2 or 3
#
def worker(llm: typing.Callable):

    logger.debug("LLM worker started")

    while True:

        job = None
        if job_queue:
            job = job_queue.popleft()
            job_states[job.job_id] = JobStates.PROCESSING
            logger.debug(f"Processing job (id = {job.job_id}).")
        else:
            time.sleep(0.1)
            continue

        llm_call_lambda = lambda prompt: llm(
            prompt,
            max_tokens=job.llm_params.max_tokens,
            temperature=job.llm_params.temperature,
            top_k=job.llm_params.top_k,
            top_p=job.llm_params.top_p,
            repeat_penalty=job.llm_params.repeat_penalty,
        )

        resp, num_tries = generate_until_hit(job.prompt, llm_call_lambda)

        result = {}
        if num_tries == -1:
            logger.warning(
                f"LLM did not generate output in {NUM_MAX_TRIES_GENERATE_DEFAULT} for job:\n{job}"
            )
            # log that couldnt generate in NUM_MAX_TRIES_GENERATE_DEFAULT
            # store error response to return in call to result API
            result["status"] = JobResultStatus.FAILED
            result["num_tries"] = NUM_MAX_TRIES_GENERATE_DEFAULT
        else:
            logger.debug(
                f"Job (id = {job.job_id}) completed successfully"
            )  # . Response:\n{resp}')
            result["status"] = JobResultStatus.SUCCESS
            result["num_tries"] = num_tries
            result["response"] = resp

        job_states[job.job_id] = JobStates.DONE
        job_results[job.job_id] = result

        if not SAVE_WORK:
            continue

        # returned job, finally write to "DB"
        prompt_info = {
            "model": MODEL_NAME,
            "max_tokens": job.llm_params.max_tokens,
            "temperature": job.llm_params.temperature,
            "top_k": job.llm_params.top_k,
            "top_p": job.llm_params.top_p,
            "repeat_penalty": job.llm_params.repeat_penalty,
            "num_tries": num_tries,
            "max_tries": NUM_MAX_TRIES_GENERATE_DEFAULT,
            "date": str(datetime.now()),
            "extra": "-",
        }

        new_row = pd.DataFrame([prompt_info])

        df = None
        if pd.io.common.file_exists(PROMPT_STORE_FPATH):
            df = pd.read_csv(PROMPT_STORE_FPATH, index_col=0)
            last_prompt_id = df.index[-1]
        else:
            df = pd.DataFrame(columns=new_row.columns)

        new_index = df.index.max() + 1 if not df.empty else 0
        new_row.index = [new_index]

        with open(f"{PROMPT_DIR}/prompt{new_index:05d}", "w") as file:
            file.write(job.prompt)

        df = pd.concat([df, new_row], ignore_index=False)
        df.to_csv(PROMPT_STORE_FPATH)

        if num_tries != -1:
            with open(f"{PROMPT_DIR}/resp{new_index:05d}", "w") as file:
                file.write(resp)

        logger.debug(f"Job (id = {job.job_id}) saved, index: {new_index}.")


# initialise LLM
#
# TO DO: automations toolkit should handle this, and the worker stuff
#
llm = Llama(
    model_path=LLM_GGUF_FPATH,
    n_threads=NUM_THREADS_LLM,
    n_ctx=CONTEXT_LEN_LLM,
    verbose=False,
)

app = FastAPI()


Thread(target=worker, daemon=True, args=(llm,)).start()


@app.post("/submit/")
async def submit(request: fastapi.Request) -> dict:

    if len(job_queue) == NUM_JOBS_MAX:
        logger.debug(
            f"will not submit as currently have maximum number of jobs ({NUM_JOBS_MAX}) in queue"
        )
        return {"status": JobSubmitStatus.ERROR, "status_msg": "job queue full"}

    body = await request.json()
    job = None
    try:
        job = JobRequest(**body)
    except ValidationError as e:
        return fastapi.responses.JSONResponse(
            status_code=200,
            content={"status": JobSubmitStatus.ERROR, "errors": e.errors()},
        )
    except Exception as e:
        raise RuntimeError(f"Unexpected error during job submission: {e}") from e

    job_queue.append(job)
    job_states[job.job_id] = JobStates.QUEUED
    job_history[job.job_id] = job
    logger.debug(
        f"Job (id = {job.job_id}) added to queue. Jobs in queue: {len(job_queue)}."
    )
    return {"status": JobSubmitStatus.SUCCESS, "order": job_queue.index(job)}


@app.get("/cancel/{job_id}")
def cancel(job_id: str) -> dict:

    if job_states[job_id] == JobStates.QUEUED:
        job_queue.remove(job_history[job_id])
        job_states[job_id] = JobStates.CANCELLED
        logger.debug(f"Job (id = {job.job_id}) cancelled.")
        return {"status": "cancelled"}

    return {"status": f"could not cancel job with state {job_states[job_id]}"}


#
# TO DO: a proper API could not allow checking for jobs that are not mine (I would be identified by unique API_KEY)
#
@app.get("/result/{job_id}")
def result(job_id: str) -> dict:
    job_result = job_results.get(job_id, None)
    if job_result is None:
        if job_id not in job_states:
            return {"status": "badid"}
        if job_states[job_id] == JobStates.QUEUED:
            #
            # TO DO: here it is possible that I try to get it right after it is popleft'd() but before job_state changed.
            # to do properly need to Lock?
            #
            order = job_queue.index(job_history[job_id])
            return {"status": JobStates.QUEUED, "order": order}
        return {"status": job_states.get(job_id, "badid")}
    else:
        return {"status": JobStates.DONE, "result": job_result}

    # if "error" in response_data:
    #    raise HTTPException(status_code=500, detail=response_data["error"])
