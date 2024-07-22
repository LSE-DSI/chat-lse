import json

from openai.types.chat import (
    ChatCompletion,
)

def extract_function_calls(chat_completion: ChatCompletion): 
    response_message = chat_completion.choices[0].message.content
    args = json.loads(response_message)
    return args.values()


