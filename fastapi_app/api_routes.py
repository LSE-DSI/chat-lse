import fastapi

from .api_models import ChatRequest
from .globals import global_storage
from .postgres_searcher import PostgresSearcher
from .rag_simple import SimpleRAGChat
from .logger import logger  # Ensure logger is imported here


router = fastapi.APIRouter()


@router.post("/chat")
async def chat_handler(chat_request: ChatRequest):
    ragchat = SimpleRAGChat(
        searcher=PostgresSearcher(global_storage.engine),
        chat_client=global_storage.chat_client,
        chat_model=global_storage.chat_model,
        chat_deployment=global_storage.chat_deployment,
        embed_client=global_storage.embed_client,
        embed_deployment=global_storage.embed_deployment,
        embed_model=global_storage.embed_model,
        embed_dimensions=global_storage.embed_dimensions,
        context_window_override=global_storage.context_window_override
    )

    messages = [message.model_dump() for message in chat_request.messages]
    logger.info(f"Received messages: {messages}")

    overrides = chat_request.context.get("overrides", {})
    logger.info(f"Overrides: {overrides}")

    response = await ragchat.run(messages, overrides=overrides)
    logger.info(f"Response: {response}")

    return response