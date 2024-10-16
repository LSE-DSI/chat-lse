import json

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam
)

def extract_function_calls(chat_completion: ChatCompletion, key: str): 
    try: 
        called_tool = chat_completion.choices[0].message.tool_calls
        if called_tool:
            response_message = chat_completion.choices[0].message.tool_calls[0].function.arguments
        else: 
            response_message = chat_completion.choices[0].message.content
        args = json.loads(response_message)
        return args[key]
    except Exception as e: 
        return e 



def extract_json(chat_response: ChatCompletion):
    to_greet = extract_function_calls(chat_response, "is_greeting") # Judge if query is a greeting 
    is_follow_up = extract_function_calls(chat_response, "is_follow_up") # Judge if query is a follow up question like why, how, more information, etc. 
    is_reference = extract_function_calls(chat_response, "is_reference") # Judge if the query references the previous model response 
    is_relevant = extract_function_calls(chat_response, "is_relevant") # Judge if the query is relevant to the scope of ChatLSE 
    requires_clarification = extract_function_calls(chat_response, "requires_clarification") # Judge if the query requires clarification
    is_farewell = extract_function_calls(chat_response, "is_farewell") # Judge if the query is a farewell message

    return to_greet, is_follow_up, is_reference, is_relevant, requires_clarification, is_farewell



def extract_json_query_rewriter(chat_response: ChatCompletion):
    to_greet = extract_function_calls(chat_response, "is_greeting") # Judge if query is a greeting 
    is_relevant = extract_function_calls(chat_response, "is_relevant") # Judge if the query is relevant to the scope of ChatLSE 
    is_farewell = extract_function_calls(chat_response, "is_farewell") # Judge if the query is a farewell message

    to_greet = parse_type(to_greet)
    is_relevant = parse_type(is_relevant)
    is_farewell = parse_type(is_farewell)

    return to_greet, is_relevant, is_farewell


def parse_type(obj): 
    if type(obj) != bool: 
        return obj.lower() == "true"
    return obj 


def build_filter_function() -> list[ChatCompletionToolParam]:
    return [
        {
        "type": "function",
        "function": {
            "name": "filter_queries",
            "description": '''Decide whether the model should answer a user query by judging whether it is in scope.
                    Respond in the format: {"is_greeting": true/false, "is_follow_up": true/false, "is_reference": true/false, "is_relevant": true/false, "requires_clarification": true/false, "is_farewell": true/false}
                    Do NOT enclose the true or false values in quotes.''',
            "parameters": {
                "type": "object",
                "properties": {
                    "requires_clarification":{
                        "type": "boolean",
                        "description": '''Based ONLY on the last user query, decide if answering this question requires further clarification in order to provide a precise answer. For example, whether the student is a postgraduate or undergraduate. Only answer true if the question is ambiguous or unclear.
                        E.g
                        {"User": "How can I apply for postrgraduate courses at LSE", 
                            "requires_clarification": true}''',
                    },
                    "is_greeting": {
                        "type": "boolean",
                        "description": "Based ONLY on the last user query, decide if the query is a greeting, e.g. Hi, Hello, How are you, What's up, Sup, thanks, thank you, bye, great etc.",
                    },
                    "is_follow_up": {
                        "type": "boolean",
                        "description": '''Based on the last user query and the previous model response (if provided), decide if the user query references or follows up on the model's previous response.
                        Example: 
                        {
                            "model response": "LSE offers courses and modules related to AI, such as ST449 Artificial Intelligence, which covers topics including simple and advanced search algorithms, gameplay, constraint satisfaction problems (CSP), knowledge representation, supervised learning, and reinforcement learning.",
                            "user query": "Tell me more about ST449", 
                            "is_follow_up": ture
                        }
                        ''',
                    },
                    "is_reference": {
                        "type": "boolean",
                        "description": "Based on the last user query and the previous model response (if provided), does the user query mention anything in the previous model response?",
                    },
                    "is_relevant": {
                        "type": "boolean",
                        "description": "You are an assistant at the London School fo Economics (LSE). Your job is to answer any administrative questions that the staff and students may have. You must also handle all mental health related queries. Based on the last user query and the previous model response (if provided), decide if you should answer the user query provided. If the statement is purely conversational (e.g. thanks, bye, etc.), it is not relevant. By more aggressive in filtering out irrelevant queries.",
                    },

                    "is_farewell": {
                        "type": "boolean",
                        "description": '''Based ONLY on the last user query, decide if the user has sent a query that suggests they no longer require your help and are leaving the chat.
                        e.g. 
                        {"user": "Thank you for your help, goodbye"
                            is_farewell: true}''',
                    },
                },
                "required": ["is_greeting", "is_follow_up", "is_reference", "is_relevant", "requires_clarification", "is_farewell"],
            },
        },
    }     
]



def build_response_function() -> list[ChatCompletionToolParam]:
    return [
        {
            "type": "function",
            "function": {
                "name": "is_response",
                "description": '''This function gets called if the chat has reponded to the previous query with a clarifying question. This function determines whether the user has provided an undescrptive answer to the clarifying question.
                For example,
                {"User": "Yes",
                "is_response": true},
                {"User": "No",
                "is_response": false}
                Alternatively, if the chat has given the user a list of options to choose from, the user may respond with a number, letter or exactly copy the option.''',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_response": {
                            "type": "boolean",
                            "description": '''The user has responded to the clarifying question with a non-descriptive answer. For example, if the user responds with "yes" or "no" or repeats an option given by the previous clarifying question, you should respond with true or false.''',
                        },
                    },
                    "required": ["is_response"],
                },
            },
        }
    ]



def build_filter_function_query_rewriter() -> list[ChatCompletionToolParam]:
    return [
        {
        "type": "function",
        "function": {
            "name": "filter_queries",
            "description": '''Decide whether the model should answer a user query by judging whether it is in scope.
                    Respond in the format: {"is_greeting": true/false, "is_relevant": true/false, "is_farewell": true/false}
                    Do NOT enclose the true or false values in quotes.''',
            "parameters": {
                "type": "object",
                "properties": {
                    "is_greeting": {
                        "type": "boolean",
                        "description": "Based ONLY on the last user query, decide if the query is a greeting, e.g. Hi, Hello, How are you, What's up, Sup etc.",
                    },
                    "is_relevant": {
                        "type": "boolean",
                        "description": "You are an assistant at the London School fo Economics (LSE). Your job is to answer any administrative questions that the staff and students may have. You must also handle all mental health related queries. Based on the last user query and the previous model response (if provided), decide if you should answer the user query provided. Pay attention to the user's role withing the LSE, his/her affiliation and the level of studies (if applicable) to give a more accurate response. All questions that mention LSE's courses, policies, career opportunities are relevant. If the statement is purely conversational (e.g. thanks, bye, etc.), it is not relevant. If you are unsure, answer true.",
                    },
                    "is_farewell": {
                        "type": "boolean",
                        "description": '''Based ONLY on the last user query, decide if the user query suggests the termination of the conversation or that they no longer require your help.
                        E.g. Perfect, Thank you, Thanks, Great, Bye, Goodbye, Thank you for your help, etc.''',
                    },
                },
                "required": ["is_greeting", "is_relevant", "is_farewell"],
            },
        },
    }     
]
