# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BoxScraperItem(scrapy.Item):
    """
    Represents a box scraped from the DSI pages. 

    Attributes: 
    name: The name of the item, i.e box
    origin_url (scrapy.Field): The original URL of the box.
    img_url (scrapy.Field): The URL of the image in the box.
    title (scrapy.Field): The title of the box.
    html (scrapy.Field): The html content of the box.
    image_src (scrapy.Field): The source of the image in the box
    image_alt_text (scrapy.Field): The alternative text to the image in the box. 
    date_scraped (scrapy.Field): The date when the box was scraped.
    """
    name = 'boxes'
    origin_url = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    html = scrapy.Field()
    image_src = scrapy.Field()
    image_alt_text = scrapy.Field()
    date_scraped = scrapy.Field()
    current_hash = scrapy.Field()


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
