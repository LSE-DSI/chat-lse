import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import scrapy
from scrapy.utils.project import get_project_settings
from scrapy_selenium import SeleniumRequest


class SimpleSeleniumSpider(scrapy.Spider):
    name = "simple_selenium"

    def start_requests(self):
        yield SeleniumRequest(
            url='https://www.lse.ac.uk/library',
            wait_time=10,
            callback=self.parse,
            script='window.scrollTo(0, document.body.scrollHeight);'
        )

    def parse(self, response):
        driver = response.meta.get('driver')
        login_link = response.css('#Loginto::attr(href)').get()
        login_link = response.urljoin(login_link)
        self.logger.info('Login link: %s', login_link)
        yield scrapy.Request(login_link, callback=self.parse_login)

    def parse_login(self, response):
        next_button = response.css('#staff::attr(href)').get()
        next_button = response.urljoin(next_button)
        self.logger.info('Next button: %s', next_button)
