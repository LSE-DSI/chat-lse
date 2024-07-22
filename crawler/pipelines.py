# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging

from itemadapter import ItemAdapter

from sqlalchemy import text
from dotenv import load_dotenv

from chatlse.postgres_engine import create_postgres_engine_from_env_sync

from chatlse.crawler import parse_doc, generate_json_entry, generate_list_ingested_data



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

    def create_tables(self, engine):
        logging.debug("ItemToPostgresPipeline create tables")
        logging.debug(engine)
        with engine.connect() as conn:
            logging.info("Enabling the pgvector extension for Postgres...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            logging.info("Creating lse_doc table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS lse_doc (
                    id TEXT PRIMARY KEY, 
                    doc_id TEXT,
                    chunk_id TEXT, 
                    type TEXT, 
                    url TEXT,
                    title TEXT,
                    content TEXT,
                    date_scraped TIMESTAMP, 
                    embedding VECTOR(1024) 
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
                # Get specific fields from PDF files 
                elif item_type == "file_metadata": 
                    file_path = adapter["file_path"]
                    content, doc_id, type = parse_doc(file_path)

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
                        conn.execute(
                            text('DELETE FROM lse_doc WHERE url = :url'), {'url': url})

                # Insert document into the database (if document not exist or if it has changed)
                output_list = generate_json_entry(content, type, url, title, date_scraped, doc_id)
                for idx, doc_id, chunk_id, type, url, title, content, date_scraped, embedding in output_list:
                    conn.execute(text('''
                        INSERT INTO lse_doc (id, doc_id, chunk_id, type, url, title, content, date_scraped, embedding)
                        VALUES (:id, :doc_id, :chunk_id, :type, :url, :title, :content, :date_scraped, :embedding)
                    '''), {
                        "id": idx, 
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "type": type,
                        "url": url,
                        "title": title,
                        "content": content,
                        "date_scraped": date_scraped,
                        "embedding": embedding
                    })

                logging.info(f'Item processed and stored in PostgreSQL {adapter["url"]}')

                generate_list_ingested_data("data/ingested_data.json", idx, type, url, title, date_scraped)

                logging.info(f'File saved to list of ingested data: {adapter["url"]}')
                
                conn.commit()

            except Exception as e:  # Keeping this here for debugging
                print("Transaction failed:", e)
                conn.rollback()

        return item
