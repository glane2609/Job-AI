from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
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

def is_complete(df):
    # At least 95% of jobs must have titles
    if len(df) == 0:
        return False
    filled = df["title"].astype(str).str.strip().ne("").sum()
    return (filled / len(df)) > 0.95


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
    return driver


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
    driver = create_driver()
    seen_ids = load_seen()

    try:
        driver.get(url)
        time.sleep(3)

        tiles = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")

        # Swiper pagination
        while True:
            try:
                btn = driver.find_element(By.CLASS_NAME, "swiper-button-next")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.2)
                tiles_new = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")
                if len(tiles_new) == len(tiles):
                    break
                tiles = tiles_new
            except:
                break

        jobs = []

        for tile in tiles:
            try:
                job_id = tile.get_attribute("data-jobid")
                if not job_id:
                    continue

                title = ""
                url_job = ""
                location = ""

                try:
                    t = tile.find_element(By.CLASS_NAME, "attrax-vacancy-tile__title")
                    title = t.text.strip()
                    url_job = t.get_attribute("href")
                except:
                    pass

                try:
                    location = tile.find_element(
                        By.CSS_SELECTOR,
                        ".attrax-vacancy-tile__option-location .attrax-vacancy-tile__item-value"
                    ).text.strip()
                except:
                    pass

                jobs.append({
                    "job_id": str(job_id),
                    "title": title,
                    "location": location,
                    "url": url_job
                })
            except:
                pass

        df = pd.DataFrame(jobs)

        # Identify NEW jobs only
        df_new = df[~df["job_id"].isin(seen_ids)]

        # Enrich only NEW jobs
        for i, row in df_new.iterrows():
            try:
                driver.get(row["url"])
                time.sleep(2.5)

                if not row["title"]:
                    try:
                        df.loc[df["job_id"] == row["job_id"], "title"] = driver.find_element(By.TAG_NAME, "h1").text.strip()
                    except:
                        pass

                if not row["location"]:
                    loc = extract_location(driver)
                    if loc:
                        df.loc[df["job_id"] == row["job_id"], "location"] = loc
            except:
                pass

        # Save updated seen list
        all_seen = seen_ids.union(set(df["job_id"]))
        save_seen(all_seen)

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
        print(f"Scraping {name}…")

        for attempt in range(5):  # retry up to 5 times
            df = scrape_clifford(url)

            if is_complete(df):
                print(f"{name}: OK on attempt {attempt+1}")
                break
            else:
                print(f"{name}: incomplete, retrying...")
                time.sleep(2)

        results[name] = df.to_dict("records")

    return results

