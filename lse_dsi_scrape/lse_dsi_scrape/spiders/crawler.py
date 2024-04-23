import scrapy
import os 

class MySpider(scrapy.Spider):
    name = 'dsi_scraper'
    start_urls = [
        'https://www.lse.ac.uk/DSI',
    ]

    def parse(self, response):
        # Extract data from the current page
        for box in response.css("a.component__link"):
            yield {
                'Title': box.css("h2.component__title ::text").get().strip(),
                'Text': ' '.join(box.css(".component__details ::text").getall()).strip(),
                'URL': box.attrib['href']
            }

        # Follow links found on the current page
        for next_page_url in response.css("a.component__link::attr(href)").extract():
            yield scrapy.Request(response.urljoin(next_page_url), callback=self.parse_linked_page)

    def parse_linked_page(self, response):
        # Extract data from the linked page
        page = {
            'Title': response.css('title::text').get(),
            'Text': ' '.join(response.css('p::text').getall()),
            'URL': response.url
        }
        
        # Create a folder if it doesn't exist
        folder_name = 'linked_pages'
        os.makedirs(folder_name, exist_ok=True)
        
        filename = f"{folder_name}/Linked_DSI_Page_{response.url.split('/')[-1]}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Title: {page['Title']}\n")
            f.write(f"Text: {page['Text']}\n")
            f.write(f"URL: {page['URL']}\n")
        
        self.log(f"Saved file {filename}")
        
        yield page