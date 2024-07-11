# This file contains util functions for the crawler
import os
import re
import asyncio
import hashlib
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from chatlse.embeddings import compute_text_embedding_sync



#### Environment variables & Constants ####

# Default is 512 for GTE-large
EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE")
# Default is 128 as experimented
EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE")
# Get embedding model 
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")

if not EMBED_MODEL:
    # Use default model if not provided
    EMBED_MODEL = "thenlper/gte-large"

MODEL_INSTANCE = HuggingFaceEmbedding(EMBED_MODEL)



#### Util Functions ####

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


def parse_doc(file_path): 
    # This function parses a file and returns its cleaned texts as python string
    # Supported file types: [".pdf", ".doc", ".docx", ".ppt", ".pptx"] 
    
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

    doc_id = hashlib.md5(cleaned_content.encode("utf-8")).hexdigest()
    type = file_path.split(".")[-1]

    return cleaned_content, doc_id, type


def embed_json(text, type, url, title, date_scraped, doc_id):
    load_dotenv(override=True)

    # Chunking and embedding chunks
    splitter = SentenceSplitter(
        chunk_size=EMBED_CHUNK_SIZE if EMBED_CHUNK_SIZE else 512,
        chunk_overlap=EMBED_OVERLAP_SIZE if EMBED_OVERLAP_SIZE else 128
    )

    sentence_chunks = splitter.split_text(text)
    output_list = []
    for chunk_id, chunk_text in enumerate(sentence_chunks):
        id = f"{doc_id}_{chunk_id}"
        embedding = compute_text_embedding_sync(chunk_text, model_instance=MODEL_INSTANCE)
        output_list.append([
            id, 
            doc_id,
            chunk_id,
            type,
            url,
            title,
            chunk_text,
            date_scraped,
            embedding
        ])
    
    return output_list


def generate_json_entry_for_files(text, type, url, title, date_scraped, doc_id):
    """
    This function takes the metadata returned by the `file_downloader`, chunks and embeds
    the files and returns a json entry for input into postgres database. 

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

    return embed_json(text, type, url, title, date_scraped, doc_id)


def generate_json_entry_for_html(text, url, title, date_scraped, doc_id):
    """
    This function takes the metadata returned by the lse_crawler, parses, chunks and embeds
    the html and returns a list entry for input into postgres database. 

    Output: 
        - doc_id: hashed html content 
        - chunk_id: id of the text chunk 
        - type: type of the file 
        - url: url of the webpage 
        - title: title of the webpage 
        - content: chunked content of the html 
        - date_scraped: datetime of when the data is scraped 
        - embedding: embedded chunk 
    """

    # Parse the html content
    soup = BeautifulSoup(text, 'html.parser')
    cleaned_content = clean_text(soup.get_text())

    return embed_json(cleaned_content, "webpage", url, title, date_scraped, doc_id)
