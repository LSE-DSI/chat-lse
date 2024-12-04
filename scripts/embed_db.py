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

logger = logging.getLogger("ragapp")

load_dotenv(override=True)

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")

CHAT_MODEL_INSTANCE = openai.OpenAI(
            base_url=OLLAMA_ENDPOINT, 
            api_key="nokeyneeded", 
        )
EMBED_MODEL_INSTANCE = HuggingFaceEmbedding(EMBED_MODEL)

engine = create_postgres_engine_from_env_sync()
#logging.debug(engine)

logging.basicConfig(level=logging.INFO)


### SET EMBEDDING TYPE HERE 
embedding_type = os.getenv("EMBEDDING_TYPE")
allowed_embedding_types = ["simple_embeddings", "title_embeddings", "context_embeddings"]
if embedding_type not in allowed_embedding_types: 
    raise ValueError('embedding_type must be in ["simple_embeddings", "title_embeddings", "context_embeddings"]')


# Create a table for document summary 
with engine.connect() as conn:
    logger.info("Creating doc_summary table...")
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS doc_summary (
            doc_id TEXT PRIMARY KEY, 
            content TEXT,
            summary TEXT
        );
    '''))

    conn.commit()
    logger.info("Table doc_summary created successfully.")


# Check if the 'embeddings' column exists
insp = sqlalchemy.inspect(engine)
columns = [col['name'] for col in insp.get_columns('lse_doc')]

for e_type in allowed_embedding_types: 
    if e_type not in columns:
        with engine.connect() as conn:
            logger.info("Enabling the pgvector extension for Postgres...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            logger.info(f"Adding '{e_type}' column to lse_doc table...")
            conn.execute(text(f'''
                ALTER TABLE lse_doc ADD COLUMN {e_type} VECTOR(1024);
            '''))

            logger.info(f"'{e_type}' column added successfully.")
            conn.commit() 
    else:
        logger.info(f"'{e_type}' column already exists, no need to add it.")


# Embed documents where embeddings is NULL
with engine.connect() as conn:
    logger.info(f"Fetching data for {embedding_type} calculation...")
    query = f'''
        SELECT id, doc_id, title, content 
        FROM lse_doc 
        WHERE {embedding_type} IS NULL
    '''

    df_results = pd.read_sql_query(query, conn) 

    if not df_results.empty: 
        logger.info("Collating full document text...")
        if embedding_type == "context_embeddings": 
            df_docs = df_results.sort_values("id").groupby("doc_id").agg({"content": lambda x: " ".join(x)}).reset_index()

        total = len(df_results)
        count = 0 
        for row in df_results.itertuples(index=False, name="Row"):
            logger.info(f"Embedding chunk {count}/{total}")
            count += 1
            id, doc_id, title, chunk_content = row

            if embedding_type == "context_embeddings": 
                logger.info("Summarising document contents...")
                # Check if the document already exists in the doc_summary
                summary = conn.execute(
                    text('SELECT summary FROM doc_summary WHERE doc_id = :doc_id'),
                    {'doc_id': doc_id}
                ).fetchone()

                if not summary: 
                    # Retrieve full document and summarise its content 
                    doc_content = df_docs.loc[df_docs["doc_id"]==doc_id, "content"].iloc[0]
                    doc = f"{{title: {title}, content: {doc_content}}}"
                    
                    # Manually handle some problems with summary format that can't be solved with prompt engineering
                    if "CourseGuidesProgrammeRegs" in title: 
                        summary = f"Course guides and programme regulations for 20{title[25:30]}."
                    elif "SchoolRegs" in title: 
                        summary = f"School Regulations for 20{title[10:15]}"
                    else: 
                        summary = summarise_and_embed_sync(doc, chat_model_instance=CHAT_MODEL_INSTANCE, embed_model_instance=EMBED_MODEL_INSTANCE)
                    
                    summary = summary.split(".")[0] + "." # Manually handle some problems with summary format that can't be solved with prompt engineering

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
                
                logger.info(f"TITLE: {title} \n\nSUMMARY: {summary}")

                contextual_chunk = f"title: {title}\nsummary: {summary}\ncontent: {chunk_content}"
            elif embedding_type == "title_embeddings": 
                contextual_chunk = f"title: {title}\ncontent: {chunk_content}"
            else: 
                contextual_chunk = chunk_content
            
            logger.info("Embedding chunks...")
            embedding = compute_text_embedding_sync(contextual_chunk, model_instance=EMBED_MODEL_INSTANCE)
            logger.info("######################################################################")
            
            # Update the table with the calculated embedding
            conn.execute(text(f'''
                UPDATE lse_doc SET {embedding_type} = :{embedding_type} WHERE id = :id
            '''), {embedding_type: embedding, 'id': id})

            conn.commit()

            logger.info(f"Embedding calculated and updated for id: {id}")
    else:
        logger.info("No rows with NULL embeddings found. No updates needed.")

    logger.info("Embeddings calculated and updated successfully.")


engine.dispose()
logger.info('PostgreSQL Connection closed')
