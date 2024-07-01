# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
import sqlite3
import logging

from scrapy import signals
from datetime import datetime
from itemadapter import ItemAdapter
from crawler.settings import SQLITE_DB_PATH
from scrapy.exporters import JsonLinesItemExporter


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
        self.items = ['pages', 'boxes']
        self.files = {}
        self.exporters = {}

        for item in self.items:
            # Open a file for each item type
            self.files[item] = open(
                f'data/{item}.jl', 'wb')
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


class ItemToSQLitePipeline:
    def __init__(self):
        # Connecting to SQLite database
        self.conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
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
                    date_scraped TEXT,
                    current_hash TEXT,
                    UNIQUE(url, current_hash)
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
                    current_hash TEXT,
                    FOREIGN KEY (origin_url) REFERENCES Webpage(origin_url),
                    UNIQUE(url, current_hash)
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

            # Create indexes for efficient lookups
            self.cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_webpage_url ON Webpage(url);')
            self.cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_box_url ON Box(url);')

            self.conn.commit()
            logging.info('Tables and indexes created successfully')

        except Exception as e:
            logging.error(f'Error creating tables: {e}')

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_name = item.name

        if item_name == 'pages':
            self.process_page(adapter)
        elif item_name == 'boxes':
            self.process_box(adapter)

        self.conn.commit()
        return item

    def process_page(self, adapter):
        # Check if URL already exists in the database for pages
        self.cursor.execute('''
            SELECT id, current_hash FROM Webpage WHERE url = ?
        ''', (adapter['url'],))
        result = self.cursor.fetchone()

        if result:
            webpage_id, previous_hash = result
            if previous_hash == adapter['current_hash']:
                logging.info(f'Page not modified since last scraped: {adapter["url"]}')
                return

            else:
                # Delete old entry
                self.cursor.execute(
                    'DELETE FROM Webpage WHERE id = ?', (webpage_id,))
                self.cursor.execute(
                    'DELETE FROM Links WHERE webpage_id = ?', (webpage_id,))
                self.cursor.execute(
                    'DELETE FROM CrawlerMetadata WHERE webpage_id = ?', (webpage_id,))

        # If the page has not been modified, the function will return and not carry out the following operations

        self.cursor.execute('''
            INSERT INTO Webpage (origin_url, url, title, html, date_scraped, current_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (adapter['origin_url'], adapter['url'], adapter['title'],
              adapter['html'], adapter['date_scraped'], adapter['current_hash']))

        webpage_id = self.cursor.lastrowid

        selector = scrapy.Selector(text=adapter['html'])
        links = selector.css('a::attr(href)').extract()

        for link in links:
            self.cursor.execute('''
                INSERT INTO Links (webpage_id, link)
                VALUES (?, ?)
            ''', (webpage_id, link))

        self.cursor.execute('''
            INSERT INTO CrawlerMetadata (webpage_id, crawled_at)
            VALUES (?, ?)
        ''', (webpage_id, datetime.now()))

        logging.info(f'Page processed and stored in SQLite: {adapter["url"]}')

    def process_box(self, adapter):
        # Check if URL already exists in the database for boxes
        self.cursor.execute('''
            SELECT id, current_hash FROM Box WHERE url = ?
        ''', (adapter['url'],))
        result = self.cursor.fetchone()

        if result:
            box_id, previous_hash = result
            if previous_hash == adapter['current_hash']:
                logging.info(f'Box not modified since last scraped: {adapter["url"]}')
                return
            else:
                # Delete old entry
                self.cursor.execute('DELETE FROM Box WHERE id = ?', (box_id,))
                self.cursor.execute(
                    'DELETE FROM CrawlerMetadata WHERE webpage_id = (SELECT id FROM Webpage WHERE url = ?)', (adapter['origin_url'],))

        self.cursor.execute('''
            INSERT INTO Box (origin_url, url, title, html, image_src, image_alt_text, date_scraped, current_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (adapter['origin_url'], adapter['url'], adapter['title'], adapter['html'],
              adapter['image_src'], adapter['image_alt_text'], adapter['date_scraped'], adapter['current_hash']))

        self.cursor.execute('''
            INSERT INTO CrawlerMetadata (webpage_id, crawled_at)
            VALUES ((SELECT id FROM Webpage WHERE url = ?), ?)
        ''', (adapter['origin_url'], datetime.now()))

        logging.info(f'Box processed and stored in SQLite: {adapter["url"]}')

    def close_spider(self, spider):
        self.conn.close()
        logging.info('SQLite Connection closed')
