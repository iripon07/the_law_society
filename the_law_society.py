import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        links = []

        for page_numbers in range(1, 6):
            url = f"https://solicitors.lawsociety.org.uk/search/results?Pro=True&Type=0&Location=London+Colney&LocationId=london-colney&Page={page_numbers}"
            print("Starting headless browser...")
            driver.get(url)
            time.sleep(30)
            print(f"Page Title: {driver.title}")

            # Assuming 'driver' is already initialized

            solicitor_sections = driver.find_elements(By.CLASS_NAME, "solicitor-outer")
            for section in solicitor_sections:
                link_element = section.find_element(By.CSS_SELECTOR, "h2 a")
                relative_path = link_element.get_attribute("href")
                if relative_path:
                    links.append(relative_path)

    finally:
        driver.quit()
        print("Browser closed.")


if __name__ == "__main__":
    main()
