import pathlib
from collections.abc import AsyncGenerator
from typing import (
    Any,
)

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
)
from openai_messages_token_helper import build_messages, get_token_limit

from .globals import global_storage

from .api_models import ThoughtStep
from .postgres_searcher import PostgresSearcher
from chatlse.embeddings import compute_text_embedding
from chatlse.llm_functions import build_filter_function, extract_function_calls, build_context_function, extract_context, build_response_function


class AdvancedRAGChat:

    def __init__(
        self,
        *,
        searcher: PostgresSearcher,
        chat_client: AsyncOpenAI,
        chat_model: str,
        chat_deployment: str | None,  # Not needed for non-Azure OpenAI
        embed_client: AsyncOpenAI,
        embed_deployment: str | None,  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embed_model: str,
        embed_dimensions: int,
        context_window_override: int | None # Context window size (default to 4000 if None)
    ):
        self.searcher = searcher
        self.chat_client = chat_client
        self.chat_model = chat_model
        self.chat_deployment = chat_deployment
        self.embed_client = embed_client
        self.embed_deployment = embed_deployment
        self.embed_model = embed_model
        self.embed_dimensions = embed_dimensions
        self.chat_token_limit = context_window_override if context_window_override else get_token_limit(chat_model, default_to_minimum=True)
        current_dir = pathlib.Path(__file__).parent
        self.query_prompt_template = open(current_dir / "prompts/query.txt").read()
        self.greeting_prompt_template = open(current_dir / "prompts/greeting.txt").read()
        self.rag_answer_prompt_template = open(current_dir / "prompts/rag_answer_advanced.txt").read()
        self.no_answer_prompt_template = open(current_dir / "prompts/no_answer_advanced.txt").read()
        self.follow_up_prompt_template = open(current_dir / "prompts/follow_up.txt").read()
        self.get_context_prompt_template = open(current_dir / "prompts/get_context.txt").read()
        self.require_clarification_prompt_template = open(current_dir / "prompts/clarification.txt").read()
        self.farewell_prompt_template = open(current_dir / "prompts/farewell.txt").read()
        self.clarification_response_prompt_template = open(current_dir / "prompts/clarification_response.txt").read()
        self.clar_response_prompt_template = open(current_dir / "prompts/clar_response.txt").read()
        self.first_message = open(current_dir / "prompts/first_question.txt").read()
        #self.summarise_prompt_template = open(current_dir / "prompts/summarize.txt").read()

    async def run(
        self, messages: list[dict], overrides: dict[str, Any] = {}
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:

        text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        top = overrides.get("top", 3)

        original_user_query = messages[-1]["content"]
        past_messages = messages[:-1]

        # Clear cached RAG results if it builds up 
        if len(global_storage.rag_results) >= 3: 
            global_storage.rag_results = [global_storage.rag_results[-1]]


        ############################################################################################################################################################
        # Summarising last chat model output 
        """if past_messages: 
            to_summarise = past_messages[-1]["content"] 
            response_token_limit = 1024
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.summarise_prompt_template,
                new_user_content=to_summarise,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

            chat_completion_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                stream=False,
            )

            past_messages[-1]["content"] = chat_completion_response.choices[0].message.content"""



        ############################################################################################################################################################
        # Generate the prompt that asks the model to decide whether it should answer the use query (use rag)

        ### Define extract_json function to extract the json object from the response message

        def extract_json(chat_response: ChatCompletion):
            to_greet = extract_function_calls(chat_completion_resp_filter, "is_greeting") # Judge if query is a greeting 
            is_follow_up = extract_function_calls(chat_completion_resp_filter, "is_follow_up") # Judge if query is a follow up question like why, how, more information, etc. 
            is_reference = extract_function_calls(chat_completion_resp_filter, "is_reference") # Judge if the query references the previous model response 
            is_relevant = extract_function_calls(chat_completion_resp_filter, "is_relevant") # Judge if the query is relevant to the scope of ChatLSE 
            requires_clarification = extract_function_calls(chat_completion_resp_filter, "requires_clarification") # Judge if the query requires clarification
            is_farewell = extract_function_calls(chat_completion_resp_filter, "is_farewell") # Judge if the query is a farewell message

            return to_greet, is_follow_up, is_reference, is_relevant, requires_clarification, is_farewell
        

        first_message = not past_messages

        query_response_token_limit = 500
        try: 
            query_messages = build_messages(
                model=self.chat_model,
                system_prompt=self.query_prompt_template,
                new_user_content=original_user_query,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - query_response_token_limit,  # TODO: count functions
                fallback_to_default=True,
            )
        except IndexError: 
            query_messages = build_messages(
                model=self.chat_model,
                system_prompt=self.query_prompt_template,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - query_response_token_limit,  # TODO: count functions
                fallback_to_default=True,
            )
        
        if first_message:
            print("ABOUT TO MAKE CONTEXT CALL!")
            message = build_messages(
                model=self.chat_model,
                system_prompt=self.get_context_prompt_template,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - query_response_token_limit,
                fallback_to_default=True,
            )
            print("ABOUT TO CALL CONTEXT FUNCTION!")
            chat_completion_context_response = await self.chat_client.chat.completions.create(
                    # Azure OpenAI takes the deployment name as the model name
                    model=self.chat_deployment if self.chat_deployment else self.chat_model,
                    messages=message,  # type: ignore
                    temperature=0, # Setting temperature to 0 for testing
                    max_tokens=100,
                    n=1,
                    tools=build_context_function(),
                    tool_choice="required",
                    response_format = {"type": "json_object"},
                    stream=False,
                )
            user_context = extract_context(chat_completion_context_response)
            global_storage.user_context = user_context
            print(f"USER CONTEXT: {user_context}")
            

        
        chat_completion_resp_filter: ChatCompletion = await self.chat_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            # Azure OpenAI takes the deployment name as the model name
            model=self.chat_deployment if self.chat_deployment else self.chat_model,
            temperature=0,  # Minimize creativity for search query generation
            max_tokens=100,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            tools=build_filter_function(),
            tool_choice="required",
            response_format = {"type": "json_object"}
        )
        print(chat_completion_resp_filter)
        print("FILTER FUNCTION RESPONSE")

        to_greet, is_follow_up, is_reference, is_relevant, requires_clarification, is_farewell = extract_json(chat_completion_resp_filter)


        print (f"LENGTH OF PAST MESSAGES: {len(past_messages)}")
        print(f"To greet: {to_greet}, is_follow_up: {is_follow_up}, is_reference: {is_reference}, is_relevant: {is_relevant}, requires_clarification: {requires_clarification}, is_farewell: {is_farewell}")


        to_search = is_relevant and (not requires_clarification) and (not first_message) and (not is_follow_up) # whether model uses RAG functionality 
        print(f"To search: {to_search}")
        to_follow_up = is_follow_up and (not first_message) and (not requires_clarification) and (not clarification_response) # Whether model considers the query a follow up question that requires expanding on revious answer 
        print(f"To follow_up: {to_follow_up}")
    
        



        # Deciding whether to invoke RAG functionalities 







        ############################################################################################################################################################
        # Inserting different system prompts for model based on specific functionalities required 
        response_token_limit = 1024

        if global_storage.requires_clarification:
            print("ENTERED GLOBAL STORAGE CLARIFICATION")
            print(global_storage.requires_clarification)
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.clarification_response_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True
            )

            chat_completion_clar_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                tools=build_response_function(),
                tool_choice="required",
                response_format = {"type": "json_object"},
                stream=False,
            )

            clarification_response = extract_context(chat_completion_clar_response)
            #reset global storage until next requires_clarification occurs.
            global_storage.requires_clarification = False
        
        else:
            clarification_response = False


        if first_message:  
            print("BUILDING FIRST MESSAGE")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.first_message,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_greet and not first_message:
            print("ENTERED GREETING")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.greeting_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_follow_up and not first_message: 
            print("ENTERED FOLLOW UP OR CLARIFICATION")

            content = global_storage.rag_results[-1]

            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.follow_up_prompt_template,
                new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content,
                past_messages=[past_messages[-1]], 
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif requires_clarification and not first_message:
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.require_clarification_prompt_template,
                new_user_content = original_user_query,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )
            global_storage.requires_clarification = True
        

        elif is_farewell and not first_message:
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.farewell_prompt_template,
                new_user_content = original_user_query,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_search and (not requires_clarification and not to_greet and not first_message) or clarification_response: 
            # Retrieve relevant documents from the database with the GPT optimized query
            vector: list[float] = []
            query_text = None 
            if vector_search:
                if clarification_response:
                    print(f"Entering clarification response vector search with query text: {past_messages[-2]['content']}")
                    vector = await compute_text_embedding(
                        past_messages[-2]["content"],
                        None,
                        self.embed_model
                    )
                elif to_search:
                    print(f"Entering vector search with query text: {original_user_query}")
                    vector = await compute_text_embedding(
                        original_user_query,
                        None,
                        self.embed_model 
                    )

            if not text_search:
                query_text = None

            results = await self.searcher.search(query_text, vector, top)

            sources_content = [f"[{(doc.doc_id)}]: {doc.to_str_for_rag()}\n\n" for doc in results]
            content = "\n".join(sources_content)
            global_storage.rag_results.append(content)
 
            if clarification_response:
                messages = build_messages(
                    model = self.chat_model,
                    system_prompt = self.clar_response_prompt_template,
                    new_user_content = original_user_query,
                    past_messages= past_messages,
                    max_tokens=self.chat_token_limit - response_token_limit,
                    fallback_to_default=True,
                )

            else:
                messages = build_messages(
                    model=self.chat_model,
                    system_prompt=self.rag_answer_prompt_template,
                    new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content,
                    past_messages=past_messages,
                    max_tokens=self.chat_token_limit - response_token_limit,
                    fallback_to_default=True,
                )


        # If the model decides the query does not require RAG 
        else: 
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.no_answer_prompt_template,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
           )

        ############################################################################################################################################################
        
        # Generate answer to user query 

        chat_completion_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                stream=False,
            )
        
        chat_resp = chat_completion_response.model_dump()

        # Include ThoughtStep data for display in frontend 
        if to_search and (not requires_clarification and not to_greet and not first_message): 
            chat_resp["choices"][0]["context"] = {
                "data_points": {"text": sources_content},
                "thoughts": [
                    ThoughtStep(
                        title="Whether RAG functionalities are used",
                        description=to_search,
                        props={
                            "RAG": to_search
                        }
                    ),
                    ThoughtStep(
                        title="Search query for database",
                        description=query_text,
                        props={
                            "top": top,
                            "vector_search": vector_search,
                            "text_search": text_search,
                        },
                    ),
                    ThoughtStep(
                        title="Search results",
                        description=[result.to_dict() for result in results],
                    ),
                    ThoughtStep(
                        title="Prompt to generate answer",
                        description=[str(message) for message in messages],
                        props=(
                            {"model": self.chat_model, "deployment": self.chat_deployment}
                            if self.chat_deployment
                            else {"model": self.chat_model}
                        ),
                    ),
                ],
            }
        else: 
            chat_resp["choices"][0]["context"] = {
                "data_points": {"text": None},
                "thoughts": [
                    ThoughtStep(
                        title="Whether RAG functionalities are used",
                        description=False,
                        props={
                            "RAG":False
                        }
                    ),
                    ThoughtStep(
                        title="Search query for database",
                        description=None,
                    ),
                    ThoughtStep(
                        title="Search results",
                        description=None,
                    ),
                    ThoughtStep(
                        title="Prompt to generate answer",
                        description=[str(message) for message in messages],
                        props=(
                            {"model": self.chat_model, "deployment": self.chat_deployment}
                            if self.chat_deployment
                            else {"model": self.chat_model}
                        ),
                    ),
                ],
            }

        return chat_resp

class AdvancedRAGChatMistral:

    def __init__(
        self,
        *,
        searcher: PostgresSearcher,
        chat_client: AsyncOpenAI,
        chat_model: str,
        chat_deployment: str | None,  # Not needed for non-Azure OpenAI
        embed_client: AsyncOpenAI,
        embed_deployment: str | None,  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embed_model: str,
        embed_dimensions: int,
        context_window_override: int | None # Context window size (default to 4000 if None)
    ):
        self.searcher = searcher
        self.chat_client = chat_client
        self.chat_model = chat_model
        self.chat_deployment = chat_deployment
        self.embed_client = embed_client
        self.embed_deployment = embed_deployment
        self.embed_model = embed_model
        self.embed_dimensions = embed_dimensions
        self.chat_token_limit = context_window_override if context_window_override else get_token_limit(chat_model, default_to_minimum=True)
        current_dir = pathlib.Path(__file__).parent
        self.query_prompt_template = open(current_dir / "prompts/query.txt").read()
        self.greeting_prompt_template = open(current_dir / "prompts/greeting.txt").read()
        self.rag_answer_prompt_template = open(current_dir / "prompts/rag_answer_advanced.txt").read()
        self.no_answer_prompt_template = open(current_dir / "prompts/no_answer_advanced.txt").read()
        self.follow_up_prompt_template = open(current_dir / "prompts/follow_up.txt").read()
        self.get_context_prompt_template = open(current_dir / "prompts/get_context.txt").read()
        self.require_clarification_prompt_template = open(current_dir / "prompts/clarification.txt").read()
        self.farewell_prompt_template = open(current_dir / "prompts/farewell.txt").read()
        self.clarification_response_prompt_template = open(current_dir / "prompts/clarification_response.txt").read()
        self.clar_response_prompt_template = open(current_dir / "prompts/clar_response.txt").read()
        self.first_message = open(current_dir / "prompts/first_question.txt").read()
        #self.summarise_prompt_template = open(current_dir / "prompts/summarize.txt").read()

    async def run(
        self, messages: list[dict], overrides: dict[str, Any] = {}
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:

        text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        top = overrides.get("top", 3)

        original_user_query = messages[-1]["content"]
        past_messages = messages[:-1]

        # Clear cached RAG results if it builds up 
        if len(global_storage.rag_results) >= 3: 
            global_storage.rag_results = [global_storage.rag_results[-1]]


        ############################################################################################################################################################
        # Summarising last chat model output 
        """if past_messages: 
            to_summarise = past_messages[-1]["content"] 
            response_token_limit = 1024
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.summarise_prompt_template,
                new_user_content=to_summarise,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

            chat_completion_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                stream=False,
            )

            past_messages[-1]["content"] = chat_completion_response.choices[0].message.content"""



        ############################################################################################################################################################
        # Generate the prompt that asks the model to decide whether it should answer the use query (use rag)

        ### Define extract_json function to extract the json object from the response message

        def extract_json(chat_response: ChatCompletion):
            to_greet = extract_function_calls(chat_completion_resp_filter, "is_greeting") # Judge if query is a greeting 
            is_follow_up = extract_function_calls(chat_completion_resp_filter, "is_follow_up") # Judge if query is a follow up question like why, how, more information, etc. 
            is_reference = extract_function_calls(chat_completion_resp_filter, "is_reference") # Judge if the query references the previous model response 
            is_relevant = extract_function_calls(chat_completion_resp_filter, "is_relevant") # Judge if the query is relevant to the scope of ChatLSE 
            requires_clarification = extract_function_calls(chat_completion_resp_filter, "requires_clarification") # Judge if the query requires clarification
            is_farewell = extract_function_calls(chat_completion_resp_filter, "is_farewell") # Judge if the query is a farewell message

            return to_greet, is_follow_up, is_reference, is_relevant, requires_clarification, is_farewell
        

        first_message = not past_messages

        query_response_token_limit = 500
        try: 
            query_messages = build_messages(
                model=self.chat_model,
                system_prompt=self.query_prompt_template,
                new_user_content=original_user_query,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - query_response_token_limit,  # TODO: count functions
                fallback_to_default=True,
            )
        except IndexError: 
            query_messages = build_messages(
                model=self.chat_model,
                system_prompt=self.query_prompt_template,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - query_response_token_limit,  # TODO: count functions
                fallback_to_default=True,
            )
        
        if first_message:
            print("ABOUT TO MAKE CONTEXT CALL!")
            message = build_messages(
                model=self.chat_model,
                system_prompt=self.get_context_prompt_template,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - query_response_token_limit,
                fallback_to_default=True,
            )
            print("ABOUT TO CALL CONTEXT FUNCTION!")
            chat_completion_context_response = await self.chat_client.chat.completions.create(
                    # Azure OpenAI takes the deployment name as the model name
                    model=self.chat_deployment if self.chat_deployment else self.chat_model,
                    messages=message,  # type: ignore
                    temperature=0, # Setting temperature to 0 for testing
                    max_tokens=100,
                    n=1,
                    tools=build_context_function(),
                    tool_choice="required",
                    stream=False,
                )
            user_context = extract_context(chat_completion_context_response)
            global_storage.user_context = user_context
            print(f"USER CONTEXT: {user_context}")
            

        
        chat_completion_resp_filter: ChatCompletion = await self.chat_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            # Azure OpenAI takes the deployment name as the model name
            model=self.chat_deployment if self.chat_deployment else self.chat_model,
            temperature=0,  # Minimize creativity for search query generation
            max_tokens=100,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            tools=build_filter_function(),
            tool_choice="required"
        )
        print(chat_completion_resp_filter)
        print("FILTER FUNCTION RESPONSE")

        to_greet, is_follow_up, is_reference, is_relevant, requires_clarification, is_farewell = extract_json(chat_completion_resp_filter)


        print (f"LENGTH OF PAST MESSAGES: {len(past_messages)}")
        print(f"To greet: {to_greet}, is_follow_up: {is_follow_up}, is_reference: {is_reference}, is_relevant: {is_relevant}, requires_clarification: {requires_clarification}, is_farewell: {is_farewell}")


        to_search = is_relevant and (not requires_clarification) and (not first_message) and (not is_follow_up) # whether model uses RAG functionality 
        print(f"To search: {to_search}")
        to_follow_up = is_follow_up and (not first_message) and (not requires_clarification) and (not clarification_response) # Whether model considers the query a follow up question that requires expanding on revious answer 
        print(f"To follow_up: {to_follow_up}")
    
        



        # Deciding whether to invoke RAG functionalities 







        ############################################################################################################################################################
        # Inserting different system prompts for model based on specific functionalities required 
        response_token_limit = 1024

        if global_storage.requires_clarification:
            print("ENTERED GLOBAL STORAGE CLARIFICATION")
            print(global_storage.requires_clarification)
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.clarification_response_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True
            )

            chat_completion_clar_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                tools=build_response_function(),
                tool_choice="required",
                stream=False,
            )

            clarification_response = extract_context(chat_completion_clar_response)
            #reset global storage until next requires_clarification occurs.
            global_storage.requires_clarification = False
        
        else:
            clarification_response = False


        if first_message:  
            print("BUILDING FIRST MESSAGE")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.first_message,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_greet and not first_message:
            print("ENTERED GREETING")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.greeting_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_follow_up and not first_message: 
            print("ENTERED FOLLOW UP OR CLARIFICATION")

            content = global_storage.rag_results[-1]

            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.follow_up_prompt_template,
                new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content,
                past_messages=[past_messages[-1]], 
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif requires_clarification and not first_message:
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.require_clarification_prompt_template,
                new_user_content = original_user_query,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )
            global_storage.requires_clarification = True
        

        elif is_farewell and not first_message:
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.farewell_prompt_template,
                new_user_content = original_user_query,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_search and (not requires_clarification and not to_greet and not first_message) or clarification_response: 
            # Retrieve relevant documents from the database with the GPT optimized query
            vector: list[float] = []
            query_text = None 
            if vector_search:
                if clarification_response:
                    print(f"Entering clarification response vector search with query text: {past_messages[-2]['content']}")
                    vector = await compute_text_embedding(
                        past_messages[-2]["content"],
                        None,
                        self.embed_model
                    )
                elif to_search:
                    print(f"Entering vector search with query text: {original_user_query}")
                    vector = await compute_text_embedding(
                        original_user_query,
                        None,
                        self.embed_model 
                    )

            if not text_search:
                query_text = None

            results = await self.searcher.search(query_text, vector, top)

            sources_content = [f"[{(doc.doc_id)}]: {doc.to_str_for_rag()}\n\n" for doc in results]
            content = "\n".join(sources_content)
            global_storage.rag_results.append(content)
 
            if clarification_response:
                messages = build_messages(
                    model = self.chat_model,
                    system_prompt = self.clar_response_prompt_template,
                    new_user_content = original_user_query,
                    past_messages= past_messages,
                    max_tokens=self.chat_token_limit - response_token_limit,
                    fallback_to_default=True,
                )

            else:
                messages = build_messages(
                    model=self.chat_model,
                    system_prompt=self.rag_answer_prompt_template,
                    new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content,
                    past_messages=past_messages,
                    max_tokens=self.chat_token_limit - response_token_limit,
                    fallback_to_default=True,
                )


        # If the model decides the query does not require RAG 
        else: 
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.no_answer_prompt_template,
                new_user_content=original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
           )

        ############################################################################################################################################################
        
        # Generate answer to user query 

        chat_completion_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                stream=False,
            )
        
        chat_resp = chat_completion_response.model_dump()

        # Include ThoughtStep data for display in frontend 
        if to_search and (not requires_clarification and not to_greet and not first_message): 
            chat_resp["choices"][0]["context"] = {
                "data_points": {"text": sources_content},
                "thoughts": [
                    ThoughtStep(
                        title="Whether RAG functionalities are used",
                        description=to_search,
                        props={
                            "RAG": to_search
                        }
                    ),
                    ThoughtStep(
                        title="Search query for database",
                        description=query_text,
                        props={
                            "top": top,
                            "vector_search": vector_search,
                            "text_search": text_search,
                        },
                    ),
                    ThoughtStep(
                        title="Search results",
                        description=[result.to_dict() for result in results],
                    ),
                    ThoughtStep(
                        title="Prompt to generate answer",
                        description=[str(message) for message in messages],
                        props=(
                            {"model": self.chat_model, "deployment": self.chat_deployment}
                            if self.chat_deployment
                            else {"model": self.chat_model}
                        ),
                    ),
                ],
            }
        else: 
            chat_resp["choices"][0]["context"] = {
                "data_points": {"text": None},
                "thoughts": [
                    ThoughtStep(
                        title="Whether RAG functionalities are used",
                        description=False,
                        props={
                            "RAG":False
                        }
                    ),
                    ThoughtStep(
                        title="Search query for database",
                        description=None,
                    ),
                    ThoughtStep(
                        title="Search results",
                        description=None,
                    ),
                    ThoughtStep(
                        title="Prompt to generate answer",
                        description=[str(message) for message in messages],
                        props=(
                            {"model": self.chat_model, "deployment": self.chat_deployment}
                            if self.chat_deployment
                            else {"model": self.chat_model}
                        ),
                    ),
                ],
            }

        return chat_resp
    
    