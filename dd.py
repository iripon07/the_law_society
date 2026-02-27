import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
CSV_FILE = "law_society_data.csv"
JSON_FILE = "law_society_data.json"
START_URL = "https://solicitors.lawsociety.org.uk/search/results?Pro=True&Location=London+Colney"

chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)


def safe_get(url, retries=3):
    """Attempt to load a page multiple times if internet fails."""
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"   Retry {i+1}/{retries} failed for {url}...")
            time.sleep(5)  # Wait 5 seconds before trying again
    return False


def scrape_organization(url):
    # Blueprint
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
        # "accreditations": "Missing",
        # "total_people": "Missing",
        # "total_solicitors": "Missing",
        # "total_sra_managers": "Missing",
        # "total_offices": "Missing",
        # "has_disabled_access": False,
        # "has_induction_loops": False,
        # "accepts_legal_aid": False,
        # "provides_sign_language": False,
    }

    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # --- Extraction Logic ---
        data["firm_name"] = driver.find_element(
            By.CSS_SELECTOR, "header h1"
        ).text.strip()

        # Sidebar Details
        try:
            dl = driver.find_element(
                By.CSS_SELECTOR, "div.details-outer dl.single-lines"
            )
            for dt in dl.find_elements(By.TAG_NAME, "dt"):
                lbl = dt.text.lower()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                if "type" in lbl:
                    data["type"] = dd.text.strip()
                elif "sra id" in lbl:
                    data["sra_id"] = dd.text.split("|")[0].strip()
                    if "not regulated" in dd.text.lower():
                        data["is_sra_regulated"] = False
                elif "telephone" in lbl:
                    data["telephone"] = dd.text.strip()
                elif "web" in lbl:
                    data["website"] = dd.text.strip()
                elif "email" in lbl:
                    try:
                        data["email"] = dd.find_element(By.TAG_NAME, "a").get_attribute(
                            "data-email"
                        )
                    except:
                        data["email"] = dd.text.strip()
        except:
            pass

        # Address Logic
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

        # Sections (Structure, Practices, etc.)
        sections = driver.find_elements(By.TAG_NAME, "section")
        for sec in sections:
            try:
                title_el = sec.find_elements(By.TAG_NAME, "h2")
                if not title_el:
                    continue
                title = title_el[0].text.strip().lower()

                if "people, offices and structure" in title:
                    columns = sec.find_elements(
                        By.CSS_SELECTOR, "div.accordion-inner-body-split-halves > div"
                    )
                    if len(columns) >= 1:
                        org_li = columns[0].find_elements(By.TAG_NAME, "li")
                        data["total_people"] = ", ".join(
                            [li.text.replace("\n", " ").strip() for li in org_li]
                        )
                        for li in org_li:
                            if "office" in li.text.lower():
                                data["total_offices"] = li.find_element(
                                    By.TAG_NAME, "strong"
                                ).text
                    if len(columns) >= 2:
                        for li in columns[1].find_elements(By.TAG_NAME, "li"):
                            txt, num = (
                                li.text.lower(),
                                li.find_element(By.TAG_NAME, "strong").text,
                            )
                            if "solicitors" in txt:
                                data["total_solicitors"] = num
                            elif "managers" in txt:
                                data["total_sra_managers"] = num

                elif "areas of practice" in title:
                    items = [
                        driver.execute_script(
                            "return arguments[0].childNodes[0].textContent.trim();", li
                        )
                        for li in sec.find_elements(By.CSS_SELECTOR, "div.body ul li")
                    ]
                    res = ", ".join(filter(None, items))
                    if "branch" in title:
                        data["areas_of_practice_branch"] = res
                    else:
                        data["areas_of_practice_org"] = res

            except:
                continue
    except Exception as e:
        print(f"Parsing error on {url}: {e}")
    return data


def main():
    results = []
    headers = list(scrape_organization(None).keys())

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        current_search_page = START_URL
        while current_search_page:
            print(f"Navigating to search page: {current_search_page}")
            if not safe_get(current_search_page):
                break  # Exit if search page won't load

            # Get links
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            )
            h2_elements = driver.find_elements(By.TAG_NAME, "h2")
            page_links = []
            for h2 in h2_elements:
                try:
                    href = h2.find_element(By.TAG_NAME, "a").get_attribute("href")
                    if "/office/" in href:
                        page_links.append(href)
                except:
                    continue

            # Scrape links
            for link in page_links:
                print(f"   Processing: {link}")
                row = scrape_organization(link)
                writer.writerow(row)
                f.flush()
                results.append(row)
                time.sleep(1)

            # Find Next Page
            try:
                # Must go back to search results if profile scraping changed the URL
                safe_get(current_search_page)
                next_btn = driver.find_element(
                    By.XPATH, "//a[contains(text(), 'Next')]"
                )
                current_search_page = next_btn.get_attribute("href")
            except:
                print("Final page reached.")
                current_search_page = None

    with open(JSON_FILE, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=4)

    driver.quit()


if __name__ == "__main__":
    main()
