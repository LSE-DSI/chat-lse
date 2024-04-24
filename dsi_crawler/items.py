# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DSIPagesScraperItem(scrapy.Item):
    """
    Represents an item scraped from the DSI pages.

    Attributes:
        origin_url (scrapy.Field): The original URL of the page.
        url (scrapy.Field): The URL of the page.
        title (scrapy.Field): The title of the page.
        text (scrapy.Field): The text content of the page.
        html (scrapy.Field): The HTML content of the page.
        date_scraped (scrapy.Field): The date when the page was scraped.
    """
    origin_url = scrapy.Field()  
    url = scrapy.Field()
    title = scrapy.Field()
    text = scrapy.Field()
    html = scrapy.Field()
    date_scraped = scrapy.Field()
