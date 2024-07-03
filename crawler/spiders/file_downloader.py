import scrapy
import os

class FileDownloaderSpider(scrapy.Spider):
    name = 'file_downloader'
    start_urls = [
        'https://info.lse.ac.uk/Staff/Divisions/Human-Resources/A-to-Z'    
         ]
    
    def parse(self, response):
        for file_link in response.css("a::attr(href)").extract():
            if file_link.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx')):
                yield scrapy.Request(response.urljoin(file_link), callback=self.save_file)
    
    def save_file(self, response):
        file_name = response.url.split('/')[-1]
        
        # Save the file
        file_path = os.path.join('data/documents/', file_name)
        with open(file_path, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {file_name}')