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
data = {"people_office_struct_org": "Missing", "people_office_struct_office": "Missing"}

try:
    url = "https://solicitors.lawsociety.org.uk/office/539073/labrums-solicitors-llp"
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    section_fields = driver.find_elements(By.TAG_NAME, "section")

    for section_field in section_fields:
        # Get title safely
        try:
            title_el = section_field.find_element(By.TAG_NAME, "h2")
            areas_titles = title_el.text.strip().lower()
        except:
            continue

        if "people, offices and structure" in areas_titles:
            halves = section_field.find_elements(
                By.CSS_SELECTOR, "div.accordion-inner-body-split-halves > div"
            )

            # --- ORGANIZATION SIDE ---
            if len(halves) >= 1:
                org_list = []  # Defined inside the block
                org_li_elements = halves[0].find_elements(By.TAG_NAME, "li")
                for li in org_li_elements:
                    raw_text = li.get_attribute("textContent")
                    clean_item = (
                        " ".join(raw_text.split())
                        .replace("in this organisation", "")
                        .strip()
                    )
                    if clean_item:
                        org_list.append(clean_item)
                data["people_office_struct_org"] = ", ".join(org_list)

            # --- OFFICE SIDE ---
            if len(halves) >= 2:
                off_list = []  # Defined inside the block
                off_li = halves[1].find_elements(By.TAG_NAME, "li")
                for li in off_li:
                    txt = li.get_attribute("textContent")
                    clean = " ".join(txt.split()).replace("at this office", "").strip()
                    if clean:
                        off_list.append(clean)
                # MOVED INSIDE the if-block to prevent 'not defined' errors
                data["people_office_struct_office"] = ", ".join(off_list)
        print(data)

    # SUCCESS LOGGING
    print(f"\n{BOLD}Extraction Complete!{RESET}")
    print(f"Org: {data['people_office_struct_org']}")
    print(f"Office: {data['people_office_struct_office']}")
    print(f"{GREEN}💾 DATA READY TO SAVE{RESET}")

except Exception as e:
    print(f"Failed to scrape: {e}")

finally:
    driver.quit()
