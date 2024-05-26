import scrapy
import os
from scrapy.utils.project import get_project_settings


class FileDownloaderSpider(scrapy.Spider):
    name = 'file_downloader'
    start_urls = [
        'https://www.lse.ac.uk/2030'    
         ]
    
    def parse(self, response):
        # Look for links to files
        for file_link in response.css("a::attr(href)").extract():
            if file_link.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx')):
                yield scrapy.Request(response.urljoin(file_link), callback=self.save_file)
    
    def save_file(self, response):
        file_name = response.url.split('/')[-1]
        
        # Save the file
        file_path = os.path.join('data/', file_name)
        with open(file_path, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {file_name}')