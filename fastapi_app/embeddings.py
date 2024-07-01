from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Filter unnecessary FutureWarning thrown by HuggingFaceEmbedding
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

DEFAULT_EMBED_MODEL = "thenlper/gte-large"

async def compute_text_embedding(
    q: str, embed_model: str = DEFAULT_EMBED_MODEL
):
    model = HuggingFaceEmbedding(model_name=embed_model) 
    embedding = model.get_text_embedding(q)

    return embedding
