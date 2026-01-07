import streamlit as st
import pandas as pd
import os

from Clifford_chance import run_clifford
from tower import run_tower


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
h1, h2, h3, h4 {
    color: white;
}
.stButton>button {
    background-color: #00c6ff;
    color: black;
    font-weight: bold;
    border-radius: 8px;
}
.stSelectbox label {
    color: white !important;
}
table {
    color: black;
    background-color: white;
}
</style>
""", unsafe_allow_html=True)


# -------------------------------
# Header
# -------------------------------
st.markdown(
    "<h1 style='text-align:center;'>📊 Live Hiring Intelligence Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<h4 style='text-align:center;'>Track Clifford Chance & Tower Research in real time</h4>",
    unsafe_allow_html=True
)

st.divider()


# -------------------------------
# Storage folder
# -------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


# -------------------------------
# Deduplicating Append Logic
# -------------------------------
def diff_and_store(df_live, file):
    path = f"{DATA_DIR}/{file}"

    if os.path.exists(path):
        df_old = pd.read_csv(path)
    else:
        df_old = pd.DataFrame(columns=df_live.columns)

    key = df_live.columns[0]  # job_id or id

    old_ids = set(df_old[key].astype(str))
    live_ids = set(df_live[key].astype(str))

    # Only truly new jobs
    df_new = df_live[~df_live[key].astype(str).isin(old_ids)]

    # Append new jobs to historical dataset
    final = pd.concat([df_old, df_new], ignore_index=True)

    final.to_csv(path, index=False)

    return final, len(df_new)


# -------------------------------
# Company Selector
# -------------------------------
source = st.selectbox("Select Hiring Source", ["Clifford Chance", "Tower Research"])

st.divider()


# -------------------------------
# Run Button
# -------------------------------
if st.button("🚀 Run Live Scan"):

    if source == "Tower Research":

        with st.spinner("Scanning Tower Research…"):
            df_live = run_tower()

        df, new_count = diff_and_store(df_live, "tower.csv")

        if new_count > 0:
            st.success(f"🆕 {new_count} new Tower jobs added!")
        else:
            st.info("No new Tower jobs found")

        df_display = df.copy()
        df_display["url"] = df_display["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')

        st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)


    else:

        with st.spinner("Scanning Clifford Chance…"):
            data = run_clifford()

        tabs = st.tabs([
            "Experienced Lawyers",
            "Business Professionals",
            "Early Careers"
        ])

        mapping = {
            "Experienced Lawyers": ("Experienced_Lawyers", "clifford_experienced.csv"),
            "Business Professionals": ("Business_Professionals", "clifford_business.csv"),
            "Early Careers": ("Early_Careers", "clifford_early.csv")
        }

        for tab, key in zip(tabs, mapping):
            with tab:
                df_live = data[mapping[key][0]]
                df, new_count = diff_and_store(df_live, mapping[key][1])

                if new_count > 0:
                    st.success(f"🆕 {new_count} new jobs added!")
                else:
                    st.info("No new jobs found")

                df_display = df.copy()
                df_display["url"] = df_display["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')

                st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
