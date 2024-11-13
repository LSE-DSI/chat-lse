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



# Create a table for document summary 
with engine.connect() as conn:
    logging.info("Creating doc_summary table...")
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS doc_summary (
            doc_id TEXT PRIMARY KEY, 
            content TEXT,
            summary TEXT
        );
    '''))

    conn.commit()
    logging.info("Table doc_summary created successfully.")


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

    if not df_results.empty: 
        logging.info("Collating full document text...")
        df_docs = df_results.sort_values("id").groupby("doc_id").agg({"content": lambda x: "".join(x)}).reset_index()

        total = len(df_results)
        count = 0 
        for row in df_results.itertuples(index=False, name="Row"):
            print(f"Embedding chunk {count}/{total}")
            count += 1
            id, doc_id, title, chunk_content = row

            logging.info("Summarising document contents...")
            # Check if the document already exists in the doc_summary
            summary = conn.execute(
                text('SELECT summary FROM doc_summary WHERE doc_id = :doc_id'),
                {'doc_id': doc_id}
            ).fetchone()

            if not summary: 
                # Retrieve full document and summarise its content 
                doc_content = df_docs.loc[df_docs["doc_id"]==doc_id, "content"].iloc[0]
                summary = summarise_and_embed_sync(doc_content, chat_model_instance=CHAT_MODEL_INSTANCE, embed_model_instance=EMBED_MODEL_INSTANCE)
                # Insert the document and summary into the table
                conn.execute(text('''
                            INSERT INTO doc_summary (doc_id, content, summary)
                            VALUES (:doc_id, :content, :summary)
                        '''), {
                            "doc_id": doc_id,
                            "content": doc_content,
                            "summary": summary
                        })
                conn.commit()
            else: 
                summary = summary[0]

            logging.info("Embedding contextual chunks...")
            contextual_chunk = f"title: {title}\nsummary: {summary}\ncontent: {chunk_content}"
            print(f"CONTEXTUAL CHUNK: {contextual_chunk}")
            embedding = compute_text_embedding_sync(contextual_chunk, model_instance=EMBED_MODEL_INSTANCE)
            print("######################################################################")
            
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
