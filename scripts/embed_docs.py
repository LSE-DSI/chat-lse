import os
import glob
import asyncio
import logging
import argparse

import numpy as np

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
from sqlalchemy import Table, Column, Integer, String, LargeBinary, MetaData
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_app.clients import create_embed_client
from llama_index.core.node_parser import SentenceSplitter 
from fastapi_app.postgres_engine import create_postgres_engine_from_env

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define the metadata
metadata = MetaData()

# Define the embeddings table
embeddings_table = Table(
    'embeddings', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('filename', String),
    Column('embedding', LargeBinary)
)

async def setup_database():
    engine = await create_postgres_engine_from_env()
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    return engine

def create_embeddings(text):
    embedding = model.encode(text)
    return np.array(embedding).astype(np.float32).tobytes()

async def embed_docs(directory, session):

    # https://stackoverflow.com/a/13297537/843365
    listing = glob.glob(os.path.join(directory, "*.pdf"))

    if not listing:
        raise ValueError(f"No PDF files found in {directory}")

    for filename in listing:
        file_path = os.path.join(directory, filename)
        # FIXME: This function no longer exists. Use utils/pdf_reader.py instead.
        text = await extract_text_from_pdf(file_path)
        embedding = create_embeddings(text)
        
        # Insert into the database
        # FIXME: Use the approach in fastapi_app/setup_postgres_seeddata.py instead of the following
        insert_statement = embeddings_table.insert().values(filename=filename, embedding=embedding)
        await session.execute(insert_statement)
        await session.commit()
        logging.info(f"Processed and stored embedding for {filename}")

async def main():

    # STEP 1 -- Parse command line arguments
    argparser_str = "Embed PDFs and store embeddings in Postgres DB"
    parser = argparse.ArgumentParser(description=argparser_str)
    dir_help = "Directory containing PDF files to embed"
    parser.add_argument("--dir", type=str, required=True, help=dir_help)
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        error_msg = f"The directory {args.dir} does not exist or is not a directory."
        raise ValueError(error_msg)

    # STEP 2 -- Load environment variables and setup SentenceSplitter
    load_dotenv(override=True)

    EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE") # Default is 512 for GTE-large
    EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE") # Default is 128 as experimented
    
    embed_model = await create_embed_client()
    splitter = SentenceSplitter(
        chunk_size = EMBED_CHUNK_SIZE if EMBED_CHUNK_SIZE else 512, 
        chunk_overlap=EMBED_OVERLAP_SIZE if EMBED_OVERLAP_SIZE else 128
        )

    # STEP 3 -- Read the PDFs in the directory
    # TODO: Read the PDFs in the directory and embed them (adapt from notebooks/NB04)

    # STEP 4 -- Generate the embeddings
    # TODO: Generate the embeddings for the text chunks (adapt from notebooks/NB04)

    # STEP 5 -- Store the embeddings in the database
    # TODO: Adopt from fastapi_app/setup_postgres_seeddata.py

    engine = await create_postgres_engine_from_env()
    async_session = sessionmaker(
        bind=engine, 
        expire_on_commit=False,
        class_=AsyncSession
    )

    async with async_session() as session:
        await embed_docs(args.dir, session)

    logging.info("Embedding process completed.")

if __name__ == "__main__":
    asyncio.run(main())
