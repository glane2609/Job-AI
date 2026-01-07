from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd


# -------------------------------
# Create Chrome safely (Streamlit Cloud compatible)
# -------------------------------
def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Do NOT set binary_location – let Selenium auto-detect Chromium
    service = Service()

    return webdriver.Chrome(service=service, options=options)


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
            if any(word in txt for word in blacklist):
                continue
            return raw
        except:
            continue

    return ""


# -------------------------------
# Scrape one portal
# -------------------------------
def scrape_portal(driver, wait, portal_name, url):

    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "attrax-vacancy-tile")))

    seen = set()
    jobs = []

    while True:
        tiles = driver.find_elements(By.CLASS_NAME, "attrax-vacancy-tile")

        for tile in tiles:
            try:
                job_id = tile.get_attribute("data-jobid")
                if not job_id or job_id in seen:
                    continue
                seen.add(job_id)

                job = {"job_id": job_id}

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

        try:
            next_btn = driver.find_element(By.CLASS_NAME, "swiper-button-next")
            if "swiper-button-disabled" in next_btn.get_attribute("class"):
                break
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(1)
        except:
            break

    # Enrich missing fields
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

    return pd.DataFrame(jobs, columns=["job_id", "title", "location", "url"])


# -------------------------------
# PUBLIC FUNCTION (called by Streamlit)
# -------------------------------
def run_clifford():

    PORTALS = {
        "Experienced_Lawyers": "https://jobs.cliffordchance.com/experienced-lawyers",
        "Business_Professionals": "https://jobs.cliffordchance.com/business-professionals",
        "Early_Careers": "https://jobs.cliffordchance.com/early-careers"
    }

    driver = get_driver()
    wait = WebDriverWait(driver, 20)

    results = {}

    for name, link in PORTALS.items():
        results[name] = scrape_portal(driver, wait, name, link)

    driver.quit()

    return results
