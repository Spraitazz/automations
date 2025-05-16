from llm_server.definitions import *


def generate_until_hit(
    prompt: str,
    llm_call_lambda: typing.Callable,
    num_tries_max: int = NUM_MAX_TRIES_GENERATE_DEFAULT,
):
    response_text = ""
    num_tries = 0
    while len(response_text) == 0 and num_tries < num_tries_max:
        response = llm_call_lambda(prompt)
        response_text = response["choices"][0]["text"].strip()
        my_resp = ""
        try:
            my_resp = response_text[: response_text.index("*")].strip()
        except ValueError:
            my_resp = response_text
        response_text = my_resp
        num_tries += 1

    if num_tries == num_tries_max and len(response_text) == 0:
        return None, -1

    return response_text, num_tries
