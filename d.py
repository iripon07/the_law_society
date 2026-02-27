# 1. Initialize empty lists at the TOP of the loop
section_fields = driver.find_elements(By.TAG_NAME, "section")

for section_field in section_fields:
    # Safely get the title
    try:
        areas_titles = (
            section_field.find_element(By.TAG_NAME, "h2").text.strip().lower()
        )
    except:
        continue


    # --- LANGUAGES ---
    
