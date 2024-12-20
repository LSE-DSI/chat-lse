# This file contains util functions for the crawler
import os
import re
import hashlib
from PyPDF2 import PdfReader
from llama_index.core.node_parser import SentenceSplitter
import json
from datetime import datetime


#### Environment variables & Constants ####

# Default is 512 for GTE-large
EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE")
#  Default is 128 as experimented
EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE")


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
    """

    # Chunking and embedding chunks
    splitter = SentenceSplitter(
        chunk_size=EMBED_CHUNK_SIZE if EMBED_CHUNK_SIZE else 512,
        chunk_overlap=EMBED_OVERLAP_SIZE if EMBED_OVERLAP_SIZE else 128
    )

    sentence_chunks = splitter.split_text(text)
    output_list = []
    for chunk_id, chunk_text in enumerate(sentence_chunks):
        id = f"{doc_id}_{chunk_id}"
        #embedding = compute_text_embedding_sync(chunk_text, model_instance=MODEL_INSTANCE)
        output_list.append([
            id,
            doc_id,
            chunk_id,
            type,
            url,
            title,
            chunk_text,
            date_scraped
            #embedding
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
