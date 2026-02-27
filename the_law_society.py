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
        "trading_names": "Missing",
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
        "areas_of_practice_branch": "Missing",
        "areas_of_practice_org": "Missing",
        "people_office_struct_org": "Missing",
        "people_office_struct_office": "Missing",
        "languages_at_branch": "Missing",
        "languages_at_org": "Missing",
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

            WebDriverWait(driver, 40).until(
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
                    WebDriverWait(driver, 30).until(
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
                            try:
                                email_elem = dd.find_element(
                                    By.CLASS_NAME, "show-email"
                                )
                                current_data["email"] = email_elem.get_attribute(
                                    "data-email"
                                )
                            except:
                                current_data["email"] = "Not Found"
                        elif "web" in label:
                            current_data["website"] = value
                        if "SRA Regulated" in driver.page_source:
                            current_data["is_sra_regulated"] = True
                        else:
                            current_data["is_sra_regulated"] = False

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
                    section_fields = driver.find_elements(By.TAG_NAME, "section")

                    for section_field in section_fields:
                        headers = section_field.find_elements(By.TAG_NAME, "h2")
                        if not headers:
                            continue

                        areas_titles = headers[0].text.strip().lower()
                        # areas_titles = (
                        #     section_field.find_elements(By.TAG_NAME, "h2")
                        #     .text.strip()
                        #     .lower()
                        # )
                        li_elements = section_field.find_elements(
                            By.CSS_SELECTOR, "div.body ul li"
                        )

                        if "areas of practice at this branch" in areas_titles:
                            branch_list = []
                            li_elements = section_field.find_elements(
                                By.CSS_SELECTOR, "div.body ul li"
                            )
                            for li in li_elements:
                                name = driver.execute_script(
                                    "return arguments[0].childNodes[0].textContent.trim();",
                                    li,
                                )
                                if name:
                                    branch_list.append(name)
                            current_data["areas_of_practice_branch"] = ", ".join(
                                branch_list
                            )

                        elif "areas of practice at this organisation" in areas_titles:
                            org_list = []
                            li_elements = section_field.find_elements(
                                By.CSS_SELECTOR, "div.body ul li"
                            )
                            for li in li_elements:
                                name = driver.execute_script(
                                    "return arguments[0].childNodes[0].textContent.trim();",
                                    li,
                                )
                                if name:
                                    org_list.append(name)
                            current_data["areas_of_practice_org"] = ", ".join(org_list)
                        elif "people, offices and structure" in areas_titles:
                            halves = section_field.find_elements(
                                By.CSS_SELECTOR,
                                "div.accordion-inner-body-split-halves > div",
                            )
                            if len(halves) >= 1:
                                org_list = []
                                org_li_elements = halves[0].find_elements(
                                    By.TAG_NAME, "li"
                                )
                                for li in org_li_elements:
                                    raw_text = li.get_attribute("textContent")
                                    clean_item = (
                                        " ".join(raw_text.split())
                                        .replace("in this organisation", "")
                                        .strip()
                                    )
                                    if clean_item:
                                        org_list.append(clean_item)
                                        current_data["people_office_struct_org"] = (
                                            ", ".join(org_list)
                                        )

                            if len(halves) >= 2:
                                off_list = []
                                off_li = halves[1].find_elements(By.TAG_NAME, "li")
                                for li in off_li:
                                    txt = li.get_attribute("textContent")
                                    clean = (
                                        " ".join(txt.split())
                                        .replace("at this office", "")
                                        .strip()
                                    )
                                    if clean:
                                        off_list.append(clean)

                                current_data["people_office_struct_office"] = ", ".join(
                                    off_list
                                )
                        elif "languages spoken at this branch" in areas_titles:
                            lang_list_branch = []
                            li_elements = section_field.find_elements(
                                By.CSS_SELECTOR, "div.body ul li"
                            )
                            for li in li_elements:
                                lang_name = li.get_attribute("textContent").strip()
                                # print("lang br", lang_name)
                                if lang_name:
                                    lang_list_branch.append(lang_name)
                            current_data["languages_at_branch"] = ", ".join(
                                lang_list_branch
                            )

                        elif "languages spoken at this organisation" in areas_titles:
                            lang_list_org = []
                            li_elements = section_field.find_elements(
                                By.CSS_SELECTOR, "div.body ul li"
                            )
                            for li in li_elements:
                                lang_name = li.get_attribute("textContent").strip()
                                # print("lang org", lang_name)
                                if lang_name:
                                    lang_list_org.append(lang_name)
                            current_data["languages_at_org"] = ", ".join(lang_list_org)

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
