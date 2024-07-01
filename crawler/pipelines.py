# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
import sqlite3
import logging

from sqlalchemy import text 
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session 
from itemadapter import ItemAdapter

from scrapy import signals
from scrapy.exporters import JsonLinesItemExporter

from fastapi_app.postgres_engine import create_postgres_engine_from_env_sync
from fastapi_app.postgres_models import Webpage

class ItemExporter(object):
    """ Exports the items to JSON Lines files.
    The items include boxes and pages, which are exported as inidividual JSON Lines file"""

    @classmethod
    def from_crawler(cls, crawler):
        # Initialize the pipeline
        pipeline = cls()
        # Connect signals for opening and closing spider
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        # Initialize file handlers and exporters for each item type
        self.items = ['webpage']
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
        self.exporters[item.name].export_item(item)
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

            logging.info("Creating Wepage table...")
            conn.execute(text('''
                DROP TABLE IF EXISTS webpage;
                CREATE TABLE IF NOT EXISTS webpage (
                    id SERIAL PRIMARY KEY,
                    origin_url TEXT,
                    link TEXT,
                    title TEXT, 
                    content TEXT, 
                    date_scraped TIMESTAMP
                );
            '''))
            conn.commit()

            logging.info("Database extension and tables created successfully.")

        conn.close()

    def process_item(self, item, spider):
        logging.debug("ItemToPostgresPipeline process item")
        adapter = ItemAdapter(item)
        item_name = item.name

        # with self.engine.connect() as conn:
        with Session(self.engine) as session:
            if item_name == 'pages':
                logging.debug("item_name == 'pages'")
                #FIXME: Webpage has been deprecated and replaced with Document
                model = Webpage(
                    origin_url=adapter['origin_url'],
                    link = adapter['link'],
                    title = adapter['title'],
                    content = adapter['content'],
                    date_scraped = adapter['date_scraped'],
                )
                session.add(model)
                session.commit()
                
        return item

class ItemToSQLitePipeline:
    def __init__(self):
        # Connecting to SQLite database
        self.conn = sqlite3.connect('data/dsi_crawler.db')
        self.cursor = self.conn.cursor()
        logging.info('SQLite Connection established')

        # Creating tables
        self.create_tables()

    def create_tables(self):
        try:
            # Create Webpage table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Webpage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin_url TEXT,
                    url TEXT,
                    title TEXT, 
                    html TEXT, 
                    date_scraped TEXT
                )
            ''')

            # Create Box table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Box (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin_url TEXT,
                    url TEXT, 
                    title TEXT, 
                    html TEXT, 
                    image_src TEXT, 
                    image_alt_text TEXT, 
                    date_scraped TEXT,
                    FOREIGN KEY (origin_url) REFERENCES Webpage(origin_url)
                    )
            ''')

            # Create CrawlerMetadata table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS CrawlerMetadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webpage_id INTEGER,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (webpage_id) REFERENCES Webpage(id)
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webpage_id INTEGER,
                    link TEXT,
                    FOREIGN KEY (webpage_id) REFERENCES Webpage(id)
                )
            ''')

            # Commit changes to the database
            self.conn.commit()
            logging.info('Tables created successfully')

        except Exception as e:
            logging.error(f'Error creating tables: {e}')

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_name = item.name

        if item_name == 'pages':
            # Insert data into Webpage table
            self.cursor.execute('''
                INSERT INTO Webpage (origin_url, url, title, html, date_scraped)
                VALUES (?, ?, ?, ?, ?)
            ''', (adapter['origin_url'], adapter['url'], adapter['title'],
                  adapter['html'], adapter['date_scraped']))

            # Retrieve the inserted webpage_id
            webpage_id = self.cursor.lastrowid

            # Extract links from HTML
            selector = scrapy.Selector(text=adapter['html'])
            links = selector.css('a::attr(href)').extract()

            # Insert data into Links table
            for link in links:
                self.cursor.execute('''
                    INSERT INTO Links (webpage_id, link)
                    VALUES (?, ?)
                ''', (webpage_id, link))

            # Insert crawler metadata into CrawlerMetadata table
            self.cursor.execute('''
                INSERT INTO CrawlerMetadata (webpage_id, crawled_at)
                VALUES (?, ?)
            ''', (webpage_id, datetime.now()))

        self.conn.commit()  # Commit changes to the database
        return item

    def close_spider(self, spider):
        self.conn.close()
        logging.info('SQLite Connection closed')
