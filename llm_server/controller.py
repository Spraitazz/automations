
from utils import init_default_logger
from llm_server.definitions import *
from llm_server.worker import worker as llm_worker
from llm_server.server import app as llm_server_app


llm = None
llm_worker_thread = None
llm_server_thread = None

#
# TO DO: unify logging - currently both passed as argument and used through global LOGGER_NAME
#
def start(controller_logger: logging.Logger):
    """start LLM, worker and uvicorn server to serve FastAPI app defined in server.py"""    
    
    global llm
    global llm_worker_thread
    global llm_server_thread    
    
    try:
        llm = llama_cpp.Llama(
            model_path=str(LLM_GGUF_PATH),
            n_threads=NUM_THREADS_LLM,
            n_ctx=CONTEXT_LEN_LLM,
            verbose=False,
        )
        
        logger, logs_folder_path = init_default_logger(LOGGER_NAME)
        
        llm_worker_thread = StoppableThread(target=llm_worker, daemon=True, args=(llm, logger))
        llm_worker_thread.start()

        config = uvicorn.Config(
            llm_server_app,
            host=LLM_SERVER_HOST,
            port=LLM_SERVER_PORT,
            loop="asyncio",
        )
        llm_server_thread = ServerThread(config)
        llm_server_thread.start()
        return True
    except:
        controller_logger.exception("")
        return False
    
    
# 
# TO DO: wait for server to stop before stopping worker
# TO DO 2: wait for worker to stop??????
#
def stop(controller_logger: logging.Logger):
    """First stop the server, worker might still be working,
    then stop the worker"""

    global llm
    global llm_worker_thread
    global llm_server_thread
    
    try:    
        llm_server_thread.shutdown()
        llm_server_thread = None    
              
        llm_worker_thread.stop()  
        llm_worker_thread = None   
        
        del llm
        llm = None   
        
        return True
    except:
        controller_logger.exception("")
        return False 
        
        
        
        
        
