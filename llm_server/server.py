
from llm_server.definitions import *


app = FastAPI()

@app.post("/submit/")
async def submit(request: fastapi.Request) -> dict:

    logger = logging.getLogger(LOGGER_NAME)

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

    logger = logging.getLogger(LOGGER_NAME)

    if job_states[job_id] == JobStates.QUEUED:
        job_queue.remove(job_history[job_id])
        job_states[job_id] = JobStates.CANCELLED
        logger.debug(f"Job (id = {job.job_id}) cancelled.")
        return {"status": "cancelled"}

    return {"status": f"could not cancel job with state {job_states[job_id]}"}


#
# TO DO: an API expecting more than 1 user could not allow checking for jobs
#        that are not mine (I would be identified by unique API_KEY)
#
@app.get("/result/{job_id}")
def result(job_id: str) -> dict:

    logger = logging.getLogger(LOGGER_NAME)

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
