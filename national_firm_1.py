import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
chrome_options = Options()
# chrome_options.add_argument("--headless") # Recommended for large scrapes
driver = webdriver.Chrome(options=chrome_options)

CSV_FILE = "law_society_data.csv"
JSON_FILE = "law_society_data.json"


def scrape_organization(url):
    data = {
        "firm_name": "Missing",
        "type": "Missing",
        "sra_id": "Missing",
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
        "languages_at_branch": "Missing",
        "languages_at_org": "Missing",
        "accreditations": "Missing",
        "total_people": "Missing",
        "total_solicitors": "Missing",
        "total_sra_managers": "Missing",
        "total_offices": "Missing",
        "has_disabled_access": False,
        "has_induction_loops": False,
        "accepts_legal_aid": False,
        "provides_sign_language": False,
    }

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # 1. Header Info
        data["firm_name"] = driver.find_element(
            By.CSS_SELECTOR, "header h1"
        ).text.strip()

        # 2. Sidebar Details
        try:
            dl = driver.find_element(
                By.CSS_SELECTOR, "div.details-outer dl.single-lines"
            )
            for dt in dl.find_elements(By.TAG_NAME, "dt"):
                lbl = dt.text.lower()
                val = dt.find_element(By.XPATH, "following-sibling::dd[1]").text.strip()
                if "type" in lbl:
                    data["type"] = val
                elif "sra id" in lbl:
                    data["sra_id"] = val.split("|")[0].strip()
                    if "not regulated" in val.lower():
                        data["is_sra_regulated"] = False
                elif "telephone" in lbl:
                    data["telephone"] = val
                elif "web" in lbl:
                    data["website"] = val
                elif "email" in lbl:
                    try:
                        data["email"] = dt.find_element(
                            By.XPATH, "following-sibling::dd[1]//a"
                        ).get_attribute("data-email")
                    except:
                        data["email"] = val
        except:
            pass

        # 3. Address Parsing
        try:
            addr_box = driver.find_element(By.CLASS_NAME, "multi-line")
            raw = (
                addr_box.find_element(By.CLASS_NAME, "address")
                .text.replace("Head office |", "")
                .strip()
            )
            data["address_raw"] = raw
            pts = [p.strip() for p in raw.split(",")]
            if len(pts) >= 1:
                data["country"] = pts[-1]
            if len(pts) >= 2:
                data["postal_code"] = pts[-2]
            if len(pts) >= 3:
                data["county"] = pts[-3]
            if len(pts) >= 4:
                data["city"] = pts[-4]
            data["google_map"] = addr_box.find_element(
                By.CSS_SELECTOR, "a[href*='maps.google']"
            ).get_attribute("href")
        except:
            pass

        # 4. Sections Logic
        sections = driver.find_elements(By.TAG_NAME, "section")
        for sec in sections:
            try:
                title = sec.find_element(By.TAG_NAME, "h2").text.strip().lower()

                # People, Offices & Structure (Your new logic)
                if "people, offices and structure" in title:
                    columns = sec.find_elements(
                        By.CSS_SELECTOR, "div.accordion-inner-body-split-halves > div"
                    )
                    if len(columns) >= 1:  # Organisation side
                        org_li = columns[0].find_elements(By.TAG_NAME, "li")
                        data["total_people"] = ", ".join(
                            [li.text.replace("\n", " ").strip() for li in org_li]
                        )
                        # Extra extraction for specific counts
                        for li in org_li:
                            txt = li.text.lower()
                            if "office" in txt:
                                data["total_offices"] = li.find_element(
                                    By.TAG_NAME, "strong"
                                ).text

                    if len(columns) >= 2:  # Office side
                        off_li = columns[1].find_elements(By.TAG_NAME, "li")
                        for li in off_li:
                            txt = li.text.lower()
                            num = li.find_element(By.TAG_NAME, "strong").text
                            if "solicitors" in txt:
                                data["total_solicitors"] = num
                            elif "managers" in txt:
                                data["total_sra_managers"] = num

                # Practices & Languages
                elif "areas of practice" in title or "languages" in title:
                    items = []
                    for li in sec.find_elements(By.CSS_SELECTOR, "div.body ul li"):
                        val = (
                            driver.execute_script(
                                "return arguments[0].childNodes[0].textContent.trim();",
                                li,
                            )
                            if "areas" in title
                            else li.text.strip()
                        )
                        if val:
                            items.append(val)
                    res = ", ".join(items)
                    if "areas" in title and "branch" in title:
                        data["areas_of_practice_branch"] = res
                    elif "areas" in title and "organisation" in title:
                        data["areas_of_practice_org"] = res
                    elif "languages" in title and "branch" in title:
                        data["languages_at_branch"] = res
                    elif "languages" in title and "organisation" in title:
                        data["languages_at_org"] = res

                # Accreditations
                elif "accreditations" in title:
                    accs = [
                        li.text.strip() for li in sec.find_elements(By.TAG_NAME, "li")
                    ]
                    data["accreditations"] = ", ".join(accs)

                # Accessibility (Booleans)
                elif "accessibility" in title:
                    txt = sec.text.lower()
                    data["has_disabled_access"] = "disabled access" in txt
                    data["has_induction_loops"] = "induction loops" in txt
                    data["provides_sign_language"] = "sign language" in txt

            except:
                continue

    except Exception as e:
        print(f"URL Error: {e}")
    return data


# --- EXECUTION ---
def main():
    urls = ["https://solicitors.lawsociety.org.uk/office/539073/labrums-solicitors-llp"]
    results = []
    headers = list(scrape_organization(None).keys())

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for i, url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}] Scraping: {url}")
            row = scrape_organization(url)
            writer.writerow(row)
            f.flush()  # Save CSV row-by-row
            results.append(row)
            time.sleep(1)

    with open(JSON_FILE, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=4)

    driver.quit()
    print(f"Complete! CSV and JSON updated.")


if __name__ == "__main__":
    main()
