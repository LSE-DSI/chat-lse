import json
import pathlib
from collections.abc import AsyncGenerator
from typing import (
    Any,
)
from .logger import logger

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
)
from openai_messages_token_helper import build_messages, get_token_limit
 

from .globals import global_storage

from .api_models import ThoughtStep
from .postgres_neo4j_searcher import PostgresSearcher
from chatlse.embeddings import compute_text_embedding
from chatlse.llm_functions import build_filter_function, build_filter_function_query_rewriter, extract_function_calls, extract_json, extract_json_query_rewriter, build_response_function, build_cypher_query


class AdvancedRAGChat: 
    def __init__(
        self,
        *,
        searcher: PostgresSearcher,
        chat_client: AsyncOpenAI,
        chat_model: str,
        embed_model: str,
        embed_dimensions: int,
        context_window_override: int | None, # Context window size (default to 4000 if None)
        to_summarise: bool | None 
    ):
        self.searcher = searcher
        self.chat_client = chat_client
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.embed_dimensions = embed_dimensions
        self.chat_token_limit = context_window_override if context_window_override else get_token_limit(chat_model, default_to_minimum=True)
        self.to_summarise = to_summarise 
        
        # Load prompts 
        current_dir = pathlib.Path(__file__).parent
        # Classify query 
        self.query_prompt_template = open(current_dir / f"prompts/query.txt").read()
        # Summariser prompt 
        self.summarise_prompt_template = open(current_dir / f"prompts/summarize.txt").read()
        # Decide whether a query is a response to clarification question 
        self.clarification_response_prompt_template = open(current_dir / f"prompts/clarification_response.txt").read()
        # Handling different types of queries 
        self.greeting_prompt_template = open(current_dir / f"prompts/greeting.txt").read()
        self.farewell_prompt_template = open(current_dir / f"prompts/farewell.txt").read()
        self.require_clarification_prompt_template = open(current_dir / f"prompts/clarification.txt").read()
        self.follow_up_prompt_template = open(current_dir / f"prompts/follow_up.txt").read()
        self.clar_response_prompt_template = open(current_dir / f"prompts/clar_response.txt").read()
        self.rag_answer_prompt_template = open(current_dir / f"prompts/rag_answer_advanced.txt").read()
        self.no_answer_prompt_template = open(current_dir / f"prompts/no_answer_advanced.txt").read()


    async def summarise_resp(self, past_messages): 
        """
        Assumes that len(past_messages) >= 6, summarises the 4th most recent model response. Writes over past_messages 
        and returns nothing. 
        """
        print(f"len(past_messages): {len(past_messages)}")
        to_summarise = past_messages[-5]["content"] 
        print(f"TO SUMMARISE: {to_summarise}")
        response_token_limit = 1024
        messages = build_messages(
            model=self.chat_model,
            system_prompt=self.summarise_prompt_template,
            new_user_content=to_summarise,
            max_tokens=self.chat_token_limit - response_token_limit,
            fallback_to_default=True,
        )

        chat_completion_response = await self.chat_client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            temperature=0, # Setting temperature to 0 for testing
            max_tokens=response_token_limit,
            n=1,
            stream=False,
        )

        past_messages[-5]["content"] = chat_completion_response.choices[0].message.content
        print(f"SUMMARISED: {past_messages[-5]['content']}")


    async def judge_clarification_response(self, original_user_query, past_messages, response_token_limit=500): 
        """
        After clarifying user query, judges whether the user's answer is a direct response to the model's clarification question. 
        """
        messages = build_messages(
            model=self.chat_model,
            system_prompt=self.clarification_response_prompt_template,
            new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context,
            past_messages=[past_messages[-1]],
            max_tokens=self.chat_token_limit - response_token_limit,
            fallback_to_default=True
        )

        chat_completion_clar_response = await self.chat_client.chat.completions.create(
            messages=messages,
            # Azure OpenAI takes the deployment name as the model name
            model=self.chat_model,
            temperature=0, # Setting temperature to 0 for testing
            max_tokens=response_token_limit,
            n=1,
            tools=build_response_function(),
            tool_choice="required",
            response_format={"type": "json_object"}, 
            stream=False,
        )

        print(chat_completion_clar_response)
        clarification_response = extract_function_calls(chat_completion_clar_response, "is_response")
        print(f"clarification_response: {clarification_response}")

        return clarification_response


    async def classify_query(self, original_user_query, past_messages, query_response_token_limit=500): 
        """
        Takes the user query (`original_user_query`) and past messages (`past_messages`), using function calling to ask the model 
        to decide which categories the user query fits in, and returns how the model would handle the query.  
        """
        # Generate prompt that asks the model to first classify the query before answering 
        query_messages = build_messages(
            model=self.chat_model,
            system_prompt=self.query_prompt_template,
            new_user_content=original_user_query,
            past_messages=[past_messages[-1]] if past_messages else [], # Only include 1 past message to avoid long context distracting model decision-making
            max_tokens=self.chat_token_limit - query_response_token_limit,  
            fallback_to_default=True,
        )
            
        chat_completion_resp_filter: ChatCompletion = await self.chat_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            model=self.chat_model,
            temperature=0,  # Minimize creativity for search query generation
            max_tokens=100,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            tools=build_filter_function(),
            tool_choice="required", 
            response_format={"type": "json_object"}, 
        )

        
        # Extract model decision on query classification 
    
        to_greet, is_follow_up, is_reference, is_relevant, requires_clarification, is_farewell = extract_json(chat_completion_resp_filter)
        print(f"to_greet: {to_greet}, is_follow_up: {is_follow_up}, is_reference: {is_reference}, is_relevant: {is_relevant}, requires_clarification: {requires_clarification}, is_farewell: {is_farewell}")

        to_search = is_relevant and (not requires_clarification) and (not is_follow_up) # whether model uses RAG functionality 
        to_follow_up = is_follow_up and (not requires_clarification) and (not past_messages) # Whether model considers the query a follow up question that requires expanding on revious answer 
        
        print(f"to_search: {to_search}")
        print(f"to_follow_up: {to_follow_up}")
        print(f"global_storage.requires_calrification: {global_storage.requires_clarification}")


        # Inserting different system prompts for model based on specific functionalities required 
        if global_storage.requires_clarification:
            print("ENTERED GLOBAL STORAGE CLARIFICATION")
            clarification_response = await self.judge_clarification_response(original_user_query, past_messages, query_response_token_limit)
            #reset global storage until next requires_clarification occurs.
            global_storage.requires_clarification = False
        
        else:
            clarification_response = False

        return to_greet, is_farewell, requires_clarification, to_follow_up, to_search, clarification_response


    async def build_final_query(
        self, 
        original_user_query, 
        past_messages, 
        to_greet, 
        is_farewell, 
        requires_clarification, 
        to_follow_up, 
        to_search, 
        clarification_response, 
        no_answer, 
        vector_search, 
        text_search, 
        top, 
        response_token_limit=1024
    ): 
        sources_content, query_text, results = None, None, None 

        if to_greet:
            print("ENTERED GREETING")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.greeting_prompt_template,
                new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif is_farewell:
            print("ENTERED FAREWELL")
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.farewell_prompt_template,
                new_user_content = original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif to_follow_up: 
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

        elif requires_clarification:
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.require_clarification_prompt_template,
                new_user_content = original_user_query + "\n\nUser Context:\n" + global_storage.user_context,
                past_messages= past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )
            global_storage.requires_clarification = True

        elif to_search or clarification_response: 
            # Retrieve relevant documents from the database with the GPT optimized query
            vector: list[float] = []
            #query_text = None 
            if vector_search:
                if clarification_response:
                    # TODO: Create a optimised search query instead of just using the previous user query 
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
                    new_user_content = original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content, 
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


        # If the model decides the query is out of scope 
        else: 
            no_answer = True
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.no_answer_prompt_template,
                new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
           )
            
        return messages, sources_content, query_text, results


    async def display_thoughtstep(
        self, 
        chat_resp, 
        messages, 
        vector_search, 
        text_search, 
        top, 
        sources_content, 
        query_text, 
        results
    ): 
        if not sources_content: 
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
                            {"model": self.chat_model}
                        ),
                    ),
                ],
            }
        else: 
            chat_resp["choices"][0]["context"] = {
                "data_points": {"text": sources_content},
                "thoughts": [
                    ThoughtStep(
                        title="Whether RAG functionalities are used",
                        description=True,
                        props={
                            "RAG": True
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
                            {"model": self.chat_model}
                        ),
                    ),
                ],
            }


    async def classify_and_build_message_wrapper(self, original_user_query, past_messages, vector_search, text_search, top, query_response_token_limit=500, response_token_limit=1024): 
        # Classify user query before deciding how to handle the query (e.g. use RAG, follow up, etc.)
        to_greet, is_farewell, requires_clarification, to_follow_up, to_search, clarification_response = await self.classify_query(original_user_query, past_messages, query_response_token_limit)
        no_answer = None

        messages, sources_content, query_text, results = await self.build_final_query(
                                                            original_user_query, 
                                                            past_messages, 
                                                            to_greet, 
                                                            is_farewell, 
                                                            requires_clarification, 
                                                            to_follow_up, 
                                                            to_search, 
                                                            clarification_response, 
                                                            no_answer, 
                                                            vector_search, 
                                                            text_search, 
                                                            top, 
                                                            response_token_limit
                                                        )
        
        return messages, sources_content, query_text, results 


    async def run(
        self, messages: list[dict], user_info: dict[str, Any] = {}, overrides: dict[str, Any] = {}
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:

        # Generate JSON formatted string for user context information
        global_storage.user_context = str(user_info) 
        print(f"USER CONTEXT: {global_storage.user_context}")
        
        # Get overrides 
        text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        top = overrides.get("top", 3)

        original_user_query = messages[-1]["content"]
        past_messages = messages[:-1]

        # Clear cached RAG results if it builds up 
        if len(global_storage.rag_results) >= 3: 
            global_storage.rag_results = [global_storage.rag_results[-1]]

        ############################################################################################################################################################
        
        # Summarise model output after 3 rounds of conversation 
        if self.to_summarise and len(past_messages) >= 6: 
            await self.summarise_resp(past_messages) 

        ############################################################################################################################################################
        
        # Classify and build corresponding query messages for the model 

        messages, sources_content, query_text, results = await self.classify_and_build_message_wrapper(original_user_query, past_messages, vector_search, text_search, top)
        
        ############################################################################################################################################################

        # Generate answer to user query 
        response_token_limit  = 1024
        
        chat_completion_response = await self.chat_client.chat.completions.create(
                # Azure OpenAI takes the deployment name as the model name
                model=self.chat_model,
                messages=messages,
                temperature=0, # Setting temperature to 0 for testing
                max_tokens=response_token_limit,
                n=1,
                stream=False,
            )
        
        chat_resp = chat_completion_response.model_dump()

        # Include ThoughtStep data for display in frontend 
        await self.display_thoughtstep(
            chat_resp, 
            messages, 
            vector_search, 
            text_search, 
            top, 
            sources_content, 
            query_text, 
            results
        )

        return chat_resp


class QueryRewriterRAG(AdvancedRAGChat): 
    def __init__(
        self,
        *,
        searcher: PostgresSearcher,
        chat_client: AsyncOpenAI,
        chat_model: str,
        embed_model: str,
        embed_dimensions: int,
        context_window_override: int | None, # Context window size (default to 4000 if None)
        to_summarise: bool | None 
    ): 
        super().__init__(
            searcher=searcher,
            chat_client=chat_client, 
            chat_model=chat_model, 
            embed_model=embed_model, 
            embed_dimensions=embed_dimensions, 
            context_window_override=context_window_override, 
            to_summarise=to_summarise
            ) 

        # Load prompts 
        current_dir = pathlib.Path(__file__).parent
        # Classify query 
        self.query_prompt_template = open(current_dir / f"prompts/query.txt").read()
        # Summariser prompt 
        self.summarise_prompt_template = open(current_dir / f"prompts/summarize.txt").read()
        # Handling different types of queries 
        self.greeting_prompt_template = open(current_dir / f"prompts/greeting.txt").read()
        self.farewell_prompt_template = open(current_dir / f"prompts/farewell.txt").read()
        self.query_rewriter_prompt_template = open(current_dir / f"prompts/query_rewriter.txt").read()
        self.rag_answer_prompt_template = open(current_dir / f"prompts/rag_answer_advanced.txt").read()
        self.no_answer_prompt_template = open(current_dir / f"prompts/no_answer_advanced.txt").read()



    async def classify_query(self, original_user_query, past_messages, query_response_token_limit=500):
        """
        Takes the user query (`original_user_query`) and past messages (`past_messages`), using function calling to ask the model 
        to decide which categories the user query fits in, and returns how the model would handle the query.  
        """
        # Generate prompt that asks the model to first classify the query before answering 
        query_messages = build_messages(
            model=self.chat_model,
            system_prompt=self.query_prompt_template,
            new_user_content=original_user_query,
            past_messages=[past_messages[-1]] if past_messages else [], # Only include 1 past message to avoid long context distracting model decision-making
            max_tokens=self.chat_token_limit - query_response_token_limit,  
            fallback_to_default=True,
        )
            
        chat_completion_resp_filter: ChatCompletion = await self.chat_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            model=self.chat_model,
            temperature=0,  # Minimize creativity for search query generation
            max_tokens=100,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            tools=build_filter_function_query_rewriter(),
            tool_choice="required", 
            response_format={"type": "json_object"} #if self.chat_model=="llama3.1:8b-instruct-q8_0" else None, 
        )

        
        # Extract model decision on query classification 
    
        to_greet, is_relevant, is_farewell = extract_json_query_rewriter(chat_completion_resp_filter)
        print(f"to_greet: {to_greet}, is_relevant: {is_relevant}, is_farewell: {is_farewell}")

        return to_greet, is_relevant, is_farewell
    

    async def rewrite_search_query(self, original_user_query, past_messages, past_n=5, query_response_token_limit=1024): 
        """
        Takes user query and previous chat history, create a search query that takes into account past conversation history 
        """
        if not past_messages: 
            return original_user_query
        
        if len(past_messages) <= past_n: 
            query_messages = build_messages(
                model=self.chat_model,
                system_prompt=self.query_rewriter_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages, 
                max_tokens=self.chat_token_limit - query_response_token_limit,  
                fallback_to_default=True,
            )
        else: 
            query_messages = build_messages(
                model=self.chat_model,
                system_prompt=self.query_rewriter_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages[-past_n:], 
                max_tokens=self.chat_token_limit - query_response_token_limit,  
                fallback_to_default=True,
            )
        
        chat_completion_resp_query_rewriter: ChatCompletion = await self.chat_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            model=self.chat_model,
            temperature=0,  # Minimize creativity for search query generation
            max_tokens=query_response_token_limit,  
            n=1,
            response_format={"type": "json_object"}, 
        )

        rewritten_search_query = json.loads(chat_completion_resp_query_rewriter.choices[0].message.content)

        return rewritten_search_query["rewritten query"]


    async def build_final_query(self, original_user_query, past_messages, search_query, to_greet, is_farewell, is_relevant, no_answer, vector_search, text_search, top, response_token_limit=1024):
        sources_content, query_text, results = None, None, None 
        
        if to_greet:
            print("ENTERED GREETING")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.greeting_prompt_template,
                new_user_content=original_user_query, 
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif is_farewell:
            print("ENTERED FAREWELL")
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.farewell_prompt_template,
                new_user_content = original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif is_relevant: 
            # Retrieve relevant documents from the database with the GPT optimized query
            vector: list[float] = []
            query_text = None 
            if vector_search:
                print(f"Entering vector search with query text: {search_query}")
                vector = await compute_text_embedding(
                    search_query,
                    None,
                    self.embed_model 
                )

            if not text_search:
                query_text = None

            results = await self.searcher.search(query_text, vector, top)

            sources_content = [f"[{(doc.doc_id)}]: {doc.to_str_for_rag()}\n\n" for doc in results]
            content = "\n".join(sources_content)
            global_storage.rag_results.append(content)

            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.rag_answer_prompt_template,
                new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content,
                past_messages=past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )


        # If the model decides the query is out of scope 
        else: 
            no_answer = True
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.no_answer_prompt_template,
                new_user_content=original_user_query, 
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
           )
            
        return messages, sources_content, query_text, results 
    

    async def classify_and_build_message_wrapper(self, original_user_query, past_messages, vector_search, text_search, top, query_response_token_limit=500, response_token_limit=1024):
        # Rewrite search query based on chat history to capture follow up questions 
        search_query = await self.rewrite_search_query(original_user_query, past_messages, past_n=1)
        
        # Classify user query before deciding how to handle the query (e.g. use RAG)
        to_greet, is_relevant, is_farewell = await self.classify_query(search_query, past_messages, query_response_token_limit)
        no_answer = None

        messages, sources_content, query_text, results = await self.build_final_query(
                                                            original_user_query, 
                                                            past_messages, 
                                                            search_query, 
                                                            to_greet, 
                                                            is_farewell, 
                                                            is_relevant, 
                                                            no_answer, 
                                                            vector_search, 
                                                            text_search, 
                                                            top, 
                                                            response_token_limit
                                                        )
        
        return messages, sources_content, query_text, results 


class GraphRAG(QueryRewriterRAG): 
    def __init__(
        self,
        *,
        searcher: PostgresSearcher,
        chat_client: AsyncOpenAI,
        chat_model: str,
        embed_model: str,
        embed_dimensions: int,
        context_window_override: int | None, # Context window size (default to 4000 if None)
        to_summarise: bool | None 
    ): 
        super().__init__(
            searcher=searcher,
            chat_client=chat_client, 
            chat_model=chat_model, 
            embed_model=embed_model, 
            embed_dimensions=embed_dimensions, 
            context_window_override=context_window_override, 
            to_summarise=to_summarise
            ) 

        # Load prompts 
        current_dir = pathlib.Path(__file__).parent
        # Classify query 
        self.query_prompt_template = open(current_dir / f"prompts/query.txt").read()
        # Summariser prompt 
        self.summarise_prompt_template = open(current_dir / f"prompts/summarize.txt").read()
        # Handling different types of queries 
        self.greeting_prompt_template = open(current_dir / f"prompts/greeting.txt").read()
        self.farewell_prompt_template = open(current_dir / f"prompts/farewell.txt").read()
        self.query_rewriter_prompt_template = open(current_dir / f"prompts/query_rewriter.txt").read()
        self.cypher_prompt_template = open(current_dir / f"prompts/cypher.txt").read()
        self.rag_answer_prompt_template = open(current_dir / f"prompts/rag_answer_advanced.txt").read()
        self.no_answer_prompt_template = open(current_dir / f"prompts/no_answer_advanced.txt").read()
        self.cypher_relationship_prompt_template = open(current_dir / f"prompts/cypher_relationship.txt").read()
    
    def generate_cypher_query(self, original_user_query):
        """Generate Cypher query based on classification."""

        system_prompt = self.cypher_prompt_template

        messages = build_messages(
            model=self.chat_model,
            system_prompt=system_prompt,
            new_user_content=original_user_query,
            max_tokens=self.chat_token_limit - 100
        )

        # Generate the Cypher query
        chat_completion = self.chat_client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            temperature=0,
            max_tokens=100,
            n=1
        )

        # Extract the Cypher query from the response
        cypher_query = chat_completion.choices[0].message.content.strip()
        
        return cypher_query


    async def build_final_query(self, original_user_query, past_messages, search_query, to_greet, is_farewell, is_relevant, no_answer, vector_search, text_search, top, response_token_limit=1024):
        sources_content, query_text, results = None, None, None 
        
        if to_greet:
            print("ENTERED GREETING")
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.greeting_prompt_template,
                new_user_content=original_user_query, 
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif is_farewell:
            print("ENTERED FAREWELL")
            messages = build_messages(
                model = self.chat_model,
                system_prompt = self.farewell_prompt_template,
                new_user_content = original_user_query,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )

        elif is_relevant: 
            # Relevant entities 
            entities = [
                "AdministrativeCommittee",
                "AdvisoryBoardMember",
                "Alumna",
                "Alumni",
                "AlumniNetwork",
                "Alumnus",
                "App",
                "ArchitecturalPractice",
                "Author",
                "Award",
                "Blog",
                "Building",
                "Campaign",
                "Centre",
                "Charity",
                "Club",
                "Committee",
                "Company",
                "ConstructionCompany",
                "ConsultingGroup",
                "Contact",
                "ContactPerson",
                "CoResearcher",
                "Course",
                "Database",
                "Deadline",
                "Degree",
                "Department",
                "Division",
                "Document",
                "ECRNetwork",
                "EligibilityCriteria",
                "Email",
                "Episode",
                "Event",
                "Expert",
                "Facility",
                "Faculty",
                "FeaturedAlumni",
                "Fellowship",
                "Festival",
                "Form",
                "FundingSource",
                "Graduate",
                "Group",
                "Guide",
                "HeadOfSociety",
                "HostOrganisation",
                "Initiative",
                "Institution",
                "Job",
                "Library",
                "LSEExpertsDirectory",
                "LSEResearchOnline",
                "Mentor",
                "Module",
                "Network",
                "Newsletter",
                "NGO",
                "Office",
                "Opportunity",
                "Organization",
                "Partnership",
                "PensionScheme",
                "Person",
                "PhD",
                "PhDResearcher",
                "PhDStudent",
                "Podcast",
                "Policy",
                "Prize",
                "ProfessionalServicesStaff",
                "Program",
                "Programme",
                "Project",
                "ProjectBoard",
                "Publication",
                "Ranking",
                "Report",
                "Research",
                "ResearchCentre",
                "ResearchCluster",
                "Researcher",
                "ResearchGroup",
                "ResearchImpactManager",
                "ResearchPolicyTeam",
                "ResearchProject",
                "ResearchTheme",
                "Resource",
                "Reviewer",
                "Role",
                "Scholarship",
                "ScholarshipProgramme",
                "School",
                "Skill",
                "Society",
                "Speaker",
                "Startup",
                "Student",
                "StudentAmbassador",
                "StudentChair",
                "StudentVlogger",
                "Support",
                "Syllabus",
                "TeachingCentre",
                "Team",
                "Thesis",
                "University",
                "Video",
                "Visitor",
                "Vlogger",
                "Website",
                "Workshop"
            ]

            # Retrieve relevant documents from the database with the GPT optimized query
            vector: list[float] = []
            #query_text = None 
            if vector_search:
                print(f"Entering vector search with query text: {search_query}")
                vector = await compute_text_embedding(
                    original_user_query,
                    None,
                    self.embed_model 
                )

            if not text_search:
                query_text = None


            cypher_relationship = self.generate_cypher_query(original_user_query)
            print(f"CYPHER RELATIONSHIP: {cypher_relationship}")


#            cypher_response_json = json.loads(cypher_response.choices[0].message.tool_calls[0].function.arguments)
#            llm_generated_cypher_query = cypher_response_json["Cypher Query"] if cypher_response_json["Cypher Query"] in entities else None
#            print(f"LLM GENERATED CYPHER QUERY: {llm_generated_cypher_query}")

            if len(past_messages) <= 2: 
                query_embedding = await compute_text_embedding(original_user_query, None, self.embed_model)
            else:
                query_embedding = await compute_text_embedding(query_text, None, self.embed_model)


            results = await self.searcher.search(query_text, vector, top, query_embedding, original_user_query)


            # Process results and format them into a string for context
            sources_content = [f"[{(doc.doc_id)}]: {doc.to_str_for_rag()}\n\n" for doc in results]
            content = "\n".join(sources_content)
            global_storage.rag_results.append(content)

            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.rag_answer_prompt_template,
                new_user_content=original_user_query + "\n\nUser Context:\n" + global_storage.user_context + "\n\nSources:\n" + content,
                past_messages=past_messages,
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
            )


        # If the model decides the query is out of scope 
        else: 
            no_answer = True
            messages = build_messages(
                model=self.chat_model,
                system_prompt=self.no_answer_prompt_template,
                new_user_content=original_user_query, 
                max_tokens=self.chat_token_limit - response_token_limit,
                fallback_to_default=True,
           )
            
        return messages, sources_content, query_text, results 
