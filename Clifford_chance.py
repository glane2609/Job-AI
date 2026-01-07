from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# -------------------------------
# Browser Setup
# -------------------------------
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")      # Chrome 109+ headless
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# -------------------------------
# Smart breadcrumb location parser
# -------------------------------
def extract_location_from_breadcrumb(driver):
    blacklist = ["permanent", "temporary", "contract", "fixed", "full", "part", "term"]

    try:
        items = driver.find_elements(
            By.XPATH,
            '//*[@id="506ab26f-a08d-47ed-acc8-80ac556e8636"]/ol/li'
        )
    except:
        return ""

    for li in items:
        try:
            raw = li.text.strip()
            if not raw:
                continue

            txt = raw.lower()

            # Skip contract-type words
            if any(word in txt for word in blacklist):
                continue

            return raw
        except:
            continue

    return ""



# -------------------------------
# Core scraper for a single portal
# -------------------------------
def scrape_portal(portal_name, url):
    print(f"\n🔍 Scraping: {portal_name}")

    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "attrax-vacancy-tile")))

    seen = set()
    jobs = []

    # ------------------------------
    # Step 1 — Swipe through tiles
    # ------------------------------
    while True:
        tiles = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")

        for tile in tiles:
            try:
                job_id = tile.get_attribute("data-jobid")
                if not job_id or job_id in seen:
                    continue
                seen.add(job_id)

                job = {}
                job["job_id"] = job_id

                try:
                    title_el = tile.find_element(By.CLASS_NAME, "attrax-vacancy-tile__title")
                    job["title"] = title_el.text.strip()
                    job["url"] = title_el.get_attribute("href")
                except:
                    job["title"] = ""
                    job["url"] = ""

                try:
                    job["location"] = tile.find_element(
                        By.CSS_SELECTOR,
                        ".attrax-vacancy-tile__option-location .attrax-vacancy-tile__item-value"
                    ).text.strip()
                except:
                    job["location"] = ""

                try:
                    job["department"] = tile.find_element(
                        By.CSS_SELECTOR,
                        ".attrax-vacancy-tile__option-department .attrax-vacancy-tile__item-value"
                    ).text.strip()
                except:
                    job["department"] = ""

                jobs.append(job)

            except:
                pass

        try:
            next_btn = driver.find_element(By.CLASS_NAME, "swiper-button-next")
            if "swiper-button-disabled" in next_btn.get_attribute("class"):
                break
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(1)
        except:
            break

    # ------------------------------
    # Step 2 — Enrich missing fields
    # ------------------------------
    for job in jobs:
        if job["title"] == "" or job["location"] == "":
            driver.get(job["url"])
            wait.until(EC.presence_of_element_located((By.ID, "headertext")))

            try:
                job["title"] = driver.find_element(By.ID, "headertext").text.strip()
            except:
                pass

            try:
                job["location"] = extract_location_from_breadcrumb(driver)
            except:
                pass

    df = pd.DataFrame(jobs, columns=["job_id", "title", "location", "url"])
    print(f"✔ {portal_name}: {len(df)} jobs")

    return df


# -------------------------------
# Run for all portals
# -------------------------------
PORTALS = {
    "Experienced_Lawyers": "https://jobs.cliffordchance.com/experienced-lawyers",
    "Business_Professionals": "https://jobs.cliffordchance.com/business-professionals",
    "Early_Careers": "https://jobs.cliffordchance.com/early-careers"
}

results = {}

for name, link in PORTALS.items():
    results[name] = scrape_portal(name, link)

# -------------------------------
# Separate DataFrames
# -------------------------------
df_experienced = results["Experienced_Lawyers"]
df_business    = results["Business_Professionals"]
df_early       = results["Early_Careers"]

def run_clifford():
    return {
        "Experienced_Lawyers": df_experienced,
        "Business_Professionals": df_business,
        "Early_Careers": df_early
    }
