from fastapi import FastAPI
from Clifford_chance import run_clifford
from tower import run_tower
import json
import os

app = FastAPI()

CACHE_FILE = "clifford_cache.json"

@app.get("/")
def home():
    return {"status": "Job API is running"}

@app.get("/tower")
def tower():
    df = run_tower()
    return df.to_dict(orient="records")

@app.get("/clifford")
def clifford():
    try:
        data = run_clifford()

        # Convert DataFrames to JSON
        payload = {
            "Experienced_Lawyers": data["Experienced_Lawyers"].to_dict(orient="records"),
            "Business_Professionals": data["Business_Professionals"].to_dict(orient="records"),
            "Early_Careers": data["Early_Careers"].to_dict(orient="records")
        }

        # Save cache
        with open(CACHE_FILE, "w") as f:
            json.dump(payload, f)

        return payload

    except Exception as e:
        # If Selenium crashes, return last known good data
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        else:
            return {"error": "Clifford scraping failed and no cache exists"}


@app.get("/tower")
def tower():
    df = run_tower()
    return df.to_dict(orient="records")
