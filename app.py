import streamlit as st
import pandas as pd
import os
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
# ASIA LOCATIONS
# -------------------------------
ASIA_LOCATIONS = [
    "India","Singapore","China","Japan","Korea","South Korea","Taiwan",
    "Thailand","Malaysia","Indonesia","Vietnam","Philippines",
    "UAE","Qatar","Saudi","Dubai","Abu Dhabi","Doha",
    "Mumbai","Bangalore","Bengaluru","Delhi","Gurgaon","Gurugram","Noida",
    "Hyderabad","Chennai","Pune","Kolkata","GIFT City","Gift City",
    "Hong Kong","Tokyo","Osaka","Seoul","Shanghai","Beijing",
    "Taipei","Bangkok","Kuala Lumpur","Jakarta","Manila","Ho Chi Minh"
]

CLIFFORD_SNAPSHOT = "data/clifford_asia_snapshot.csv"
TOWER_SNAPSHOT = "data/tower_asia_snapshot.csv"

# -------------------------------
# Snapshot helpers
# -------------------------------
def is_asia(location):
    if not isinstance(location, str):
        return False
    return any(k.lower() in location.lower() for k in ASIA_LOCATIONS)

def load_snapshot(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def save_snapshot(df, path):
    os.makedirs("data", exist_ok=True)
    df.to_csv(path, index=False)

def compare(today, snapshot_path, id_col):
    yesterday = load_snapshot(snapshot_path)
    if len(yesterday) == 0:
        return today, pd.DataFrame(), pd.DataFrame()

    new = today[~today[id_col].isin(yesterday[id_col])]
    removed = yesterday[~yesterday[id_col].isin(today[id_col])]
    return today, new, removed

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

# ===============================
# TOWER
# ===============================
if source == "Tower Research":

    if st.session_state.tower_live is None:
        st.info("Click Run Live Scan to fetch Tower Research jobs")
        st.stop()

    df = st.session_state.tower_live.drop_duplicates(subset=["id"])
    df_asia = df[df["location"].apply(is_asia)]

    today, new, removed = compare(df_asia, TOWER_SNAPSHOT, "id")
    save_snapshot(today, TOWER_SNAPSHOT)

    st.markdown(f"**Asia jobs visible today:** `{len(today)}`")
    st.success(f"🆕 New since last scan: `{len(new)}`")
    st.warning(f"🗑 Removed since last scan: `{len(removed)}`")

    today["url"] = today["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
    st.markdown(today.to_html(escape=False, index=False), unsafe_allow_html=True)

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
            df = pd.DataFrame(data[key]).drop_duplicates(subset=["job_id"])
            df_asia = df[df["location"].apply(is_asia)]

            today, new, removed = compare(df_asia, CLIFFORD_SNAPSHOT, "job_id")
            save_snapshot(today, CLIFFORD_SNAPSHOT)

            st.markdown(f"**Asia jobs visible today:** `{len(today)}`")
            st.success(f"🆕 New since last scan: `{len(new)}`")
            st.warning(f"🗑 Removed since last scan: `{len(removed)}`")

            today["url"] = today["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
            st.markdown(today.to_html(escape=False, index=False), unsafe_allow_html=True)
