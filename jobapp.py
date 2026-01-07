import streamlit as st
import pandas as pd
import os
import requests

# -------------------------------
# Safe API fetch
# -------------------------------
def safe_api_get(url):
    try:
        r = requests.get(url, timeout=120)
        if r.status_code != 200:
            st.error(f"API error {r.status_code} while calling {url}")
            return None
        return r.json()
    except Exception as e:
        st.error(f"API call failed: {e}")
        return None

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Job Intelligence Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# Gradient UI
# -------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}
h1, h2, h3 {
    color: white;
}
.stButton>button {
    background-color: #00c6ff;
    color: black;
    font-weight: bold;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>📊 Live Hiring Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>Clifford Chance & Tower Research</h4>", unsafe_allow_html=True)
st.divider()

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------
# Dedup storage
# -------------------------------
def diff_and_store(df_live, file):
    path = f"{DATA_DIR}/{file}"

    if os.path.exists(path):
        df_old = pd.read_csv(path)
    else:
        df_old = pd.DataFrame(columns=df_live.columns)

    key = df_live.columns[0]

    df_new = df_live[~df_live[key].astype(str).isin(df_old[key].astype(str))]
    final = pd.concat([df_old, df_new], ignore_index=True)
    final.to_csv(path, index=False)

    return final, len(df_new)

# -------------------------------
# API base URL
# -------------------------------
API = "https://job-ai-chf4.onrender.com"

source = st.selectbox("Select Hiring Source", ["Clifford Chance", "Tower Research"])

if st.button("🚀 Run Live Scan"):

    # ============================
    # Tower Research
    # ============================
    if source == "Tower Research":

        with st.spinner("🔍 Scanning Tower Research careers portal..."):
            data = safe_api_get(f"{API}/tower")

        if data is None:
            st.stop()

        df_live = pd.DataFrame(data)
        total_found = len(df_live)

        df, new_count = diff_and_store(df_live, "tower.csv")

        st.markdown("### 📊 Tower Research Results")
        st.markdown(f"**Total roles currently listed:** `{total_found}`")

        if new_count > 0:
            st.success(f"🆕 {new_count} new Tower jobs detected!")
        else:
            st.info("No new Tower jobs since last scan")

        df["url"] = df["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ============================
    # Clifford Chance
    # ============================
    else:

        with st.spinner("🔍 Scanning Clifford Chance global careers site..."):
            data = safe_api_get(f"{API}/clifford")

        if data is None:
            st.stop()

        st.markdown("## ⚖️ Clifford Chance Hiring Status")

        tabs = st.tabs(["Experienced Lawyers", "Business Professionals", "Early Careers"])

        mapping = {
            "Experienced Lawyers": ("Experienced_Lawyers", "clifford_experienced.csv"),
            "Business Professionals": ("Business_Professionals", "clifford_business.csv"),
            "Early Careers": ("Early_Careers", "clifford_early.csv")
        }

        for i, (label, (api_key, file_name)) in enumerate(mapping.items()):
            with tabs[i]:

                jobs = data.get(api_key, [])

                if not jobs:
                    st.warning("No roles returned from API for this category")
                    continue

                df_live = pd.DataFrame(jobs)
                total_found = len(df_live)

                df, new_count = diff_and_store(df_live, file_name)

                st.markdown(f"**Total roles currently listed:** `{total_found}`")

                if new_count > 0:
                    st.success(f"🆕 {new_count} new roles detected!")
                else:
                    st.info("No new roles since last scan")

                df["url"] = df["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
