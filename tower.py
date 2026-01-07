import requests
import pandas as pd

def run_tower():

    url = "https://boards-api.greenhouse.io/v1/boards/towerresearchcapital/jobs"
    data = requests.get(url).json()

    rows = []

    for j in data["jobs"]:
        rows.append([
            j["id"],
            j["title"],
            j["location"]["name"],
            j["absolute_url"]
        ])

    df = pd.DataFrame(rows, columns=["id", "title", "location", "url"])
    return df
