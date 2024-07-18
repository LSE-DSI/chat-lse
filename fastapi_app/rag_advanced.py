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

from .api_models import ThoughtStep
from chatlse.embeddings import compute_text_embedding
from .postgres_searcher import PostgresSearcher


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
        self.rag_answer_prompt_template = open(current_dir / "prompts/rag_answer_advanced.txt").read()
        self.no_answer_prompt_template = open(current_dir / "prompts/no_answer_advanced.txt").read()
        self.summarise_prompt_template = open(current_dir / "prompts/summarize.txt").read()

    async def run(
        self, messages: list[dict], overrides: dict[str, Any] = {}
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:

        text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        top = overrides.get("top", 3)

        original_user_query = messages[-1]["content"]
        past_messages = messages[:-1]
        


        ##############################################################################
        # Summarising last chat model output 
        if past_messages: 
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

            past_messages[-1]["content"] = chat_completion_response.choices[0].message.content



        ##############################################################################
        # Generate the prompt that asks the model to decide whether it should answer the use query (use rag)
        query_response_token_limit = 500
        query_messages = build_messages(
            model=self.chat_model,
            system_prompt=self.query_prompt_template,
            new_user_content=original_user_query,
            past_messages=past_messages,
            max_tokens=self.chat_token_limit - query_response_token_limit,  # TODO: count functions
            fallback_to_default=True,
        )

        chat_completion: ChatCompletion = await self.chat_client.chat.completions.create(
            messages=query_messages,  # type: ignore
            # Azure OpenAI takes the deployment name as the model name
            model=self.chat_deployment if self.chat_deployment else self.chat_model,
            temperature=0.0,  # Minimize creativity for search query generation
            max_tokens=20,  # Setting too low risks malformed JSON, setting too high may affect performance
            n=1,
            #tools=build_function(),
            #tool_choice={"type": "function", "function": {"name": "if_search_database"}},
        )

        # Deciding whether to invoke RAG functionalities 
        resp = chat_completion.choices[0].message.content
        #print(resp)
        to_search = resp == "True"



        ##############################################################################
        # If the model decides to use the database
        if to_search: 
            # Retrieve relevant documents from the database with the GPT optimized query
            vector: list[float] = []
            query_text = None 
            if vector_search:
                vector = await compute_text_embedding(
                    original_user_query,
                    None,
                    self.embed_model 
                )
            if not text_search:
                query_text = None

            results = await self.searcher.search(query_text, vector, top)

            sources_content = [f"[{(doc.doc_id)}]:{doc.to_str_for_rag()}\n\n" for doc in results]
            content = "\n".join(sources_content)

            # Generate a contextual and content specific answer using the search results and chat history
            response_token_limit = 1024
            messages = build_messages(
                model=self.chat_model,
                system_prompt=overrides.get("prompt_template") or self.rag_answer_prompt_template,
                new_user_content=original_user_query + "\n\nSources:\n" + content,
                past_messages=past_messages,
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

            chat_resp = chat_completion_response.model_dump()
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

        # If the model decides the query does not require RAG 
        else: 
            # Generate a contextual and content specific answer using the chat history only 
            response_token_limit = 1024
            messages = build_messages(
                model=self.chat_model,
                system_prompt=overrides.get("prompt_template") or self.no_answer_prompt_template,
                new_user_content=original_user_query,
                past_messages=past_messages,
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

            chat_resp = chat_completion_response.model_dump()
            chat_resp["choices"][0]["context"] = {
                "data_points": {"text": None},
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

