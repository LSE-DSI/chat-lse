import json

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam
)

def extract_function_calls(chat_completion: ChatCompletion, key: str): 
    response_message = chat_completion.choices[0].message.tool_calls[0].function.arguments
    args = json.loads(response_message)
    return args[key]


def build_filter_function() -> list[ChatCompletionToolParam]:
    return [
        {
            "type": "function",
            "function": {
                "name": "filter_queries",
                "description": '''Decide whether the model should answer a user query by judging whether it is in scope.
                        Respond in the format: {"is_greeting": true/false, "is_follow_up": true/false, "is_reference": true/false, "is_relevant": true/false, "is_domain_knowledge": true/false, "requires_clarification": true/false, "is_farewell": true/false}
                        Do NOT enclode the true or false values in quotes.''',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "requires_clarification":{
                            "type": "boolean",
                            "description": '''Based ONLY on the last user query, decide if answering this question requires further clarification in order to provide a precise answer.
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
                            "description": '''Based ONLY on the last user query, decide if a given query is a follow-up question to a previous response. A follow-up question typically seeks additional information, clarification, or elaboration on the topic discussed in the prior response. Your goal is to analyze the context and relationship between the response and the query to make this determination. he query should relate directly to the topic or details mentioned in the previous response. The query should logically continue the conversation, seeking further insight or details. The query might aim to clarify a specific point made in the previous response. The query could request more information or expand on the subject introduced earlier.
                             e.g. 
                              {"Previous response": "LSE offers financial support in the form of scholarships, bursaries, student-discounts, PhD funding, and more"
                                "User": "Can you elaborate on scholarships?"
                               is_follow_up: true} ''',
                        },
                        "is_reference": {
                            "type": "boolean",
                          "description": "Based on the last user query and the previous model response (if provided), does the user query mention anything in the previous model response?",
                        },
                        "is_relevant": {
                            "type": "boolean",
                            "description": "You are an assistant at the London School fo Economics (LSE). Your job is to answer any administrative questions that the staff and students may have. You must also handle all mental health related queries. Based on the last user query and the previous model response (if provided), decide if you should answer the user query provided. If the statement is purely conversational (e.g. thanks, bye, etc.), it is not relevant. By more aggressive in filtering out irrelevant queries.",
                        },
                        "is_domain_knowledge": {
                            "type": "boolean",
                            "description": "Based ONLY on the last user query, decide if answering this question requires any specific domain knowledge that is taught in university courses. e.g. Explain dark matter to me, Explain populism, Make a webpage for me in Javascript, etc.",
                        },

                        "is_farewell": {
                            "type": "boolean",
                            "description": '''Based ONLY on the last user query, decide if the user has sent a query that suggests they no longer require your help and are leaving the chat.
                            e.g. 
                            {"user": "Thank you for your help, goodbye"
                             is_farewell: true}''',
                        }
                        },
                        }
                    },
                    "required": ["is_greeting", "is_follow_up", "is_reference", "is_relevant", "is_domain_knowledge", "requires_clarification", "is_farewell"],
                },
            
        
    ]