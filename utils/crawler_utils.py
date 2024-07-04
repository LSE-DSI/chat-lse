# This file contains util functions for the crawler 
import os 
import re
import hashlib
from  PyPDF2 import PdfReader
from dotenv import load_dotenv
from llama_index.core.node_parser import SentenceSplitter
from fastapi_app.clients import create_embed_client
from fastapi_app.embeddings import compute_text_embedding

def read_pdf(file_path):
    # Initialize a variable to hold all the text
    all_text = ""
    
    # Open the PDF file
    with open(file_path, "rb") as file:
        # Initialize a PDF reader object
        pdf_reader = PdfReader(file)
        
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


async def embed_text(text, file_path, url, title, date_scraped, doc_id): 
    load_dotenv(override=True)

    EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE") # Default is 512 for GTE-large
    EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE") # Default is 128 as experimented

    # Chunking and embedding chunks 
    embed_model = await create_embed_client() 
    splitter = SentenceSplitter(
        chunk_size = EMBED_CHUNK_SIZE if EMBED_CHUNK_SIZE else 512, 
        chunk_overlap=EMBED_OVERLAP_SIZE if EMBED_OVERLAP_SIZE else 128
        )
    
    sentence_chunks = splitter.split_text(text) 
    for chunk_id, chunk_text in enumerate(sentence_chunks): 
        embedding = await compute_text_embedding(chunk_text, embed_model)
        yield [
            doc_id, 
            chunk_id, 
            file_path.split(".")[-1], 
            url, 
            title, 
            chunk_text, 
            date_scraped, 
            embedding 
        ]


async def generate_json_entry_for_files(file_path, url, title, date_scraped): 
    """
    This function takes the metadata returned by the `file_downloader`, chunks and embeds
    the files and returns a json entry for input into postgres database. 

    Supported file types: [".pdf", ".doc", ".docx", ".ppt", ".pptx"] 

    Output: 
        - doc_id: hashed chunk content 
        - chunk_id: id of the file chunk 
        - type: type of the file 
        - url: url of the file 
        - title: title of the file 
        - content: chunked content of the file 
        - date_scraped: datetime of when the data is scraped 
        - embedding: embedded chunk 
    """
    # Parse file for different file types 
    if file_path.endswith(".pdf"): 
        content = read_pdf(file_path) 
        cleaned_content = clean_text(content) 
    elif file_path.endswith(".doc"): 
        pass
    elif file_path.endswith(".docx"): 
        pass
    elif file_path.endswith(".ppt"): 
        pass
    elif file_path.endswith(".pptx"): 
        pass

    # Generate hash for content 
    doc_id = hashlib.md5(cleaned_content.encode("utf-8")).hexdigest() 

    await embed_text(cleaned_content, file_path, url, title, date_scraped, doc_id)
