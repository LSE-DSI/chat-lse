import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SimpleSeleniumSpider(scrapy.Spider):
    name = "simple_selenium"

    def start_requests(self):
        yield SeleniumRequest(
            url='https://www.lse.ac.uk/library',
            wait_time=10,
            callback=self.parse
        )

    def parse(self, response):
        driver = response.meta.get('driver')
        if not driver:
            self.log("Driver not found in response meta.")
            return

        self.log("Driver found, Selenium integration successful.")
        # Verify a simple interaction
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'Loginto')))
            self.log(f"Element found: {element.tag_name}")
        except Exception as e:
            self.log(f"Error finding element: {e}")

        # Close the driver
        driver.quit()
