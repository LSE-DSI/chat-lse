import os
import scrapy
import hashlib
from crawler.items import PagesScraperItem, FilesScraperItem
from dateutil.parser import parse

DATA_FOLDER = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '..', '..', 'data', 'files')

global abnormal_error
global error_301
abnormal_error = {}
error_301 = {}


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
        for next_page_url in response.css("a.component__link::attr(href)").extract():
            if next_page_url not in visited:
                visited.append(next_page_url)

                # Download linked files
                # Keeping only support for .pdf for now
                if next_page_url.endswith(('.pdf')):
                    # Download the linked files
                    yield scrapy.Request(response.urljoin(next_page_url), callback=self.save_file)

                    #  Save metadata for the files to be downloaded
                    file_item = FilesScraperItem()
                    file_item["url"] = response.urljoin(next_page_url)
                    file_item["title"] = next_page_url.split('/')[-1]
                    file_item["file_path"] = os.path.join(
                        'data/files/', file_item["title"])
                    file_item["date_scraped"] = file_item['date_scraped'] = self.parse_as_datetime(
                        response.headers['Date'].decode())

                    yield file_item

                #  Follow links found on the current page
                else:
                    yield scrapy.Request(
                        response.urljoin(next_page_url),
                        callback=self.parse_linked_page,
                        meta={'depth': 1, 'origin_url': response.url},
                        errback=self.handle_error
                    )

    def parse_linked_page(self, response):
        # Extract data from the linked page
        webpage_item = PagesScraperItem()
        webpage_item['url'] = response.url
        webpage_item['title'] = response.css('title::text').get().strip()
        webpage_item['content'] = response.text
        webpage_item['date_scraped'] = self.parse_as_datetime(
            response.headers['Date'].decode())
        webpage_item['doc_id'] = self.compute_hash(webpage_item['content'])

        yield webpage_item

        current_depth = response.meta.get('depth', 1)
        if current_depth < self.max_depth:
            for next_page_url in response.css("a.component__link::attr(href)").extract():
                if next_page_url not in visited:
                    visited.append(next_page_url)

                    # Download linked files
                    # Keeping only support for .pdf for now
                    if next_page_url.endswith(('.pdf')):
                        # Download the linked files
                        yield scrapy.Request(response.urljoin(next_page_url), callback=self.save_file)

                        #  Save metadata for the files to be downloaded
                        file_item = FilesScraperItem()
                        file_item["url"] = response.urljoin(next_page_url)
                        file_item["title"] = next_page_url.split('/')[-1]
                        file_item["file_path"] = os.path.join(
                            'data/files/', file_item["title"])
                        file_item["date_scraped"] = file_item['date_scraped'] = self.parse_as_datetime(
                            response.headers['Date'].decode())

                        yield file_item

                    # Follow links found on the linked page if the depth is less than max_depth
                    else:
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
        try:
            if failure.value.response.status != 200:
                print("Non-200/301 http error:", failure.request.url)
                abnormal_error[
                    f"{failure.request.url}"] = failure.value.response.status
                if failure.value.response.status == 301:
                    error_301[
                        f"{failure.request.url}"] = failure.value.response.status
        except AttributeError:
            print("Failure object does not have the expected attributes")
            self.logger.error(
                "Failure object does not have the expected attributes")

    def compute_hash(self, content: str):
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def parse_as_datetime(self, date_str):
        # Takes a date string and parse it as a datetime object to be fed as TIMESTAMP
        return parse(date_str).replace(tzinfo=None)

    def save_file(self, response):
        file_name = response.url.split('/')[-1]

        os.makedirs(DATA_FOLDER, exist_ok=True)

        # Save the file
        file_path = os.path.join(DATA_FOLDER, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {file_name}')
