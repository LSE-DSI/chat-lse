import scrapy

import os
import hashlib
from bs4 import BeautifulSoup
from crawler.items import SUPagesScraperItem, ErrorScraperItem, Error301ScraperItem
from dateutil.parser import parse

from chatlse.crawler import clean_text

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'data', 'files')

class LsesuCrawlerSpider(scrapy.Spider):
    name = "lsesu_crawler"
    allowed_domains = ["www.lsesu.com"]
    start_urls = ["https://www.lsesu.com"]

    max_depth = 6

    def __init__(self, *args, **kwargs):
        super(LsesuCrawlerSpider, self).__init__(*args, **kwargs)
        self.visited = []

    def parse(self, response):
        for next_page_url in response.css("a.nav-link::attr(href)").extract():
#            if next_page_url not in visited:
            self.visited.append(next_page_url)

            yield scrapy.Request(
                response.urljoin(next_page_url),
                callback=self.parse_linked_page,
                meta={'depth': 1, 'origin_url': response.url},
                errback=self.handle_error
            )
    
    def parse_linked_page(self, response):
        # Parse the html content from the linked page 
        soup = BeautifulSoup(response.text, 'html.parser')
        cleaned_content = clean_text(soup.get_text())
        cleaned_excluded = cleaned_content.replace('''Saw Swee Hock Student Centre, \r 1 Sheffield Street,\r London WC2A 2AP\r Registered Charity Number: 1143103\r Company Number: 7710669We are a London Living Wage employerLSESU''', " " )
        cleaned_excluded = cleaned_excluded.replace('''FacebookLSESU TwitterLSESU InstagramLSESU YouTubeLSESU LinkedIn''', " " )
        cleaned_excluded = cleaned_excluded.replace('''Return to LSESU site Controls Admin Basket Sign InHomeStudent Voice Student RepresentativesAcademic RepresentationElectionsDemocracy CommitteeDemocracy ReviewStudent Town HallsStudent PanelsSubmit a Policy Proposal!Campaigns & PolicyTeaching AwardsCommunities SocietiesRAGStudent MediaSports and RecreationMarshall BuildingCommittee HubWhat's on Upcoming EventsThe Three TunsDenning Learning CaféGymActive LifestyleWind Down WednesdaysSupport Advice ServiceGuidance on The Middle EastCovid-19 UpdatesFundingStudent Check - InBME MentoringReporting Racism at LSEConsent EdReally Useful StuffLead LSESearchHomeSupport Funding''', " " )
        print(f"Cleaned content: {cleaned_excluded}")
    


        # Extract data from the linked page
        webpage_item = SUPagesScraperItem()
        webpage_item['url'] = response.url
        webpage_item['title'] = response.css('title::text').get().strip()
        webpage_item['content'] = cleaned_excluded
        webpage_item['date_scraped'] = self.parse_as_datetime(response.headers['Date'].decode())
        webpage_item['doc_id'] = self.compute_hash(cleaned_content)

        print(f"Yielding PagesScraperItem: {webpage_item}")

        yield webpage_item

        current_depth = response.meta.get('depth', 1)
        if current_depth < self.max_depth:
            for next_page_url in response.css("a.msl-imagenav-page::attr(href)").extract():
#               if next_page_url not in visited:
                self.visited.append(next_page_url)

                yield scrapy.Request(
                    response.urljoin(next_page_url),
                    callback=self.parse_linked_page,
                    meta={'depth': current_depth + 1, 'origin_url': response.meta['origin_url']},
                    errback=self.handle_error
                )

    def handle_error(self, failure):
        self.logger.error(repr(failure))
        self.logger.error('Failed URL: %s', failure.request.url)
        print("Error:", repr(failure), "Failed URL:", failure.request.url)
        try:
            if failure.value.response.status != 200:
                print("Non-200 http error:", failure.request.url)
                error_item = ErrorScraperItem()
                error_item["url"] = failure.request.url
                error_item["status"] = failure.value.response.status
                print(f"Yielding ErrorScraperItem: {error_item}")
                yield error_item

                if failure.value.response.status == 301:
                    print("301 http error:", failure.request.url)
                    error301_item = Error301ScraperItem()
                    error301_item["url"] = failure.request.url
                    error301_item["status"] = failure.value.response.status
                    print(f"Yielding Error301ScraperItem: {error301_item}")
                    yield error301_item

        except AttributeError:
            self.logger.error(
                "Failure object does not have the expected attributes")
            error_item = ErrorScraperItem()
            error_item["url"] = failure.request.url
            error_item["status"] = "Forbidden by robots.txt"
            print(f"Yielding ErrorScraperItem with status: {error_item}")
            yield error_item

    def compute_hash(self, content: str):
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def parse_as_datetime(self, date_str):
        # Takes a date string and parse it as a datetime object to be fed as TIMESTAMP
        return parse(date_str).replace(tzinfo=None)
            
        

