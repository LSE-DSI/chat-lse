import scrapy
import pandas as pd

class MySpider(scrapy.Spider):
    name = 'dsi_scraper'

    def start_requests(self):
        urls = [
            'https://www.lse.ac.uk/DSI',
        ]
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = []
        for link in response.css("a.component__link"):
            title = link.css("h2.component__title ::text").get().strip()
            text = ' '.join(link.css(".component__details ::text").getall()).strip()
            url = link.attrib['href']
            data.append({'Title': title, 'Text': text, 'URL': url})

        # Creating DataFrame
        df = pd.DataFrame(data)

        # Saving to CSV
        df.to_csv('scrapy_data.csv')

        self.log('Saved data to scrapy_data.csv')

