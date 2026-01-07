from fastapi import FastAPI
from Clifford_chance import run_clifford
from tower import run_tower

app = FastAPI(title="Job Intelligence API")

@app.get("/")
def home():
    return {"status": "Job API is running"}

@app.get("/clifford")
def clifford():
    data = run_clifford()

    # Convert DataFrames to JSON
    return {
        "Experienced_Lawyers": data["Experienced_Lawyers"].to_dict(orient="records"),
        "Business_Professionals": data["Business_Professionals"].to_dict(orient="records"),
        "Early_Careers": data["Early_Careers"].to_dict(orient="records")
    }

@app.get("/tower")
def tower():
    df = run_tower()
    return df.to_dict(orient="records")
