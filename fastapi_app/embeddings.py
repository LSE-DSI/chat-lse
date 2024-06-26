from llama_index.embeddings.huggingface import HuggingFaceEmbedding

DEFAULT_EMBED_MODEL = "thenlper/gte-large"

async def compute_text_embedding(
    q: str, embed_model: str = DEFAULT_EMBED_MODEL
):
    model = HuggingFaceEmbedding(model_name=embed_model) 
    embedding = model.get_text_embedding(q)

    return embedding
