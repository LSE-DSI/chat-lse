# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging

from itemadapter import ItemAdapter

from sqlalchemy import text
from dotenv import load_dotenv
import jsonlines
import os
from pathlib import Path

from chatlse.postgres_engine import create_postgres_engine_from_env_sync
from chatlse.crawler import parse_doc, generate_json_entry, generate_list_ingested_data


#defining the current directory that is two levels up from the current file
CURRENT_DIR = Path(__file__).resolve().parents[1]


class ItemToPostgresPipeline:
    def __init__(self):
        logging.debug("Init ItemToPostgresPipeline")
        load_dotenv(override=True)
        self.engine = None

    def open_spider(self, spider):
        logging.debug("ItemToPostgresPipeline open spider")
        self.engine = create_postgres_engine_from_env_sync()
        logging.debug(self.engine.url)
        self.create_tables(self.engine)
        logging.info('PostgreSQL Connection established')

    def close_spider(self, spider):
        logging.debug("ItemToPostgresPipeline close spider")
        self.engine.dispose()
        logging.info('PostgreSQL Connection closed')
    
    def write_error_log(self, file_path, url):
        existing_entries = []
        try:
            with jsonlines.open(file_path, 'r') as reader:
                for entry in reader:
                    existing_entries.append(entry)
        except FileNotFoundError:
            pass

        new_entry = url
        if new_entry not in existing_entries:
            with jsonlines.open(file_path, 'a') as writer:
                writer.write(new_entry)
        
        return new_entry

    def create_tables(self, engine):
        logging.debug("ItemToPostgresPipeline create tables")
        logging.debug(engine)
        with engine.connect() as conn:
            logging.info("Enabling the pgvector extension for Postgres...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            logging.info("Creating lse_doc table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS lse_doc (
                    doc_id TEXT PRIMARY KEY,
                    type TEXT, 
                    url TEXT,
                    title TEXT,
                    content TEXT,
                    date_scraped TIMESTAMP
                );
            '''))

            conn.commit()
            logging.info("Database extension and tables created successfully.")

        conn.close()

    def process_item(self, item, spider):
        logging.info("ItemToPostgresPipeline process item")
        adapter = ItemAdapter(item)
        item_type = item.type

        with self.engine.connect() as conn:
            if item_type == "error_301":
                try:
                    filename = "data/error_301.jsonl"
                    self.process_error(conn, adapter, filename)
                except Exception as e:  # Keeping this here for debugging
                    print("Transaction failed:", e)
                    conn.rollback()

            elif item_type == "error_all":
                try:
                    filename = "data/error_all.jsonl"
                    self.process_error(conn, adapter, filename)
                except Exception as e:  # Keeping this here for debugging
                    print("Transaction failed:", e)
                    conn.rollback()
            else:
                try:
                    # Get data for each item
                    url = adapter["url"]
                    title = adapter["title"]
                    date_scraped = adapter["date_scraped"]

                    # Get specific fields from webpages 
                    if item_type == "webpage": 
                        content = adapter["content"]
                        doc_id = adapter["doc_id"]
                        type = "webpage"

                    elif item_type == "webpage_su":
                        content = adapter["content"]
                        doc_id = adapter["doc_id"]
                        type = "webpage_su"
                        
                    # Get specific fields from PDF files 
                    elif item_type == "file_metadata":
                        file_path = os.path.join(CURRENT_DIR, adapter["file_path"])
                        try:
                            content, doc_id, type = parse_doc(file_path)
                        except Exception as e:
                            print(f"Error parsing document: {e}")
                            self.write_error_log("data/error_downloads.jsonl", url)
                            return


                    # Check if the url already exists in the database
                    result = conn.execute(
                        text('SELECT url, doc_id FROM lse_doc WHERE url = :url'),
                        {'url': url}
                    ).fetchone()

                    # If url exists, check if it has changed since last scrape
                    if result:
                        _, previous_hash = result
                        # Skipping insertion and return if document has not changed
                        if previous_hash == doc_id:
                            print(f"Skipping insertion. Page not modified since last scraped:", url)
                            return
                        # Delete old insertions if document has changed
                        else:
                            print(f"Page modified since last scraped. Deleting previous data for:", url)
                            conn.execute(text('DELETE FROM lse_doc WHERE url = :url'), {'url': url})

                    # Insert document into the database (if document not exist or if it has changed)
                    output_list = generate_json_entry(content, type, url, title, date_scraped, doc_id)
                    for doc_id, type, url, title, content, date_scraped in output_list:
                        conn.execute(text('''
                            INSERT INTO lse_doc (doc_id, type, url, title, content, date_scraped)
                            VALUES (:doc_id, :type, :url, :title, :content, :date_scraped)
                        '''), {
                            "doc_id": doc_id,
                            "type": type,
                            "url": url,
                            "title": title,
                            "content": content,
                            "date_scraped": date_scraped
                        })

                    logging.info(f'Item processed and stored in PostgreSQL {adapter["url"]}')

                    generate_list_ingested_data("data/ingested_data.json", doc_id, type, url, title, date_scraped)

                    logging.info(f'File saved to list of ingested data: {adapter["url"]}')

                    conn.commit()

                except Exception as e:  # Keeping this here for debugging
                    print("Transaction failed:", e)
                    conn.rollback()

        return item

    def process_error(self, conn, adapter, filename):
        print('ENTERED ERROR')
        print(f"Adapter contents: {adapter}")  # Debug statement
        if "url" in adapter and "status" in adapter:
            url = adapter["url"]
            status = adapter["status"]

            json_data = {
                "url": url,
                "status": status
            }

            try:
                with jsonlines.open(filename, 'a') as writer:
                    # Write the entire dictionary at once
                    writer.write(json_data)
                print(f"JSON lines successfully written to {filename}")
            except Exception as e:
                print(f"An error occurred while writing JSON lines to file: {e}")
        else:
            print("url or status not found in adapter")


