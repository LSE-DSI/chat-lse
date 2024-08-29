import json

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam
)

def extract_function_calls(chat_completion: ChatCompletion, key: str): 
    response_message = chat_completion.choices[0].message.tool_calls[0].function.arguments
    args = json.loads(response_message)
    return args[key]

def extract_context(chat_completion: ChatCompletion):
    args = json.loads(chat_completion.choices[0].message.tool_calls[0].function.arguments)
    args_str = str(args)
    return args_str 



def build_filter_function() -> list[ChatCompletionToolParam]:
    return [
        {
        "type": "function",
        "function": {
            "name": "filter_queries",
            "description": '''Decide whether the model should answer a user query by judging whether it is in scope.
                    Respond in the format: {"is_greeting": true/false, "is_follow_up": true/false, "is_reference": true/false, "is_relevant": true/false, "requires_clarification": true/false, "is_farewell": true/false}
                    Do NOT enclode the true or false values in quotes.''',
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
                        "description": '''for example: 
                            {"User": "Can you give me more details,
                            "is_follow_up": true}, explanation: This input is asking for additional information on a previous topic.,
                            {"User": "What other options do I have?",
                            "is_follow_up": true}, explanation: This input is asking for additional options on a previous topic.,
                            {"User": "Why", "How", "What"}
                            "is_follow_up": true}, explanation: This input is asking for additional information on a previous topic.''',
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

def build_context_function() -> list[ChatCompletionToolParam]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_context",
                "description": '''Extract the context of the user's background from their first message. This function is called only once at the beginning of the conversation. 
                        Respond in the format: {"user_description": e.g. student/staff/visitor etc., "department": department user is affiliated with}.
                        You MUST RESPOND
                        If the user responds with N/A or avoids the question, respond with {"user_description": "N/A", "department": "N/A"}
                        If the user responds with a question instead of answering, respond with {"user_description": "N/A", "department": "N/A"}''',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_description": {
                            "type": "string",
                            "description": '''Whether the user is a student, member of staff, visitor, memeber of administrative team etc. You MUST respond. Do not leave it blank.
                            For example, {"User: "I am a new professor in the department of Economics"} should be responded with {"user_description": "new professor"}.''',
                        },
                        "department": {
                            "type": "string",
                            "description": "The department the user is in and the level of study they are at. You MUST respond. Do not leave it blank. For example, if the user is a student in the department of Economics, you should respond with {'department': 'Economics'}.",
                        },
                    },
                    "required": ["user_description", "department"],
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
                Alternatively, if the chat has given the user a list of options to choose from, the user may respond with a number, letter or exactly copy the option. 
                Respond in JSON form ONLY. 
                Respond in the format: {"is_response": true/false}''',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_response": {
                            "type": "string",
                            "description": '''The user has responded to the clarifying question with a non-descriptive answer. For example, if the user responds with "yes" or "no" or repeats an option given by the previous clarifying question, you should respond with {"is_response": true}.''',
                        },
                    },
                    "required": ["is_response"],
                },
            },
        }
    ]

