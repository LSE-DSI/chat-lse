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
        origin_url (scrapy.Field): The original URL of the page.
        link (scrapy.Field): The URL of the page.
        title (scrapy.Field): The title of the page.
        content (scrapy.Field): The HTML content of the page.
        date_scraped (scrapy.Field): The date when the page was scraped.
    """
    type = 'webpages'
    origin_url = scrapy.Field()
    link = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    date_scraped = scrapy.Field()
    current_hash = scrapy.Field()
