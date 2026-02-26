import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1. Setup
chrome_options = Options()
# chrome_options.add_argument("--headless") # Commented out so you can see it work first
driver = webdriver.Chrome(options=chrome_options)


def scrape_organization(url):
    # Initialize dictionary with your defaults
    data = {
        # Text Fields - Default: "Missing"
        "firm_name": "Missing",
        "tradings_names": "Missing",
        "type": "Missing",
        "sra_id": "Missing",
        "is_sra_regulated": True,
        # "regulation_status": "Missing",
        "telephone": "Missing",
        "email": "Missing",
        "website": "Missing",
        "profile_url": "Missing",
        "address_raw": "Missing",
        "address_line_1": "Missing",
        "address_line_2": "Missing",
        "city": "Missing",
        "county": "Missing",
        "postcode": "Missing",
        "google_map": "Missing",
        "practice_areas_branch": "Missing",
        "practice_areas_org": "Missing",
        "accreditations": "Missing",
        "total_people": "Missing",
        "total_solicitors": "Missing",
        "total_sra_managers": "Missing",
        "total_offices": "Missing",
        "languages_at_branch": "Missing",
        "languages_at_org": "Missing",
        # Boolean Fields - Default: True
        "has_disabled_access": True,
        "has_induction_loops": True,
        "accepts_legal_aid": True,
        "provides_sign_language": True,
    }
    try:
        print(f"Accessing: {url}")
        driver.get(url)

        # Use WebDriverWait instead of a hard sleep for better reliability
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # 1. Extract Firm Name
        data["firm_name"] = driver.find_element(
            By.CSS_SELECTOR, "header h1"
        ).text.strip()

        # 2. Extract Data from the DL (dt/dd pairs)
        try:
            dl_element = driver.find_element(
                By.CSS_SELECTOR, "div.details-outer dl.single-lines"
            )
            all_dts = dl_element.find_elements(By.TAG_NAME, "dt")
            # print("All dts", all_dts)

            for dt in all_dts:
                dt_texts = dt.text.strip().lower()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                text_value = dd.text.strip()

                # print("Text value ", text_value)

                # print("Label check", dt_texts)
                if "type" in dt_texts:
                    data["type"] = text_value

                elif "sra id" in dt_texts:
                    data["sra_id"] = text_value.split("|")[0].strip()

                elif "sra regulated" not in dt_texts:
                    data["is_sra_regulated"] = False
                elif "telephone" in dt_texts:
                    data["telephone"] = text_value

                elif "email" in dt_texts:
                    element = driver.find_element(By.CLASS_NAME, "show-email")
                    email_address = element.get_attribute("data-email")
                    data["email"] = email_address
                elif "web" in dt_texts:
                    data["website"] = text_value

        except Exception as e:
            print(f"Detail section missing: {e}")

        # 3. Check Regulation Status
        if "not regulated by the sra" in driver.page_source.lower():
            data["is_sra_regulated"] = False

    except Exception as e:
        print(f"Failed to scrape: {e}")

    return data


# --- THIS IS THE PART THAT WAS MISSING ---
# Call the function and print result
target_url = "https://solicitors.lawsociety.org.uk/office/539073/labrums-solicitors-llp"
result = scrape_organization(target_url)

print("\n--- SCRAPED DATA ---")
for key, val in result.items():
    print(f"{key}: {val}")

# Close driver at the very end
driver.quit()
