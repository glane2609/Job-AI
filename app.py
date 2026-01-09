import streamlit as st
import pandas as pd
import os
from datetime import datetime

from Clifford_chance import run_clifford
from tower import run_tower

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Job Intelligence Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# Session cache
# -------------------------------
if "tower_live" not in st.session_state:
    st.session_state.tower_live = None

if "clifford_live" not in st.session_state:
    st.session_state.clifford_live = None

# -------------------------------
# ASIA FILTER (Countries + Cities)
# -------------------------------
ASIA_LOCATIONS = [
    # Countries
    "India","Singapore","China","Japan","Korea","South Korea","Taiwan",
    "Thailand","Malaysia","Indonesia","Vietnam","Philippines",
    "UAE","Qatar","Saudi","Dubai","Abu Dhabi","Doha",

    # Cities
    "Mumbai","Bangalore","Bengaluru","Delhi","Gurgaon","Gurugram","Noida",
    "Hyderabad","Chennai","Pune","Kolkata",
    "Singapore","Hong Kong","Tokyo","Osaka","Seoul","Shanghai","Beijing",
    "Taipei","Bangkok","Kuala Lumpur","Jakarta","Manila","Ho Chi Minh","GIFT City","Gift City"
]

def apply_region_filter(df):
    if "location" not in df.columns:
        return df

    asia_regex = "|".join(ASIA_LOCATIONS)

    if region_filter == "Asia":
        return df[df["location"].str.contains(asia_regex, case=False, na=False)]
    elif region_filter == "Rest of World":
        return df[~df["location"].str.contains(asia_regex, case=False, na=False)]
    return df


# -------------------------------
# n-1 vs n comparison helpers
# -------------------------------
def get_new_jobs(df_live, seen_file, id_col):
    if not os.path.exists(seen_file):
        return df_live.copy()
    df_seen = pd.read_csv(seen_file)
    return df_live[~df_live[id_col].astype(str).isin(df_seen[id_col].astype(str))]

def get_dropped_jobs(df_live, seen_file, id_col):
    if not os.path.exists(seen_file):
        return pd.DataFrame()
    df_seen = pd.read_csv(seen_file)
    return df_seen[~df_seen[id_col].astype(str).isin(df_live[id_col].astype(str))]

def update_seen(df_live, seen_file, id_col):
    os.makedirs("data", exist_ok=True)
    if os.path.exists(seen_file):
        df_seen = pd.read_csv(seen_file)
        combined = pd.concat([df_seen, df_live[[id_col]]], ignore_index=True)
    else:
        combined = df_live[[id_col]]
    combined = combined.drop_duplicates()
    combined.to_csv(seen_file, index=False)


# -------------------------------
# Styling
# -------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}
h1, h2, h3 { color: white; }
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

# -------------------------------
# Controls
# -------------------------------
source = st.selectbox("Select Hiring Source", ["Clifford Chance", "Tower Research"])

if st.button("🚀 Run Live Scan"):
    if source == "Tower Research":
        with st.spinner("🔍 Scanning Tower Research..."):
            st.session_state.tower_live = run_tower()
    else:
        with st.spinner("🔍 Scanning Clifford Chance..."):
            st.session_state.clifford_live = run_clifford()

# -------------------------------
# Region filter
# -------------------------------
region_filter = st.selectbox("🌏 Filter by region", ["All", "Asia", "Rest of World"])


# ===============================
# TOWER
# ===============================
if source == "Tower Research":

    if st.session_state.tower_live is None:
        st.info("Click Run Live Scan to fetch Tower Research jobs")
        st.stop()

    df_live = st.session_state.tower_live.drop_duplicates(subset=["id"])

    df_new = get_new_jobs(df_live, "data/tower_seen.csv", "id")
    df_dropped = get_dropped_jobs(df_live, "data/tower_seen.csv", "id")
    update_seen(df_live, "data/tower_seen.csv", "id")

    df_live = apply_region_filter(df_live)

    st.markdown(f"**Total roles currently listed:** `{len(df_live)}`")
    st.success(f"🆕 New today: {len(df_new)}")
    st.warning(f"🗑 Dropped since last scan: {len(df_dropped)}")

    df_live["url"] = df_live["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
    st.markdown(df_live.to_html(escape=False, index=False), unsafe_allow_html=True)


# ===============================
# CLIFFORD
# ===============================
else:

    if st.session_state.clifford_live is None:
        st.info("Click Run Live Scan to fetch Clifford Chance jobs")
        st.stop()

    data = st.session_state.clifford_live

    tabs = st.tabs(["Experienced Lawyers", "Business Professionals", "Early Careers"])

    mapping = {
        "Experienced Lawyers": "Experienced_Lawyers",
        "Business Professionals": "Business_Professionals",
        "Early Careers": "Early_Careers"
    }

    for i, (label, key) in enumerate(mapping.items()):
        with tabs[i]:

            df_live = pd.DataFrame(data[key]).drop_duplicates(subset=["job_id"])

            df_new = get_new_jobs(df_live, "data/clifford_seen.csv", "job_id")
            df_dropped = get_dropped_jobs(df_live, "data/clifford_seen.csv", "job_id")
            update_seen(df_live, "data/clifford_seen.csv", "job_id")

            df_live = apply_region_filter(df_live)

            st.markdown(f"**Total roles currently listed:** `{len(df_live)}`")
            st.success(f"🆕 New today: {len(df_new)}")
            st.warning(f"🗑 Dropped since last scan: {len(df_dropped)}")

            df_live["url"] = df_live["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
            st.markdown(df_live.to_html(escape=False, index=False), unsafe_allow_html=True)
