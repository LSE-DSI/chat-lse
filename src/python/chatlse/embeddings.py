# This file contains util functions for embeddings
import os 
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Filter unnecessary FutureWarning thrown by HuggingFaceEmbedding
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)



#### Environment Variables ####

# Get embedding model 
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")



#### Util Functions #### 

async def compute_text_embedding(
    q: str, embed_model: str = EMBED_MODEL, model_instance=None
):
    if not model_instance:
        model_instance = HuggingFaceEmbedding(model_name=embed_model) 
    embedding = model_instance.get_text_embedding(q)

    return embedding


def compute_text_embedding_sync(
    q: str, embed_model: str = EMBED_MODEL, model_instance=None
):
    if not model_instance:
        model_instance = HuggingFaceEmbedding(model_name=embed_model) 
    embedding = model_instance.get_text_embedding(q)

    return embedding