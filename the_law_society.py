import csv
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
CSV_FILE = "law_society_data.csv"
JSON_FILE = "law_society_data.json"


def get_blueprint_data(url):
    return {
        "sra_id": "Missing",
        "firm_name": "Missing",
        "tradings_name": "Missing",
        "type": "Missing",
        "is_sra_regulated": True,
        "telephone": "Missing",
        "email": "Missing",
        "website": "Missing",
        "profile_url": url,
        "address_raw": "Missing",
        "city": "Missing",
        "county": "Missing",
        "postal_code": "Missing",
        "country": "Missing",
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
        "has_disabled_access": False,
        "has_induction_loops": False,
        "accepts_legal_aid": False,
        "provides_sign_language": False,
    }


def main():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    all_results = []
    links = []

    try:
        for page_num in range(1, 7):
            url = f"https://solicitors.lawsociety.org.uk/search/results?Pro=True&Type=0&Location=London+Colney&LocationId=london-colney&Page={page_num}"
            print(f"Gathering links from search page {page_num}...")
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "solicitor-outer"))
            )
            solicitor_sections = driver.find_elements(By.CLASS_NAME, "solicitor-outer")
            for section in solicitor_sections:
                link_element = section.find_element(By.CSS_SELECTOR, "h2 a")
                relative_path = link_element.get_attribute("href")
                if relative_path:
                    links.append(relative_path)

        total_links = len(links)
        print(f"\nFound {total_links} total firms.\n")

        # Open CSV once and write headers
        headers = list(get_blueprint_data("").keys())
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=headers)
            writer.writeheader()

            for index, link in enumerate(links, 1):
                current_data = get_blueprint_data(link)

                try:
                    driver.get(link)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "h1"))
                    )

                    # Firm Name
                    current_data["firm_name"] = driver.find_element(
                        By.CSS_SELECTOR, "header h1"
                    ).text.strip()
                    print(f"✅ [{index}/{total_links}]: {current_data['firm_name']}")

                    dl_element = driver.find_element(
                        By.CSS_SELECTOR, "div.details-outer dl.single-lines"
                    )
                    all_dts = dl_element.find_elements(By.TAG_NAME, "dt")
                    for dt in all_dts:
                        dt_texts = dt.text.strip().lower()
                        dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        text_value = dd.text.strip()
                        if "type" in dt_texts:
                            current_data["type"] = text_value

                        elif "sra id" in dt_texts:
                            current_data["sra_id"] = text_value.split("|")[0].strip()

                        elif "sra regulated" not in dt_texts:
                            current_data["is_sra_regulated"] = False
                        elif "telephone" in dt_texts:
                            current_data["telephone"] = text_value

                        elif "email" in dt_texts:
                            element = driver.find_element(By.CLASS_NAME, "show-email")
                            email_address = element.get_attribute("data-email")
                            current_data["email"] = email_address
                        elif "web" in dt_texts:
                            current_data["website"] = text_value

                    # Address Part
                    address_box = driver.find_element(By.CLASS_NAME, "multi-line")
                    raw = (
                        address_box.find_element(By.CLASS_NAME, "address")
                        .text.replace("Head office |", "")
                        .strip()
                    )
                    current_data["address_raw"] = raw
                    parts = [p.strip() for p in raw.split(",")]
                    if parts:
                        current_data["city"] = parts[len(parts) - 4]
                        current_data["county"] = parts[len(parts) - 3]
                        current_data["postal_code"] = parts[len(parts) - 2]
                        current_data["country"] = parts[len(parts) - 1]

                    current_data["google_map"] = address_box.find_element(
                        By.CSS_SELECTOR, "a[href*='maps.google']"
                    ).get_attribute("href")

                    # 4. Sections Logic (Structure, Practices, etc.)
                    sections = driver.find_elements(By.TAG_NAME, "section")
                    for sec in sections:

                        title = sec.find_element(By.TAG_NAME, "h2").text.strip().lower()
                    if "people, offices and structure" in title:
                        cols = sec.find_elements(
                            By.CSS_SELECTOR,
                            "div.accordion-inner-body-split-halves > div",
                        )
                        if len(cols) >= 1:
                            org_li = cols[0].find_elements(By.TAG_NAME, "li")
                            current_data["total_people"] = ", ".join(
                                [li.text.replace("\n", " ").strip() for li in org_li]
                            )
                            for li in org_li:
                                if "office" in li.text.lower():
                                    current_data["total_offices"] = li.find_element(
                                        By.TAG_NAME, "strong"
                                    ).text
                        if len(cols) >= 2:
                            for li in cols[1].find_elements(By.TAG_NAME, "li"):
                                txt, num = (
                                    li.text.lower(),
                                    li.find_element(By.TAG_NAME, "strong").text,
                                )
                                if "solicitors" in txt:
                                    current_data["total_solicitors"] = num
                                elif "managers" in txt:
                                    current_data["total_sra_managers"] = num

                    elif "areas of practice" in title:
                        items = [
                            driver.execute_script(
                                "return arguments[0].childNodes[0].textContent.trim();",
                                li,
                            )
                            for li in sec.find_elements(By.TAG_NAME, "li")
                        ]
                        res = ", ".join(filter(None, items))
                        if "branch" in title:
                            current_data["practice_areas_branch"] = res
                        else:
                            current_data["practice_areas_org"] = res

                    elif "accessibility" in title:
                        txt = sec.text.lower()
                        current_data["has_disabled_access"] = "disabled access" in txt
                        current_data["has_induction_loops"] = "induction loops" in txt

                except Exception as e:
                    print(f"Error extracting {link}: {e}")

                # --- REAL TIME SAVE ---
                # Save to CSV
                writer.writerow(current_data)
                f_csv.flush()

                # Update JSON file after every entry
                all_results.append(current_data)
                with open(JSON_FILE, "w", encoding="utf-8") as f_json:
                    json.dump(all_results, f_json, indent=4)

                time.sleep(0.5)  # Prevent blocking

    finally:
        driver.quit()
        print(f"\nDone! Extracted {len(all_results)} firms.")


if __name__ == "__main__":
    main()
