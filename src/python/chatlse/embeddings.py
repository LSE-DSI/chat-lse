# This file contains util functions for embeddings
import os 
import openai
from openai_messages_token_helper import build_messages

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Filter unnecessary FutureWarning thrown by HuggingFaceEmbedding
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)



#### Environment Variables ####

# Get embedding model 
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL")
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

def summarise_and_embed_sync(
    doc: str, chat_model: str = CHAT_MODEL, chat_end_point: str = OLLAMA_ENDPOINT, embed_model: str = EMBED_MODEL, chat_model_instance = None, embed_model_instance=None
): 
    if not chat_model_instance: 
        chat_model_instance = openai.OpenAI(
            base_url=chat_end_point, 
            api_key="nokeyneeded", 
        )
    if not embed_model_instance: 
        embed_model_instance = HuggingFaceEmbedding(model_name=embed_model) 
    
    embed_summarise_prompt = open("fastapi_app/prompts/embed_summarise.txt").read()
    messages = build_messages(
            model=chat_model,
            system_prompt=embed_summarise_prompt,
            new_user_content=doc,
            fallback_to_default=True,
        )
    chat_completion_response = chat_model_instance.chat.completions.create(
        model=chat_model, 
        messages=messages, 
        temperature=0, 
        max_tokens=500, 
        n=1, 
        stream=False, 
    )

    summarised_message = chat_completion_response.choices[0].message.content

    return summarised_message 