import scrapy
import hashlib
from crawler.items import PagesScraperItem
from dateutil.parser import parse


class SpiderDSI(scrapy.Spider):
    name = 'lse_crawler'
    start_urls = [
        'http://www.lse.ac.uk/accounting/Home.aspx',
        'http://www.lse.ac.uk/anthropology/home.aspx',
        'https://www.lse.ac.uk/dsi',
        'http://www.lse.ac.uk/economics/home.aspx',
        'http://www.lse.ac.uk/Economic-History',
        'http://www.lse.ac.uk/european-institute',
        'http://www.lse.ac.uk/Finance',
        'https://www.lse.ac.uk/africa',
        'http://www.lse.ac.uk/Gender',
        'http://www.lse.ac.uk/Geography-and-Environment',
        'http://www.lse.ac.uk/government/home.aspx',
        'http://www.lse.ac.uk/health-policy',
        'http://www.lse.ac.uk/international-development',
        'http://www.lse.ac.uk/International-History',
        'http://www.lse.ac.uk/International-Inequalities',
        'http://www.lse.ac.uk/International-Relations',
        'http://www.lse.ac.uk/language-centre',
        'https://www.lse.ac.uk/law',
        'http://www.lse.ac.uk/management/home.aspx',
        'http://www.lse.ac.uk/Marshall-Institute',
        'http://www.lse.ac.uk/Mathematics',
        'http://www.lse.ac.uk/media-and-communications',
        'http://www.lse.ac.uk/methodology',
        'http://www.lse.ac.uk/philosophy/',
        'http://www.lse.ac.uk/PBS',
        'http://www.lse.ac.uk/school-of-public-policy',
        'http://www.lse.ac.uk/social-policy',
        'http://www.lse.ac.uk/sociology/Home.aspx',
        'http://www.lse.ac.uk/statistics/home.aspx'
    ]
    max_depth = 3
    global visited
    visited = []

    def parse(self, response): 
        # Follow links found on the current page
        for next_page_url in response.css("a.component__link::attr(href)").extract():
            if next_page_url not in visited:
                visited.append(next_page_url)
                #print(f"following link: {response.urljoin(next_page_url)}")
                yield scrapy.Request(
                    response.urljoin(next_page_url),
                    callback=self.parse_linked_page,
                    meta={'depth': 1, 'origin_url': response.url},
                    errback=self.handle_error
                )

    def parse_linked_page(self, response):
        # Extract data from the linked page
        item = PagesScraperItem()
        item['url'] = response.url
        item['title'] = response.css('title::text').get().strip()
        item['content'] = response.text
        item['date_scraped'] = self.parse_as_datetime(response.headers['Date'].decode())
        item['doc_id'] = self.compute_hash(item['content'])

        yield item

        # Follow links found on the linked page if the depth is less than max_depth
        current_depth = response.meta.get('depth', 1)
        if current_depth < self.max_depth:
            for next_page_url in response.css("a.component__link::attr(href)").extract():
                if next_page_url not in visited:
                    visited.append(next_page_url)
                    yield scrapy.Request(
                        response.urljoin(next_page_url),
                        callback=self.parse_linked_page,
                        meta={'depth': current_depth + 1,
                              'origin_url': response.meta['origin_url']},
                        errback=self.handle_error
                    )

    def handle_error(self, failure):
        self.logger.error(repr(failure))
        self.logger.error('Failed URL: %s', failure.request.url)
        print("Error:", repr(failure), "Failed URL:", failure.request.url)

    def compute_hash(self, content: str):
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def parse_as_datetime(self, date_str): 
        # Takes a date string and parse it as a datetime object to be fed as TIMESTAMP 
        return parse(date_str).replace(tzinfo=None) 