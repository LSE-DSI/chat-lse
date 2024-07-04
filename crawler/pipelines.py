# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
import logging
import os
import re


from scrapy import signals
from datetime import datetime
from itemadapter import ItemAdapter
from scrapy.exporters import JsonLinesItemExporter
from bs4 import BeautifulSoup

from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from fastapi_app.postgres_engine import create_postgres_engine_from_env_sync
from fastapi_app.postgres_models import Doc
from fastapi_app.embeddings import compute_text_embedding

from llama_index.core.node_parser import SentenceSplitter

from utils.crawler_utils import generate_json_entry_for_files

# Default is 512 for GTE-large
EMBED_CHUNK_SIZE = os.getenv("EMBED_CHUNK_SIZE")
#  Default is 128 as experimented
EMBED_OVERLAP_SIZE = os.getenv("EMBED_OVERLAP_SIZE")


class ItemExporter(object):
    """ Exports the items to JSON Lines files.
    The items include boxes and pages, which are exported as individual JSON Lines files"""

    @classmethod
    def from_crawler(cls, crawler):
        # Initialize the pipeline
        pipeline = cls()
        # Connect signals for opening and closing spider
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.items = ['file_metadata'] # CHANGE THIS TO ["file_metadata", "webpage"] DEPENDS ON WHICH TABLE YOU WANT TO POPULATE
        self.files = {}
        self.exporters = {}
        for item in self.items:
            # Open a file for each item type
            self.files[item] = open(f'data/{item}.jl', 'wb')
            # Initialize a JsonLinesItemExporter for each item type
            self.exporters[item] = JsonLinesItemExporter(self.files[item])
            # Start exporting for each item type
            self.exporters[item].start_exporting()

    def spider_closed(self, spider):
        # Close file handlers and exporters when spider is closed
        for item in self.items:
            self.exporters[item].finish_exporting()
            self.files[item].close()

    def process_item(self, item, spider):
        # Export each item to the corresponding file
        self.exporters[item.type].export_item(item)
        return item


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

            logging.info("Creating wepage table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS webpage (
                    doc_id TEXT,
                    url TEXT,
                    title TEXT,
                    content TEXT,
                    date_scraped TIMESTAMP
                );
            '''))

            logging.info("Creating file table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS file_metadata (
                    url TEXT,
                    title TEXT,
                    file_path TEXT,
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
                except Exception as e: # Keeping this here for debugging 
                    print("Transaction failed:", e) 
                    conn.rollback()
            elif item_type == "file_metadata": 
                url = adapter["url"]
                title = adapter["title"]
                file_path = adapter["file_path"]
                date_scraped = adapter["date_scraped"]
                for doc_id, chunk_id, type, url, title, content, date_scraped, embedding in generate_json_entry_for_files(file_path, url, title, date_scraped): 
                    try: 
                        conn.execute(text('''
                            INSERT INTO lse_doc (doc_id, chunk_id, type, url, title, content, date_scraped, embedding)
                            VALUES (:doc_id, :chunk_id, :type, url, :title, :content, :date_scraped, :embedding)
                        '''), {
                            'doc_id': doc_id,
                            'chunk_id': chunk_id,
                            'type': type, 
                            'url': url, 
                            "title": title, 
                            "content": content, 
                            "date_scraped": date_scraped, 
                            "embedding": embedding
                        })
                        conn.commit()
                    except Exception as e: # Keeping this for debugging
                        print("Transaction failed:", e)
                        conn.rollback()

        return item

    def process_page(self, conn, adapter):
        result = conn.execute(
            text('SELECT url, doc_id FROM webpage WHERE url = :url'),
            {'url': adapter['url']}
        ).fetchone()

        if result:
            url, previous_hash = result
            if previous_hash == adapter['doc_id']:
                print(f"Page not modified since last scraped:", adapter["url"])
                return
            else:
                conn.execute(text('DELETE FROM webpage WHERE url = :url'), {'url': url})

        conn.execute(text('''
            INSERT INTO webpage (doc_id, url, title, content, date_scraped)
            VALUES (:doc_id, :url, :title, :content, :date_scraped)
        '''), {
            'doc_id': adapter['doc_id'],
            'url': adapter['url'],
            'title': adapter['title'],
            'content': adapter['content'],
            'date_scraped': adapter['date_scraped'],
        })

        # only export item to webpage.jl in the case of reprocessing to postgresdb
        #self.process_item(adapter, 'webpage')

        logging.info(f'Page processed and stored in PostgreSQL:', adapter["url"])

    # temorarily deleted the process_box method (adapt from the pages method if needed again)

