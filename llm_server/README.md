





-------------------------------
pip install uvicorn
pip install fastapi
pip install pandas

from inside: uvicorn run:app --host 0.0.0.0 --port 8000
from outside: python -m uvicorn llm_server.run:app --host 0.0.0.0 --port 8000



--------------------------------
for merging llm ggufs:

llama-gguf-split --merge <first-split-file-path> <merged-file-path>
example: 
llama-gguf-split --merge qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf qwen2.5-7b-instruct-q5_k_m.gguf


from llama-cpp: 
https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md

using nix:
nix-env --file '<nixpkgs>' --install --attr llama-cpp
