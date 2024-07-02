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

import PyPDF2
import re
import tqdm as tqdm
import json 

import pandas as pd 

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

    DOCS_FOLDER = './notebooks/experiments/sample-docs/'

    def read_pdf(file_path=DOCS_FOLDER):
        # Initialize a variable to hold all the text
        all_text = ""
        
        # Open the PDF file
        with open(file_path, "rb") as file:
            # Initialize a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Iterate through each page in the PDF
            for page in pdf_reader.pages:
                # Extract text from the page
                text = page.extract_text()
                if text:
                    all_text += text  # Append the extracted text to all_text

        return all_text

    def clean_text(text):
        # Replace all newline characters with a single space
        cleaned_text = re.sub(r'\n', '', text)
        # Replace two or more spaces with a single space
        cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
        # Replace a space followed by a period with just a period
        cleaned_text = re.sub(r' \.', '.', cleaned_text)
        # Replace a space followed by a comma with just a comma
        cleaned_text = re.sub(r' ,', ',', cleaned_text)
        return cleaned_text
    
    path_all_pdfs = [file for file in os.listdir(DOCS_FOLDER)]
    docs = {filename: read_pdf(os.path.join(DOCS_FOLDER, filename)) for filename in tqdm(path_all_pdfs)}
    print(f"Read {len(docs)} documents")

    cleaned_docs = {filename: clean_text(doc) for filename, doc in tqdm(docs.items())}

    # STEP 4 -- Generate the embeddings
    
    def generate_chunk_entry(embedding_model, chunk_name, chunktext):
        try:
            embedding = embedding_model.get_text_embedding(chunktext)
            return {
                "chunkname": chunk_name,
                "chunktext": chunktext,
                "embedding": embedding,  
            }
        except Exception as e:
            print(f"Error computing embedding for chunk {chunk_name}: {e}")
            return None
        
    def generate_json_entry(embed_model, splitter, filetype, filename, description, cleaned_text, url, **kwargs):
        try:
            # Split the description into chunks according to the sentence splitter
            if isinstance(splitter, SentenceSplitter):
                sentence_chunks = splitter.split_text(cleaned_text)
            else:
                raise ValueError(f"Unsupported splitter type: {type(splitter)}")
            chunks = []
            chunk_id = 1
            for chunk in tqdm(sentence_chunks, desc=f"Embedding document chunks '{filename}'"):
                chunk_entry = generate_chunk_entry(embed_model, f"{filename} - Part {chunk_id}", chunk)
                if chunk_entry:
                    chunks.append(chunk_entry)
                    chunk_id += 1

            return {
                "filetype": filetype,
                "filename": filename,
                "description": description,
                "cleaned_text": cleaned_text,
                "url": url,
                "chunks": chunks,
            }
        except Exception as e:
            print(f"Failed to compute embedding for {filename}: {e}")
            return None
        
    df_docs = pd.Series(cleaned_docs).to_frame("cleaned_text")
    df_docs.index.name = "filename"

    # Manually annotate docs 
    df_docs.loc["ConfidentialityPolicy.pdf", "description"] = "Immigration Advice Confidentiality Policy"
    df_docs.loc["Formatting-and-binding-your-thesis-2021-22.pdf", "description"] = "Formatting and binding your thesis"
    df_docs.loc["LSE-2030-booklet.pdf", "description"] = "LSE 2030 Strategy"
    df_docs.loc["MSc-Mark-Frame.pdf", "description"] = "MSc Mark Frame"
    df_docs.loc["bsc-handbook-21.22.pdf", "description"] = "BSc Economics Handbook 2021/22"
    df_docs.loc["UG-Student-Handbook-Department-of-International-History-2023-24 (1).pdf", "description"] = "UG History Department Handbook 2023/24"
    df_docs.loc["Exam-Procedures-for-Candidates.pdf", "description"] = "Exam Procedures for Candidates"
    df_docs.loc["Spring-Exam-Timetable-2024-Final.pdf", "description"] = "Spring Exam Timetable 2024"
    df_docs.loc["InterruptionPolicy.pdf", "description"] = "Interruption of Studies Policy"
    df_docs.loc["Appeals-Regulations.pdf", "description"] = "Academic Appeals Regulations for Taught Programmes"
    df_docs.loc["In-Course-Financial-Support.pdf", "description"] = "In-Course Financial Support - Application form and guidance notes"
    df_docs.loc["BA-BSc-Three-Year-scheme-for-students-from-2018.19.pdf", "description"] = "BA/BSc Three-Year Scheme for students from 2018/19"
    df_docs.loc["comPro.pdf", "description"] = "Student Complaints Procedure"
    df_docs.loc["Student-Guidance-Deferral.pdf", "description"] = "Student Guidance on Deferral"

    # Add URL of the document
    df_docs.loc["ConfidentialityPolicy.pdf", "url"] = "https://info.lse.ac.uk/current-students/immigration-advice/assets/documents/Info-Sheets/ConfidentialityPolicy.pdf"
    df_docs.loc["Formatting-and-binding-your-thesis-2021-22.pdf", "url"] = "https://info.lse.ac.uk/current-students/phd-academy/assets/documents/Formatting-and-binding-your-thesis-2021-22.pdf"
    df_docs.loc["LSE-2030-booklet.pdf", "url"] = "https://www.lse.ac.uk/2030/assets/pdf/LSE-2030-booklet.pdf"
    df_docs.loc["MSc-Mark-Frame.pdf", "url"] = "https://www.lse.ac.uk/sociology/assets/documents/study/Assessment-and-Feedback/MSc-Mark-Frame.pdf"
    df_docs.loc["bsc-handbook-21.22.pdf", "url"] = "https://www.lse.ac.uk/economics/Assets/Documents/undergraduate-study/bsc-handbook-21.22.pdf"
    df_docs.loc["UG-Student-Handbook-Department-of-International-History-2023-24 (1).pdf", "url"] = "https://www.lse.ac.uk/International-History/Assets/Documents/student-handbooks/2023-24/UG-Student-Handbook-Department-of-International-History-2023-24.pdf"
    df_docs.loc["Exam-Procedures-for-Candidates.pdf", "url"] = "https://info.lse.ac.uk/current-students/services/assets/documents/Exam-Procedures-for-Candidates.pdf"
    df_docs.loc["Spring-Exam-Timetable-2024-Final.pdf", "url"] = "https://info.lse.ac.uk/current-students/services/assets/documents/Spring-Exam-Timetable-2024-Final.pdf"
    df_docs.loc["InterruptionPolicy.pdf", "url"] = "https://info.lse.ac.uk/Staff/Divisions/Academic-Registrars-Division/Teaching-Quality-Assurance-and-Review-Office/Assets/Documents/Calendar/InterruptionPolicy.pdf"
    df_docs.loc["Appeals-Regulations.pdf", "url"] = "https://info.lse.ac.uk/current-students/services/assets/documents/Appeals-Regulations-August-2018.pdf"
    df_docs.loc["In-Course-Financial-Support.pdf", "url"] = "https://info.lse.ac.uk/current-students/financial-support/assets/documents/In-Course-Financial-Support.pdf"
    df_docs.loc["BA-BSc-Three-Year-scheme-for-students-from-2018.19.pdf", "url"] = "https://info.lse.ac.uk/staff/divisions/academic-registrars-division/Teaching-Quality-Assurance-and-Review-Office/Assets/Documents/Calendar/BA-BSc-Three-Year-scheme-for-students-from-2018.19.pdf"
    df_docs.loc["comPro.pdf", "url"] = "https://info.lse.ac.uk/staff/Services/Policies-and-procedures/Assets/Documents/comPro.pdf?from_serp=1"
    df_docs.loc["Student-Guidance-Deferral.pdf", "url"] = "https://info.lse.ac.uk/current-students/services/assets/documents/Student-Guidance-Deferral.pdf"

    df_docs["filetype"] = "pdf"

    json_entries = [
        generate_json_entry(embed_model, splitter, **doc)
        for _, doc in df_docs.reset_index().iterrows()]


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
