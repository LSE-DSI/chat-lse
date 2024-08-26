
import logging


from sqlalchemy import text
from sqlalchemy.engine import reflection
from dotenv import load_dotenv
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import os

from chatlse.postgres_engine import create_postgres_engine_from_env_sync

from chatlse.embeddings import compute_text_embedding_sync

load_dotenv(override=True)

EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")

if not EMBED_MODEL:
    # Use default model if not provided
    EMBED_MODEL = "thenlper/gte-large"

MODEL_INSTANCE = HuggingFaceEmbedding(EMBED_MODEL)

MODEL_INSTANCE = HuggingFaceEmbedding(EMBED_MODEL)


engine = create_postgres_engine_from_env_sync()

logging.debug(engine)

insp = reflection.Inspector.from_engine(engine)

# Check if the 'embedding' column exists
columns = [col['name'] for col in insp.get_columns('lse_doc')]

if 'embedding' not in columns:
    with engine.connect() as conn:
        logging.info("Adding 'embedding' column to lse_doc table...")
        conn.execute(text('''
            ALTER TABLE lse_doc ADD COLUMN embedding VECTOR(1024);
        '''))
        logging.info("'embedding' column added successfully.")
else:
    logging.info("'embedding' column already exists, no need to add it.")


# Embed documents where embedding is NULL
with engine.connect() as conn:
    logging.info("Fetching data for embedding calculation...")
    result = conn.execute(text('''
        SELECT id, content 
        FROM lse_doc 
        WHERE embedding IS NULL
    ''')).fetchall()

    if result: 
        logging.info("Calculating embeddings...")
        for row in result:
            id, content = row
            embedding = compute_text_embedding_sync(content, model_instance=MODEL_INSTANCE)
            
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
