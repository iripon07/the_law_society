import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Colors for your Save Sign
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"

chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)

# Initialize with default values
current_data = {
    "sra_id": "Missing",
    "firm_name": "Missing",
    "trading_names": "Missing",
    "type": "Missing",
    "is_sra_regulated": True,
    "telephone": "Missing",
    "email": "Missing",
    "website": "Missing",
}

try:
    url = "https://solicitors.lawsociety.org.uk/office/621087/abbey-law-limited"
    driver.get(url)
    # Wait for the main detail container
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "details-outer"))
    )

    # Find all dt/dd pairs within the details section
    dl_element = driver.find_element(
        By.CSS_SELECTOR, "div.details-outer dl.single-lines"
    )
    all_dts = dl_element.find_elements(By.TAG_NAME, "dt")

    for dt in all_dts:
        label = dt.text.strip().lower()
        # Find the immediately following dd element
        dd = dt.find_element(By.XPATH, "./following-sibling::dd[1]")
        value = dd.text.strip()

        if "sra id" in label:
            current_data["sra_id"] = value.split("|")[0].strip()
        elif "type" in label:
            current_data["type"] = value
        elif "trading names" in label:
            current_data["trading_names"] = value
        elif "telephone" in label:
            current_data["telephone"] = value
        elif "email" in label:
            # The email is hidden in a data attribute on an <a> tag inside the dd
            try:
                email_elem = dd.find_element(By.CLASS_NAME, "show-email")
                current_data["email"] = email_elem.get_attribute("data-email")
            except:
                current_data["email"] = "Not Found"
        elif "web" in label:
            current_data["website"] = value

    # Check SRA Regulation separately (it's often a tick icon, not text)
    if "SRA Regulated" in driver.page_source:
        current_data["is_sra_regulated"] = True
    else:
        current_data["is_sra_regulated"] = False

    print(current_data)

finally:
    driver.quit()
