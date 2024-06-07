import logging
import os

import openai

logger = logging.getLogger("ragapp")


async def create_openai_chat_client():
    OPENAI_CHAT_HOST = os.getenv("OPENAI_CHAT_HOST")
    if OPENAI_CHAT_HOST == "ollama":
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

    # OPENAI_EMBED_HOST = os.getenv("OPENAI_EMBED_HOST")
    
    openai_embed_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAICOM_KEY"))
    openai_embed_model = os.getenv("OPENAICOM_EMBED_MODEL")
    openai_embed_dimensions = os.getenv("OPENAICOM_EMBED_DIMENSIONS")
    return openai_embed_client, openai_embed_model, openai_embed_dimensions
