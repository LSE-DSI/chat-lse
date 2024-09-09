# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PagesScraperItem(scrapy.Item):
    """
    Represents an item scraped from the DSI pages.

    Attributes:
        type: The name of item, i.e page 
        doc_id (scrapy.Field): The hash of the HTML content of the page 
        origin_url (scrapy.Field): The original URL of the page.
        url (scrapy.Field): The URL of the page.
        title (scrapy.Field): The title of the page.
        content (scrapy.Field): The HTML content of the page.
        date_scraped (scrapy.Field): The date when the page was scraped.
    """
    type = 'webpage'
    doc_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    date_scraped = scrapy.Field()

class SUPagesScraperItem(scrapy.Item):
    """
    Represents an item scraped from the LSESU pages.

    Attributes:
        type: The name of item, i.e page 
        doc_id (scrapy.Field): The hash of the HTML content of the page 
        origin_url (scrapy.Field): The original URL of the page.
        url (scrapy.Field): The URL of the page.
        title (scrapy.Field): The title of the page.
        content (scrapy.Field): The HTML content of the page.
        date_scraped (scrapy.Field): The date when the page was scraped.
    """
    type = 'webpage_su'
    doc_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    date_scraped = scrapy.Field()


class FilesScraperItem(scrapy.Item):
    """
    Represents a file saved from the LSE links 

    Attributes: 
        type: The name of item, i.e. file 
        url (scrapy.Field): The URL of the file 
        title (scrapy.Field): The title of the file 
        file_path (scrapy.Field): The path where the file is downloaded to the local machine 
        date_scraped (scrapy.Field): The date when the file was downloaded 
    """
    type = 'file_metadata'
    url = scrapy.Field()
    title = scrapy.Field()
    file_path = scrapy.Field()
    date_scraped = scrapy.Field()


class Error301ScraperItem(scrapy.Item):
    type = 'error_301'
    url = scrapy.Field()
    status = scrapy.Field()


class ErrorScraperItem(scrapy.Item):
    type = 'error_all'
    url = scrapy.Field()
    status = scrapy.Field()
