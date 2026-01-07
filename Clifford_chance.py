from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd

# -------------------------------
# Create Chrome per scrape
# -------------------------------
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)
    return driver, wait


# -------------------------------
# Breadcrumb location extractor
# -------------------------------
def extract_location(driver):
    try:
        items = driver.find_elements(By.XPATH, '//*[@id="506ab26f-a08d-47ed-acc8-80ac556e8636"]/ol/li')
        blacklist = ["permanent", "temporary", "contract", "full", "part", "fixed", "term"]

        for li in items:
            txt = li.text.strip()
            if txt and not any(b in txt.lower() for b in blacklist):
                return txt
    except:
        pass
    return ""


# -------------------------------
# Scrape one Clifford portal
# -------------------------------
def scrape_clifford(url):
    driver, wait = create_driver()

    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "attrax-vacancy-tile")))

        seen = set()

        # ---------- Swiper Pagination Fix ----------
        while True:
            tiles = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")

            for t in tiles:
                jid = t.get_attribute("data-jobid")
                if jid:
                    seen.add(jid)

            prev = len(seen)

            try:
                btn = driver.find_element(By.CLASS_NAME, "swiper-button-next")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.2)
            except:
                break

            tiles_after = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")
            new_ids = {t.get_attribute("data-jobid") for t in tiles_after if t.get_attribute("data-jobid")}

            if len(new_ids) == prev:
                break

        # ---------- Extract jobs ----------
        jobs = []

        for tile in driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile"):
            try:
                job = {}
                job["job_id"] = tile.get_attribute("data-jobid")

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

                jobs.append(job)
            except:
                pass

        df = pd.DataFrame(jobs)

        # ---------- Enrich missing fields ----------
        for i, row in df.iterrows():
            if row["title"] == "" or row["location"] == "":
                try:
                    driver.get(row["url"])
                    wait.until(EC.presence_of_element_located((By.ID, "headertext")))

                    try:
                        df.at[i, "title"] = driver.find_element(By.ID, "headertext").text.strip()
                    except:
                        pass

                    try:
                        df.at[i, "location"] = extract_location(driver)
                    except:
                        pass
                except:
                    pass

        return df.drop_duplicates(subset=["job_id"])

    finally:
        driver.quit()


# -------------------------------
# Run all Clifford portals
# -------------------------------
def run_clifford():
    portals = {
        "Experienced_Lawyers": "https://jobs.cliffordchance.com/experienced-lawyers",
        "Business_Professionals": "https://jobs.cliffordchance.com/business-professionals",
        "Early_Careers": "https://jobs.cliffordchance.com/early-careers"
    }

    results = {}

    for name, url in portals.items():
        print(f"Scraping {name}...")
        results[name] = scrape_clifford(url).to_dict("records")

    return results
