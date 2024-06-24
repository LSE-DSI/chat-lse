import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import json


class ExamsSpider(scrapy.Spider):
    name = "exams"

    def start_requests(self):
        yield SeleniumRequest(
            url='https://www.lse.ac.uk/library',
            wait_time=10,
            callback=self.parse,
            script='window.scrollTo(0, document.body.scrollHeight);'
        )

    def parse(self, response):
        driver = response.meta.get('driver')
        if not driver:
            self.log("Driver not found in response meta.")
            return

        driver.fullscreen_window()

        # Perform login actions
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'Loginto'))).click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH, '/html/body/div[3]/div/div/h3[1]/a'))).click()
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
            (By.NAME, 'loginfmt'))).send_keys('username')
        next_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'idSIButton9')))
        if next_button:
            next_button.click()
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.NAME, 'passwd'))).send_keys('password')
        next_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'idSIButton9')))
        next_button.click()

        print(WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="idRichContext_DisplaySign"]'))).text)

        try:
            element = WebDriverWait(driver, 300).until(
                EC.visibility_of_element_located((By.ID, 'idBtn_Back')))
            element.click()
        except TimeoutException:
            self.log("The element did not appear within the time limit")

        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'div.grid-item:nth-child(1) > button:nth-child(1)'))).click()
        new_url = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, '#mainMenu > div:nth-child(4) > a:nth-child(1)')))[0].get_attribute("href")
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '#mainMenu > div:nth-child(4) > a:nth-child(1)'))).click()
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)

        # Start scraping exam papers
        self.scrape_exam_papers(driver)

    def scrape_exam_papers(self, driver):
        list = []

        def get_elements(css_selector, retries=3):
            for attempt in range(retries):
                try:
                    return WebDriverWait(driver, 60).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
                except (StaleElementReferenceException, TimeoutException) as e:
                    if attempt < retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        self.log(f"Failed to get elements: {e}")
                        return []

        def get_element(css_selector, retries=3):
            for attempt in range(retries):
                try:
                    return WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
                except (StaleElementReferenceException, TimeoutException) as e:
                    if attempt < retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        self.log(f"Failed to get element: {e}")
                        return None

        def click_load_more():
            try:
                load_more_button = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/primo-explore/div/prm-explore-main/ui-view/prm-collection-discovery/prm-collection-gallery/md-content/div[2]/prm-gallery-items-list/div/div[3]/button")))
                load_more_button.click()
                time.sleep(1)
                self.log("Clicked 'Load More' button.")
            except (NoSuchElementException, TimeoutException) as e:
                self.log(f"'Load More' button not found or not clickable: {
                         e}. Continuing...")

        def find_show_more():
            try:
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/primo-explore/div[3]/div/md-dialog/md-dialog-content/sticky-scroll/prm-full-view/div/div/div/div/div[1]/div[4]/div/prm-full-view-service-container/div[2]/div/prm-alma-viewit/prm-alma-viewit-items/button")))
                return True
            except TimeoutException:
                return False

        def click_show_more():
            try:
                show_more_button = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/primo-explore/div[3]/div/md-dialog/md-dialog-content/sticky-scroll/prm-full-view/div/div/div/div/div[1]/div[4]/div/prm-full-view-service-container/div[2]/div/prm-alma-viewit/prm-alma-viewit-items/button")))
                show_more_button.click()
                time.sleep(1)
                self.log("Clicked 'Show More' button.")
            except (NoSuchElementException, TimeoutException) as e:
                self.log(f"'Show More' button not found or not clickable: {
                         e}. Continuing...")

        try:
            driver.execute_script("document.body.style.zoom='30%'")
            boxes = get_elements(
                ".margin-bottom-small > prm-gallery-collection")

            for m in range(len(boxes)):
                for retry in range(3):  # Retry loop for each box
                    try:
                        driver.execute_script("document.body.style.zoom='30%'")
                        boxes = get_elements(
                            ".margin-bottom-small > prm-gallery-collection")
                        box = boxes[m]
                        details = {}

                        title = get_element(f".margin-bottom-small > prm-gallery-collection:nth-child({
                                            m+1}) > a:nth-child(1) > div:nth-child(1) > div:nth-child(1) > h3:nth-child(2) > span:nth-child(1)").text
                        subject_page_url = box.find_element(
                            By.TAG_NAME, "a").get_attribute("href")
                        box.click()

                        if m in [1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 19, 23, 24]:
                            while True:
                                click_load_more()
                                try:
                                    load_more_button = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
                                        (By.XPATH, "/html/body/primo-explore/div/prm-explore-main/ui-view/prm-collection-discovery/prm-collection-gallery/md-content/div[2]/prm-gallery-items-list/div/div[3]/button")))
                                    load_more_button.click()
                                except TimeoutException:
                                    break

                        containers = get_elements(
                            f".is-grid-view > prm-gallery-item")

                        for i in range(len(containers)):
                            containers = get_elements(
                                f".is-grid-view > prm-gallery-item")
                            driver.execute_script(
                                "arguments[0].scrollIntoView();", containers[i])
                            container = containers[i]

                            course_name = container.find_element(
                                By.CLASS_NAME, "item-title").text
                            type = container.find_element(
                                By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(2) > span:nth-child(1) > span:nth-child(1)").text

                            # Scroll up by 200 pixels
                            driver.execute_script("window.scrollBy(0, -200);")

                            container.click()

                            if find_show_more():
                                click_show_more()
                                time.sleep(1)
                            else:
                                self.log(
                                    "'Show More' button not visible. Continuing...")

                            exams = get_elements("md-list-item.md-3-line")

                            driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(
                                By.CSS_SELECTOR, '#action_list > div:nth-child(1) > prm-full-view-service-container:nth-child(1) > div:nth-child(1) > prm-service-header:nth-child(1)'))

                            for n in range(1, len(exams) + 1):
                                exam = get_element(f"md-list-item.md-3-line:nth-child({
                                                   n}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1)")

                                if exam:
                                    driver.execute_script(
                                        "arguments[0].scrollIntoView();", exam)
                                    exam_year = exam.text
                                    pdf_link = exam.get_attribute("href")

                                    details = {
                                        "name": title,
                                        "subject_page_url": subject_page_url,
                                        "course_name": course_name,
                                        "type": type,
                                        "exam_year": exam_year,
                                        "pdf_link": pdf_link
                                    }
                                    list.append(details)
                                    self.log(details)

                            exit_button = get_element(
                                "button.md-icon-button:nth-child(4)")
                            if exit_button:
                                exit_button.click()
                            else:
                                self.log("Exit button not found. Retrying...")
                                raise TimeoutException("Exit button not found")

                    except (StaleElementReferenceException, TimeoutException) as e:
                        self.log(f"Error processing box {m}: {e}. Retrying...")
                        back_button = get_element(
                            "prm-collection-navigation-breadcrumbs-item.layout-align-start-center:nth-child(2) > a:nth-child(1)")
                        if back_button:
                            driver.execute_script(
                                "arguments[0].scrollIntoView();", back_button)
                            back_button.click()
                            time.sleep(5)
                            WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, ".margin-bottom-small > prm-gallery-collection")))
                            continue
                        else:
                            self.log(
                                "Back button not found. Breaking out of retry loop.")
                            break

                    else:
                        break  # Break out of retry loop if no exception

                with open(f"exam_papers_{m}.json", "w") as f:
                    json.dump(list, f, indent=4)
                    self.log(f"Saved to exam_papers_{m}.json")
                back_button = get_element(
                    "prm-collection-navigation-breadcrumbs-item.layout-align-start-center:nth-child(2) > a:nth-child(1)")
                if back_button:
                    driver.execute_script(
                        "arguments[0].scrollIntoView();", back_button)
                    time.sleep(5)
                    back_button.click()
                    time.sleep(15)
                    WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, ".margin-bottom-small > prm-gallery-collection")))

        except (StaleElementReferenceException, TimeoutException) as e:
            self.log(f"Container processing error: {e}")

        return list
