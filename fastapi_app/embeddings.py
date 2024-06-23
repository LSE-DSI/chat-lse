from llama_index.embeddings.huggingface import HuggingFaceEmbedding

async def compute_text_embedding(
    q: str, embed_model: str 
):
    model = HuggingFaceEmbedding(model_name=embed_model) 
    embedding = model.get_text_embedding(q)

    return embedding
