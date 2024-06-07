import scrapy
from dsi_crawler.items import DSIPagesScraperItem
from dsi_crawler.items import BoxScraperItem


class SpiderDSI(scrapy.Spider):
    name = 'dsi_crawler'
    start_urls = [
        'https://www.lse.ac.uk/DSI',
    ]
    max_depth = 3

    def parse(self, response):
        # Extract box data from the current page
        self.parse_boxes(response)

        # Follow links found on the current page
        for next_page_url in response.css("a.component__link::attr(href)").extract():
            yield scrapy.Request(
                response.urljoin(next_page_url),
                callback=self.parse_linked_page,
                meta={'depth': response.meta.get(
                    'depth', 0) + 1, 'origin_url': response.url}
            )

    def parse_linked_page(self, response):
        # Extract data from the linked page
        item = DSIPagesScraperItem()
        item['origin_url'] = response.meta.get(
            'origin_url', self.start_urls[0])
        item['url'] = response.url
        item['title'] = response.css('title::text').get().strip()
        item['html'] = response.text
        item['date_scraped'] = response.headers['Date'].decode()

        yield item

        # Extract box data from the linked page
        self.parse_boxes(response)

        # Follow links found on the linked page if the depth is less than max_depth
        current_depth = response.meta.get('depth', 1)
        if current_depth < self.max_depth:
            for next_page_url in response.css("a.component__link::attr(href)").extract():
                yield scrapy.Request(
                    response.urljoin(next_page_url),
                    callback=self.parse_linked_page,
                    meta={'depth': current_depth + 1,
                          'origin_url': response.url}
                )

    def parse_boxes(self, response):
        for box in response.css("a.component__link"):
            item = BoxScraperItem()
            item['origin_url'] = response.url
            item['url'] = box.attrib['href']
            item['title'] = box.css("h2.component__title ::text").get().strip()
            item['html'] = '\n'.join(
                [element for element in box.css(".component__details").extract()])
            item['date_scraped'] = response.headers['Date'].decode()
            item['image_src'] = box.css(
                "div.component__img img::attr(src)").get()
            item['image_alt_text'] = box.css(
                ".component__img img::attr(alt)").get()

            yield item
