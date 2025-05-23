
from llm_server.definitions import *

llm = llama_cpp.Llama(
            model_path=str(LLM_GGUF_PATH),
            n_threads=NUM_THREADS_LLM,
            n_ctx=CONTEXT_LEN_LLM,
            verbose=True,
    )
    
print('\n\n')
for k,v in llm.metadata.items():
    print(k, v)



