import scrapy
from dsi_crawler.items import DSIPagesScraperItem, BoxScraperItem

class SpiderDSI(scrapy.Spider):
    name = 'lse_crawler'
    start_urls = [
        'https://info.lse.ac.uk/Staff/Departments-and-Institutes'
    ]
    max_depth = 3

    def parse(self, response):
        # Extract department URLs from the main page using class names
        department_links = response.css('a.sys_16.external::attr(href)').extract()
        for department_link in department_links:
            yield scrapy.Request(
                response.urljoin(department_link),
                callback=self.parse_department_page,
                meta={'origin_url': response.urljoin(department_link)},
                errback=self.handle_error
            )

    def parse_department_page(self, response):
        # Extract box data from the department page
        self.parse_boxes(response)
        
        # Follow links found on the department page
        for next_page_url in response.css("a.component__link::attr(href)").extract():
            yield scrapy.Request(
                response.urljoin(next_page_url),
                callback=self.parse_linked_page,
                meta={'depth': 1, 'origin_url': response.meta['origin_url']},
                errback=self.handle_error
            )

    def parse_linked_page(self, response):
        # Extract data from the linked page
        item = DSIPagesScraperItem()
        item['origin_url'] = response.meta['origin_url']
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
                    meta={'depth': current_depth + 1, 'origin_url': response.meta['origin_url']},
                    errback=self.handle_error
                )

    def parse_boxes(self, response):
        for box in response.css("a.component__link"):
            item = BoxScraperItem()
            item['origin_url'] = response.meta['origin_url']
            item['url'] = response.urljoin(box.attrib['href'])
            item['title'] = box.css("h2.component__title::text").get().strip()
            item['html'] = ''.join(box.css(".component__details").extract())
            item['date_scraped'] = response.headers['Date'].decode()
            item['image_src'] = box.css("div.component__img img::attr(src)").get()
            item['image_alt_text'] = box.css(".component__img img::attr(alt)").get()

            yield item

    def handle_error(self, failure):
        self.logger.error(repr(failure))
        self.logger.error('Failed URL: %s', failure.request.url)
