import asyncio
import json
import os

from dotenv import load_dotenv
from tqdm import tqdm 
from embeddings import compute_text_embedding  # Ensure correct imports
from clients import create_embed_client  # Import OpenAI client creation function
from llama_index.core.node_parser import SentenceSplitter 

async def generate_json_entry(embed_model, id, doc_id, chunk_id, filetype, filename, description, text, url):
    embedding = await compute_text_embedding(text, embed_model)
    return {
        "id": id, 
        "doc_id": doc_id, 
        "chunk_id": chunk_id, 
        "type": filetype,
        "name": filename,
        "description": description, 
        "content": text, 
        "url": url, 
        "embedding": embedding, 
    }

async def main():
    load_dotenv(override=True)

    EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE") # Default is 512 for GTE-large
    EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE") # Default is 128 as experimented

    id = 0
    doc_id = 0
    
    embed_model = await create_embed_client()
    splitter = SentenceSplitter(
        chunk_size = EMBED_CHUNK_SIZE if EMBED_CHUNK_SIZE else 512, 
        chunk_overlap=EMBED_OVERLAP_SIZE if EMBED_OVERLAP_SIZE else 128
        )

    # Get sample data 
    documents = []
    with open("data/sample_lse_docs.jsonl", "r") as file: 
        for line in file: 
            # parse each line as a json file
            documents.append(json.loads(line).values())

    json_data = []
    for filename, text, description, url, filetype in tqdm(documents, unit="file"): 
        sentence_chunks = splitter.split_text(text)
        for chunk_id, chunk_text in enumerate(sentence_chunks): 
            json_entry = await generate_json_entry(embed_model, id, doc_id, chunk_id, filetype, filename, description, chunk_text, url) 
            
            if json_entry:
                json_data.append(json_entry)
            else:
                print(f"Failed to create JSON entry for chunk {chunk_id} of {filename}")
            
            id += 1
        doc_id += 1

    json_file_path = f"data/seed_lse_data.jsonl"
    try:
        with open(json_file_path, "w") as f:
            json.dump(json_data, f, indent=4)
        print(f"JSON file created successfully at {json_file_path}")
    except Exception as e:
        print(f"Failed to write JSON file: {e}")
 
if __name__ == "__main__":
    print("WARNING: This script will take a long time to run, if the sample documents are the same, you can skip this script and use the existing seed data.\nExisting data is available in our Sharepoint Folder, see `instructions/SETUP.md` for more detail.\n")
    to_proceed = input("Are you sure you want to proceed [yes/no]: ")

    if to_proceed.lower() in ["yes", "y"]: 
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Reuse the existing running loop
            loop.create_task(main())
        else:
            # No running event loop, safe to use asyncio.run
            asyncio.run(main())
    else: 
        print("Run aborted.")