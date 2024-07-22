import os
import openai
import logging
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

logger = logging.getLogger("ragapp")

DEFAULT_EMBED_MODEL = "thenlper/gte-large"


async def create_chat_client():
    logger.info("Creating Ollama Chat Client") 
    chat_client = openai.AsyncOpenAI(
        base_url=os.getenv("OLLAMA_ENDPOINT"),
        api_key="nokeyneeded",
    )
    chat_model = os.getenv("OLLAMA_CHAT_MODEL")
    
    return chat_client, chat_model


async def create_embed_client():
    logger.info("Initialising Embedding model") 
    embed_model = HuggingFaceEmbedding(model_name=os.getenv("OLLAMA_EMBED_MODEL", DEFAULT_EMBED_MODEL))
    return embed_model
