import scrapy
import os
from crawler.items import FilesScraperItem
from dateutil.parser import parse

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'data', 'files')

class FileDownloaderSpider(scrapy.Spider):
    name = 'file_downloader'
    start_urls = [
        'https://info.lse.ac.uk/Staff/Divisions/Human-Resources/A-to-Z'    
         ]
    
    def parse(self, response):

        for file_link in response.css("a::attr(href)").extract():
            if file_link.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx')):
                # Save metadata for the files to be downloaded 
                item = FilesScraperItem()
                item["url"] = file_link 
                item["title"] = file_link.split('/')[-1]
                item["file_path"] = os.path.join(DATA_FOLDER, item["title"])
                item["date_scraped"] = item['date_scraped'] = self.parse_as_datetime(response.headers['Date'].decode())

                yield item 

                # Download the linked files 
                yield scrapy.Request(response.urljoin(file_link), callback=self.save_file)
    
    def save_file(self, response):
        file_name = response.url.split('/')[-1]
        
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # Save the file
        file_path = os.path.join(DATA_FOLDER, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {file_name}')

    def parse_as_datetime(self, date_str): 
        # Takes a date string and parse it as a datetime object to be fed as TIMESTAMP 
        return parse(date_str).replace(tzinfo=None) 