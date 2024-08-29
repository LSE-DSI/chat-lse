import fastapi

from .api_models import ChatRequest
from .globals import global_storage
from .postgres_neo4j_searcher import PostgresSearcher
from .logger import logger # Ensure logger is imported here

from .rag_simple import SimpleRAGChat
from .rag_advanced import AdvancedRAGChat
import os

router = fastapi.APIRouter()

neo4j_uri = os.getenv("NEO4J_URL")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")

@router.post("/chat")
async def chat_handler(chat_request: ChatRequest):
    ragchat = AdvancedRAGChat(
        searcher=PostgresSearcher(neo4j_uri, neo4j_user, neo4j_password, global_storage.engine),
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
