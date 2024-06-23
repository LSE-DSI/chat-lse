import logging
import os

import openai

logger = logging.getLogger("ragapp")


async def create_chat_client():
    logger.info("Authenticating to OpenAI using Ollama...") 
    chat_client = openai.AsyncOpenAI(
        base_url=os.getenv("OLLAMA_ENDPOINT"),
        api_key="nokeyneeded",
    )
    chat_model = os.getenv("OLLAMA_CHAT_MODEL")
    
    return chat_client, chat_model


async def create_embed_client():
    logger.info("Authenticating to OpenAI using Ollama...") 
    embed_model = os.getenv("OLLAMA_EMBED_MODEL")
    return embed_model
