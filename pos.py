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


data = {
    "areas_of_practice_branch": "Missing",
    "areas_of_practice_org": "Missing",
    "accreditations": "Missing",
    "total_people": "Missing",
    "total_solicitors": "Missing",
    "total_sra_managers": "Missing",
    "total_offices": "Missing",
    "languages_at_branch": "Missing",
    "languages_at_org": "Missing",
}

try:
    url = "https://solicitors.lawsociety.org.uk/office/539073/labrums-solicitors-llp"
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    section_fields = driver.find_elements(By.TAG_NAME, "section")

    for section_field in section_fields:
        areas_titles = (
            section_field.find_element(By.TAG_NAME, "h2").text.strip().lower()
        )
        li_elements = section_field.find_elements(By.CSS_SELECTOR, "div.body ul li")

        section_data = []

        if "areas of practice at this branch" in areas_titles:
            branch_list = []
            li_elements = section_field.find_elements(By.CSS_SELECTOR, "div.body ul li")
            for li in li_elements:
                name = driver.execute_script(
                    "return arguments[0].childNodes[0].textContent.trim();", li
                )
                if name:
                    branch_list.append(name)
            data["areas_of_practice_branch"] = ", ".join(branch_list)

        elif "areas of practice at this organisation" in areas_titles:
            org_list = []
            li_elements = section_field.find_elements(By.CSS_SELECTOR, "div.body ul li")
            for li in li_elements:
                name = driver.execute_script(
                    "return arguments[0].childNodes[0].textContent.trim();", li
                )
                if name:
                    org_list.append(name)
            data["areas_of_practice_org"] = ", ".join(org_list)
        elif "languages spoken at this branch" in areas_titles:
            lang_list_branch = []
            li_elements = section_field.find_elements(By.CSS_SELECTOR, "div.body ul li")
            # li_elements = sec.find_elements(By.CSS_SELECTOR, "div.body ul li"
            for li in li_elements:
                lang_name = li.get_attribute("textContent").strip()
                print("lang br", lang_name)
                if lang_name:
                    lang_list_branch.append(lang_name)
            data["languages_at_branch"] = ", ".join(lang_list_branch)

        elif "languages spoken at this organisation" in areas_titles:
            lang_list_org = []
            li_elements = section_field.find_elements(By.CSS_SELECTOR, "div.body ul li")
            for li in li_elements:
                lang_name = li.get_attribute("textContent").strip()
                print("lang org", lang_name)
                if lang_name:
                    lang_list_org.append(lang_name)
            data["languages_at_org"] = ", ".join(lang_list_org)
    print(data, "data")


except Exception as e:
    print(f"Failed to scrape: {e}")

# print("data", data)
