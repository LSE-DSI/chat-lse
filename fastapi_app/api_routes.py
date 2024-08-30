import random
import fastapi

from .api_models import ChatRequest
from .globals import global_storage
from .postgres_neo4j_searcher import PostgresSearcher
from .logger import logger, handle_new_message

from .rag_advanced import AdvancedRAGChat
import os

router = fastapi.APIRouter()

neo4j_uri = os.getenv("NEO4J_URL")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")

@router.post("/chat")
async def chat_handler(chat_request: ChatRequest):
    ragchat = AdvancedRAGChat(
        searcher=PostgresSearcher(neo4j_uri = neo4j_uri, neo4j_user = neo4j_user, neo4j_password = neo4j_password, engine = global_storage.engine),
        chat_client=global_storage.chat_client,
        chat_model=global_storage.chat_model,
        embed_model=global_storage.embed_model,
        embed_dimensions=global_storage.embed_dimensions,
        context_window_override=global_storage.context_window_override, 
        to_summarise=global_storage.to_summarise
    )

    messages = [message.model_dump() for message in chat_request.messages]
    for msg in messages:
        handle_new_message(msg['content'])  # Ensure each message is logged to history

    logger.info(f"Received messages: {messages[0]['content']}")
    
    user_info = chat_request.context.get("userInfo", {})
    logger.info(f"User Information: {user_info}")

    overrides = chat_request.context.get("overrides", {})
    logger.info(f"Overrides: {overrides}")

    response = await ragchat.run(messages, user_info=user_info, overrides=overrides)
    logger.info(f"Response: {response['choices'][0]['message']['content']}")

    return response
