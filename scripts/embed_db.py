import os
import openai
import logging
import pandas as pd 
from dotenv import load_dotenv

import sqlalchemy
from sqlalchemy import text

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from chatlse.embeddings import compute_text_embedding_sync, summarise_and_embed_sync
from chatlse.postgres_engine import create_postgres_engine_from_env_sync


load_dotenv(override=True)

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")

CHAT_MODEL_INSTANCE = openai.OpenAI(
            base_url=OLLAMA_ENDPOINT, 
            api_key="nokeyneeded", 
        )
EMBED_MODEL_INSTANCE = HuggingFaceEmbedding(EMBED_MODEL)

engine = create_postgres_engine_from_env_sync()
logging.debug(engine)

logging.basicConfig(level=logging.INFO)



# Check if the 'embedding' column exists
insp = sqlalchemy.inspect(engine)
columns = [col['name'] for col in insp.get_columns('lse_doc')]

if 'embedding' not in columns:
    with engine.connect() as conn:
        logging.info("Adding 'embedding' column to lse_doc table...")
        conn.execute(text('''
            ALTER TABLE lse_doc ADD COLUMN embedding VECTOR(1024);
        '''))

        logging.info("'embedding' column added successfully.")
        conn.commit() 
else:
    logging.info("'embedding' column already exists, no need to add it.")


# Embed documents where embedding is NULL
with engine.connect() as conn:
    logging.info("Fetching data for embedding calculation...")
    query = '''
        SELECT id, doc_id, title, content 
        FROM lse_doc 
        WHERE embedding IS NULL
    '''

    df_results = pd.read_sql_query(query, conn) 

    if df_results: 
        logging.info("Summarising documents...") 
        df_docs = df_results.sort_values("id").groupby("doc_id").agg({"content": lambda x: "".join(x)}).reset_index()
        df_docs["summarised_docs"] = df_docs["content"].apply(lambda doc: summarise_and_embed_sync(doc, chat_model_instant=CHAT_MODEL_INSTANCE, embed_model_instance=EMBED_MODEL_INSTANCE))

        logging.info("Calculating embeddings...")
        for row in df_results.itertuples(index=False, name="Row"):
            id, doc_id, title, content = row
            summary = df_docs.loc["doc_id"==doc_id, "summarised_docs"]
            contextual_chunk = f"{{title: {title}, summary: {summary}, content: {content}}}"
            embedding = compute_text_embedding_sync(contextual_chunk, model_instance=EMBED_MODEL_INSTANCE)
            
            # Update the table with the calculated embedding
            conn.execute(text('''
                UPDATE lse_doc SET embedding = :embedding WHERE id = :id
            '''), {'embedding': embedding, 'id': id})

            conn.commit()

            logging.info(f"Embedding calculated and updated for id: {id}")
    else:
        logging.info("No rows with NULL embeddings found. No updates needed.")

    logging.info("Embeddings calculated and updated successfully.")

    

conn.close()
engine.dispose()
logging.info('PostgreSQL Connection closed')
