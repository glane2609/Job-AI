from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os

SEEN_FILE = "data/clifford_seen.csv"

# -------------------------------
# Persistent seen storage
# -------------------------------
def load_seen():
    if os.path.exists(SEEN_FILE):
        return set(pd.read_csv(SEEN_FILE)["job_id"].astype(str))
    return set()

def save_seen(ids):
    os.makedirs("data", exist_ok=True)
    pd.DataFrame({"job_id": list(ids)}).to_csv(SEEN_FILE, index=False)

# -------------------------------
# Create Chrome
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
    return driver

# -------------------------------
# Breadcrumb location
# -------------------------------
def extract_location(driver):
    try:
        items = driver.find_elements(By.XPATH, '//*[@id="506ab26f-a08d-47ed-acc8-80ac556e8636"]/ol/li')
        blacklist = ["permanent", "temporary", "contract", "full", "part", "fixed", "term"]

        for li in items:
            txt = li.get_attribute("innerText").strip()
            if txt and not any(b in txt.lower() for b in blacklist):
                return txt
    except:
        pass
    return ""

# -------------------------------
# Wait until jobs fully rendered
# -------------------------------
def wait_for_jobs(driver):
    WebDriverWait(driver, 40).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "attrax-vacancy-tile"))
    )
    WebDriverWait(driver, 40).until(
        lambda d: any(
            el.get_attribute("innerText").strip() != ""
            for el in d.find_elements(By.CLASS_NAME, "attrax-vacancy-tile__title")
        )
    )

# -------------------------------
# Scrape one portal
# -------------------------------
def scrape_clifford(url):
    driver = create_driver()
    seen_ids = load_seen()

    try:
        driver.get(url)
        wait_for_jobs(driver)

        # Swiper pagination – keep clicking until nothing new loads
        last_count = 0
        while True:
            tiles = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")
            if len(tiles) == last_count:
                break
            last_count = len(tiles)
            try:
                btn = driver.find_element(By.CLASS_NAME, "swiper-button-next")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.2)
                wait_for_jobs(driver)
            except:
                break

        jobs = []

        for tile in driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile"):
            try:
                job_id = tile.get_attribute("data-jobid")
                if not job_id:
                    continue

                try:
                    t = tile.find_element(By.CLASS_NAME, "attrax-vacancy-tile__title")
                    title = t.get_attribute("innerText").strip()
                    url_job = t.get_attribute("href")
                except:
                    title = ""
                    url_job = ""

                try:
                    location = tile.find_element(
                        By.CSS_SELECTOR,
                        ".attrax-vacancy-tile__option-location .attrax-vacancy-tile__item-value"
                    ).get_attribute("innerText").strip()
                except:
                    location = ""

                jobs.append({
                    "job_id": str(job_id),
                    "title": title,
                    "location": location,
                    "url": url_job
                })
            except:
                pass

        df = pd.DataFrame(jobs).drop_duplicates(subset=["job_id"])

        # Enrich only missing rows
        for i, row in df.iterrows():
            if row["title"] and row["location"]:
                continue
            try:
                driver.get(row["url"])
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

                if not row["title"]:
                    df.loc[i, "title"] = driver.find_element(By.TAG_NAME, "h1").get_attribute("innerText").strip()

                if not row["location"]:
                    loc = extract_location(driver)
                    if loc:
                        df.loc[i, "location"] = loc
            except:
                pass

        # Update seen
        all_seen = seen_ids.union(set(df["job_id"]))
        save_seen(all_seen)

        return df

    finally:
        driver.quit()

# -------------------------------
# Run all portals
# -------------------------------
def run_clifford():
    portals = {
        "Experienced_Lawyers": "https://jobs.cliffordchance.com/experienced-lawyers",
        "Business_Professionals": "https://jobs.cliffordchance.com/business-professionals",
        "Early_Careers": "https://jobs.cliffordchance.com/early-careers"
    }

    results = {}

    for name, url in portals.items():
        print(f"Scraping {name}…")

        for attempt in range(6):
            df = scrape_clifford(url)

            # Must have no empty titles
            if (df["title"].astype(str).str.strip() != "").all():
                print(f"{name} OK")
                break
            else:
                print(f"{name} incomplete, retrying…")
                time.sleep(2)

        results[name] = df.to_dict("records")

    return results
