# This file contains util functions for the crawler
import os
import re
import hashlib
from PyPDF2 import PdfReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import json
from datetime import datetime


from chatlse.embeddings import compute_text_embedding_sync
from chatlse.multihead_attention import MultiHeadAttention
from chatlse.cross_chunk_attention import ShiftedCrossChunkAttention

import torch



#### Environment variables & Constants ####

# Default is 512 for GTE-large
EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE")
#  Default is 128 as experimented
EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE")
# Get embedding model
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")
# Get embedding dimension 
EMBED_DIM = os.getenv("EMBED_DIM")

if not EMBED_MODEL:
    # Use default model if not provided
    EMBED_MODEL = "thenlper/gte-large"

MODEL_INSTANCE = HuggingFaceEmbedding(EMBED_MODEL)

# Initialize the cross-chunk attention mechanism
MULTIHEAD_ATTENTION_INSTANCE = MultiHeadAttention(EMBED_DIM if EMBED_DIM else 1024) # Set default embed_dim to 1024
CROSS_CHUNK_ATTENTION_INSTANCE = ShiftedCrossChunkAttention(EMBED_DIM if EMBED_DIM else 1024)


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
    #  Supported file types: [".pdf", ".doc", ".docx", ".ppt", ".pptx"]

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


def generate_json_entry(text, type, url, title, date_scraped, doc_id):
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

    # Chunking the document
    splitter = SentenceSplitter(
        chunk_size=EMBED_CHUNK_SIZE if EMBED_CHUNK_SIZE else 512,
        chunk_overlap=0
    )

    sentence_chunks = splitter.split_text(text)
    chunk_embeddings = []

    # Compute initial embeddings for each chunk
    for chunk_text in sentence_chunks:
        embedding = compute_text_embedding_sync(chunk_text, model_instance=MODEL_INSTANCE)
        chunk_embeddings.append(embedding)

    # Convert to tensor and reshape for the attention mechanism
    chunk_embeddings = torch.tensor(chunk_embeddings)
    num_chunks, embed_dim = chunk_embeddings.size()
    chunk_embeddings = chunk_embeddings.view(num_chunks, 1, embed_dim)  # Reshape to (num_chunks, chunk_size=1, embed_dim)

    # Apply -chunk attention
    attended_embeddings = CROSS_CHUNK_ATTENTION_INSTANCE(chunk_embeddings) # Change to MULTIHEAD_ATTENTION_INSTANCE if want to test no shiftinbg
    attended_embeddings = attended_embeddings.view(num_chunks, embed_dim).tolist()  # Reshape back to (num_chunks, embed_dim)

    # Generate output list with attended embeddings
    output_list = []
    for chunk_id, attended_embedding in enumerate(attended_embeddings):
        id = f"{doc_id}_{chunk_id}"
        output_list.append([
            id, 
            doc_id,
            chunk_id,
            type,
            url,
            title,
            sentence_chunks[chunk_id],
            date_scraped,
            attended_embedding
        ])

    return output_list


def generate_list_ingested_data(file_path, idx, type, url, title, date_scraped):
    """
    This functions takes the metadata about the data ingested into the database and returns a json file 
    which stores the metadata about which pages and files have been ingested. The json entry is appended 
    to the `ingested_data.json` file.
    """
    json_entry = {"id": idx,
                  "type": type,
                  "url": url,
                  "title": title,
                  "date_scraped": date_scraped.isoformat() if isinstance(date_scraped, datetime) else date_scraped}

    # for a given title, if the id is the same, then delete the existing entry and insert the new one
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                data = json.loads(line)
                if data["title"] == title and data["id"] == idx:
                    lines.remove(line)
                    break
        with open(file_path, "a") as file:
            file.write(json.dumps(json_entry))
            file.write("\n")
    else:
        with open(file_path, "a") as file:
            file.write(json.dumps(json_entry))
            file.write("\n")

    print(f"Data ingested: {url}")