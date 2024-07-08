# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging
import os

from itemadapter import ItemAdapter

from sqlalchemy import text
from dotenv import load_dotenv

from fastapi_app.postgres_engine import create_postgres_engine_from_env_sync

from utils.crawler_utils import parse_doc, generate_json_entry_for_files, generate_json_entry_for_html
# Default is 512 for GTE-large
EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE")
#  Default is 128 as experimented
EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE")


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
#            conn.execute(text('''
#                CREATE TABLE IF NOT EXISTS lse_doc (
#                    id TEXT,
#                    doc_id TEXT,
#                    chunk_id TEXT,
#                    type TEXT,
#                    url TEXT,
#                    title TEXT,
#                    content TEXT,
#                    date_scraped TIMESTAMP,
#                    embedding VECTOR(1024)
#                );
#            '''))
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS lse_doc ( 
                    doc_id TEXT,
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
            if item_type == "webpage":
                try:
                    self.process_page(conn, adapter)
                    conn.commit()
                except Exception as e:  # Keeping this here for debugging
                    print("Transaction failed:", e)
                    conn.rollback()

            elif item_type == "file_metadata":
                try:
                    self.process_file(conn, adapter)
                    conn.commit()
                except Exception as e:  # Keeping this for debugging
                    print("Transaction failed:", e)
                    conn.rollback()

        return item

    def process_page(self, conn, adapter):
        result = conn.execute(
            text('SELECT url, doc_id FROM lse_doc WHERE url = :url'),
            {'url': adapter['url']}
        ).fetchone()

        doc_id = adapter["doc_id"]
        url = adapter["url"]
        title = adapter["title"]
        content = adapter["content"]
        date_scraped = adapter["date_scraped"]

        if result:
            _, previous_hash = result
            if previous_hash == doc_id:
                print(
                    f"Skipping insertion. Page not modified since last scraped:", adapter["url"])
                return
            else:
                conn.execute(
                    text('DELETE FROM lse_doc WHERE url = :url'), {'url': url})

#        output_list = generate_json_entry_for_html(content, url, title, date_scraped, doc_id)
                conn.execute(text('''
                    INSERT INTO lse_doc (doc_id, type, url, title, content, date_scraped,)
                    VALUES (:doc_id, :type, :url, :title, :content, :date_scraped)
                '''), {
                    "doc_id": doc_id,
                    "type": type,
                    "url": url,
                    "title": title,
                    "content": content,
                    "date_scraped": date_scraped
                })
#        for idx, doc_id, chunk_id, type, url, title, content, date_scraped, embedding in output_list:
#            conn.execute(text('''
#                INSERT INTO lse_doc (id, doc_id, chunk_id, type, url, title, content, date_scraped, embedding)
#                VALUES (:id, :doc_id, :chunk_id, :type, :url, :title, :content, :date_scraped, :embedding)
#            '''), {
#                "id": idx,
#                "doc_id": doc_id,
#                "chunk_id": chunk_id,
#                "type": type,
#                "url": url,
#                "title": title,
#                "content": content,
#                "date_scraped": date_scraped,
#                "embedding": embedding
#            })

        logging.info(f'Page processed and stored in PostgreSQL {
                     adapter["url"]}')

    def process_file(self, conn, adapter):
        result = conn.execute(
            text('SELECT url, doc_id FROM lse_doc WHERE url = :url'),
            {'url': adapter['url']}
        ).fetchone()

        url = adapter["url"]
        title = adapter["title"]
        file_path = adapter["file_path"]
        date_scraped = adapter["date_scraped"]
        content, doc_id, type = parse_doc(file_path)

        if result:
            _, previous_hash = result
            if previous_hash == doc_id:
                print(f"Skipping insertion. File not modified since last scraped:", url)
                return
            else:
                conn.execute(
                    text('DELETE FROM lse_doc WHERE url = :url'), {'url': url})

                conn.execute(text('''
                    INSERT INTO lse_doc (doc_id,type, url, title, content, date_scraped)
                    VALUES (:doc_id,:type, :url, :title, :content, :date_scraped)
                '''), {
                    "doc_id": doc_id,
                    "type": type,
                    "url": url,
                    "title": title,
                    "content": content,
                    "date_scraped": date_scraped
                })

#        output_list = generate_json_entry_for_files(content, type, url, title, date_scraped, doc_id)
#        for idx, doc_id, chunk_id, type, url, title, content, date_scraped, embedding in output_list:
#            conn.execute(text('''
#                INSERT INTO lse_doc (id, doc_id, chunk_id, type, url, title, content, date_scraped, embedding)
#                VALUES (:id, :doc_id, :chunk_id, :type, :url, :title, :content, :date_scraped, :embedding)
#            '''), {
#                "id": idx,
#                "doc_id": doc_id,
#                "chunk_id": chunk_id,
#                "type": type,
#                "url": url,
#                "title": title,
#                "content": content,
#                "date_scraped": date_scraped,
#                "embedding": embedding
#            })

        logging.info(f'File processed and stored in PostgreSQL: {
                     adapter["url"]}')
