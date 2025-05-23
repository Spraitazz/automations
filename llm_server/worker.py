
from llm_server.definitions import *
from llm_server.utils import generate_until_hit


def save_job_result(job: JobRequest, result: dict) -> int:
    """Save job and result to database, returning row index
    of the new row."""    

    df = None
    if pd.io.common.file_exists(PROMPT_STORE_FPATH):
        df = pd.read_csv(PROMPT_STORE_FPATH, index_col=0)
        last_prompt_id = df.index[-1]
    else:
        df = pd.DataFrame(columns=new_row.columns)

    job_info = {
        "model": MODEL_NAME,
        "max_tokens": job.llm_params.max_tokens,
        "temperature": job.llm_params.temperature,
        "top_k": job.llm_params.top_k,
        "top_p": job.llm_params.top_p,
        "repeat_penalty": job.llm_params.repeat_penalty,
        "num_tries": result["num_tries"],
        "max_tries": NUM_MAX_TRIES_GENERATE_DEFAULT,
        "date": str(datetime.now()),
        "extra": "-",
    }
    new_row = pd.DataFrame([job_info])  
    new_index = df.index.max() + 1 if not df.empty else 0
    new_row.index = [new_index]
    df = pd.concat([df, new_row], ignore_index=False)
    df.to_csv(PROMPT_STORE_FPATH)
    
    with open(f"{PROMPT_DIR}/prompt{new_index:05d}", "w") as file:
        file.write(job.prompt)

    if result["num_tries"] != -1:
        with open(f"{PROMPT_DIR}/resp{new_index:05d}", "w") as file:
            file.write(result["response"])
            
    return new_index


def process_llm_job(job: JobRequest, llm: llama_cpp.Llama, logger: logging.Logger):
    """Process single job (normally submitted to LLM server through /submit endpoint):

    have the LLM to continue the given prompt text, retrying in case it returns a stop symbol
    as the first token (up to {NUM_MAX_TRIES_GENERATE_DEFAULT} times), and finally write
    request parameters, prompt and LLM response in the database."""

    job_states[job.job_id] = JobStates.PROCESSING
    logger.debug(f"Processing job (id = {job.job_id}).")

    llm_call_lambda = lambda prompt: llm(
        prompt,        
        max_tokens=job.llm_params.max_tokens,
        temperature=job.llm_params.temperature,
        top_k=job.llm_params.top_k,
        top_p=job.llm_params.top_p,
        repeat_penalty=job.llm_params.repeat_penalty,
    )

    resp, num_tries = generate_until_hit(job.prompt, llm_call_lambda, num_tries_max=job.num_tries_max)

    result = {}
    if num_tries == -1:
        logger.warning(
            f"LLM did not generate output in {NUM_MAX_TRIES_GENERATE_DEFAULT} for job:\n{job}"
        )
        result["status"] = JobResultStatus.FAILED
        result["num_tries"] = NUM_MAX_TRIES_GENERATE_DEFAULT
    else:
        logger.debug(
            f"Job (id = {job.job_id}) completed successfully"
        )  
        result["status"] = JobResultStatus.SUCCESS
        result["num_tries"] = num_tries
        result["response"] = resp

    job_states[job.job_id] = JobStates.DONE
    job_results[job.job_id] = result

    if not SAVE_WORK:
        return

    try:
        new_index = save_job_result(job, result)
        logger.debug(f"Job (id = {job.job_id}) saved, index: {new_index}.")
    except:
        logger.exception(f"Job (id = {job.job_id}) could not be saved")


def worker(llm: llama_cpp.Llama, logger: logging.Logger, stop_event: threading.Event):
    """LLM server worker gets jobs (JobRequest instances), from job_queue (deque),
    processing them sequentially."""

    logger.debug("LLM worker started")

    while not stop_event.is_set():
        job = None
        if job_queue:
            job = job_queue.popleft()   
            process_llm_job(job, llm, logger)         
        else:
            time.sleep(0.1)
            continue
        
    logger.debug("LLM worker stopped by stop event, closing logger")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

