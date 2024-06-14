import logging
import os

import openai

logger = logging.getLogger("ragapp")


async def create_openai_chat_client():
    OPENAI_API_HOST = os.getenv("OPENAI_API_HOST")
    if OPENAI_API_HOST == "ollama":
        logger.info("Authenticating to OpenAI using Ollama...")
        openai_chat_client = openai.AsyncOpenAI(
            base_url=os.getenv("OLLAMA_ENDPOINT"),
            api_key="nokeyneeded",
        )
        openai_chat_model = os.getenv("OLLAMA_CHAT_MODEL")
    else:
        logger.info("Authenticating to OpenAI using OpenAI.com API key...")
        openai_chat_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAICOM_KEY"))
        openai_chat_model = os.getenv("OPENAICOM_CHAT_MODEL")

    return openai_chat_client, openai_chat_model


async def create_openai_embed_client():

    OPENAI_EMBED_HOST = os.getenv("OPENAI_EMBED_HOST")
    
    if OPENAI_EMBED_HOST == "ollama": 
        logger.info("Authenticating to OpenAI using Ollama...") 
        openai_embed_model = os.getenv("OLLAMA_EMBED_MODEL")
    return openai_embed_model
