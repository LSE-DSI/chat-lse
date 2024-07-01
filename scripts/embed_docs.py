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
        text = await extract_text_from_pdf(file_path)
        embedding = create_embeddings(text)
        
        # Insert into the database
        insert_statement = embeddings_table.insert().values(filename=filename, embedding=embedding)
        await session.execute(insert_statement)
        await session.commit()
        logging.info(f"Processed and stored embedding for {filename}")

async def main():
    parser = argparse.ArgumentParser(description="Embed PDFs and store embeddings in Postgres DB")
    parser.add_argument('--dir', type=str, required=True, help='Directory containing PDF files')
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        raise ValueError(f"The directory {args.dir} does not exist or is not a directory.")
    
    load_dotenv(override=True)

    engine = await setup_database()
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
