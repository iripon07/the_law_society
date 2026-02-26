from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


def save_page_source_headless(url, filename="page_source.html"):
    # Configure Chrome options for headless mode
    chrome_options = Options()
    # chrome_options.add_argument(
    #     "--headless=new"
    # )  # Use the new headless mode if available
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-gpu")

    # Initialize the Chrome WebDriver with options
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Navigate to the target URL
        print("Searching")
        driver.get(url)

        # Wait for the page to load completely (adjust as needed)
        time.sleep(15)
        print("Got it")

        # Retrieve the page source
        page_source = driver.page_source

        # Write the page source to a file with UTF-8 encoding
        with open(filename, "w", encoding="utf-8") as file:
            file.write(page_source)

        print(f"Successfully saved page source to {filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()


# Example usage:
# Replace "http://example.com" with the URL you want to scrape
save_page_source_headless(
    "https://solicitors.lawsociety.org.uk/search/results?Pro=True&Type=0&Location=London+Colney&LocationId=london-colney",
    "main_page_source.html",
)
