import fastapi

from .api_models import ChatRequest
from .globals import global_storage
from .postgres_searcher import PostgresSearcher
from .logger import logger # Ensure logger is imported here
from .clients import create_chat_model
from dotenv import load_dotenv
import random


from .rag_advanced import AdvancedRAGChat, AdvancedRAGChatMistral, AdvancedRAGChatSummariser, AdvancedRAGChatMistralSummariser

router = fastapi.APIRouter()

BACKENDS = {
    "llama31": AdvancedRAGChat,
    "mistral": AdvancedRAGChatMistral,
    "llama31_summariser": AdvancedRAGChatSummariser,
    "mistral_summariser": AdvancedRAGChatMistralSummariser
}

CHATMODELS = {
    "llama31": "llama3.1:8b-instruct-q8_0",
    "mistral": "mistral-nemo:12b-instruct-2407-q6_K"
}

model_list = ["llama31", "mistral"]


@router.post("/chat")
async def chat_handler(chat_request: ChatRequest, backend = "llama31_summariser", chatmodel = "llama31"):
    load_dotenv(override=True)
    ChatClass = BACKENDS.get(backend)
    if not ChatClass:
        raise ValueError(f"Invalid backend: {backend}")
    
    ragchat = ChatClass(
        searcher=PostgresSearcher(global_storage.engine),
        chat_client=global_storage.chat_client,
        chat_model= await create_chat_model(CHATMODELS.get(chatmodel)),
        #chat_model=global_storage.chat_model,
        chat_deployment=global_storage.chat_deployment,
        embed_client=global_storage.embed_client,
        embed_deployment=global_storage.embed_deployment,
        embed_model=global_storage.embed_model,
        embed_dimensions=global_storage.embed_dimensions,
        context_window_override=global_storage.context_window_override
    )

    messages = [message.model_dump() for message in chat_request.messages]
    #logger.info(f"Received messages: {messages}")
    
    overrides = chat_request.context.get("overrides", {})
    #logger.info(f"Overrides: {overrides}")

    response = await ragchat.run(messages, overrides=overrides)
    #logger.info(f"Response: {response}")

    return response
