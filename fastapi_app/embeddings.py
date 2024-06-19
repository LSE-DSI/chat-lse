from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = "thenlper/gte-large"

async def compute_text_embedding(
    q: str, embed_model: str 
):
    model = HuggingFaceEmbedding(model_name="thenlper/gte-large") 
    embedding = model.get_text_embedding(q)

    return embedding
