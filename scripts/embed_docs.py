import os
import argparse
import pdfplumber
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import Table, Column, Integer, String, LargeBinary, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
import warnings

from .postgres_engine import create_postgres_engine_from_env

# Load environment variables
load_dotenv()

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

async def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def create_embeddings(text):
    embedding = model.encode(text)
    return np.array(embedding).astype(np.float32).tobytes()

async def embed_docs(directory, session):
    for filename in os.listdir(directory):
        if not filename.endswith('.pdf'):
            warnings.warn(f"Skipping non-PDF file: {filename}")
            continue
        
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
    import asyncio
    asyncio.run(main())
