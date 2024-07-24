import logging
import os

import openai
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

logger = logging.getLogger("ragapp")


async def create_chat_client():
    logger.info("Authenticating to OpenAI using Ollama...") 
    chat_client = openai.AsyncOpenAI(
        base_url=os.getenv("OLLAMA_ENDPOINT"),
        api_key="nokeyneeded",
    )
    chat_model = os.getenv("OLLAMA_CHAT_MODEL")
    
    return chat_client, chat_model


DEFAULT_EMBED_MODEL = "thenlper/gte-large"


async def create_embed_client():
    logger.info("Authenticating to OpenAI using Ollama...") 
    embed_model = HuggingFaceEmbedding(model_name=os.getenv("OLLAMA_EMBED_MODEL", DEFAULT_EMBED_MODEL))
    return embed_model
