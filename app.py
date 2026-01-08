import streamlit as st
import pandas as pd
import os

from Clifford_chance import run_clifford
from tower import run_tower

# -------------------------------
# Session cache
# -------------------------------
if "tower_live" not in st.session_state:
    st.session_state.tower_live = None

if "clifford_live" not in st.session_state:
    st.session_state.clifford_live = None


# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Job Intelligence Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# India city map
# -------------------------------
INDIA_CITIES = [
    "Mumbai", "Bangalore", "Bengaluru", "Delhi", "New Delhi",
    "Gurgaon", "Gurugram", "Noida", "Hyderabad",
    "Chennai", "Pune", "Kolkata"]

# -------------------------------
# Filters
# -------------------------------
def apply_region_filter(df, key):
    if "location" not in df.columns:
        return df

    region = st.selectbox(
        "🌍 Select Region",
        ["All", "India", "Rest of World"],
        key=key
    )

    india_regex = "|".join(INDIA_CITIES)

    if region == "India":
        return df[df["location"].str.contains(india_regex, case=False, na=False)]
    elif region == "Rest of World":
        return df[~df["location"].str.contains(india_regex, case=False, na=False)]
    else:
        return df


# -------------------------------
# Styling
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


# ===========================
# TOWER DISPLAY
# ===========================
if source == "Tower Research":

    if st.session_state.tower_live is None:
        st.info("Click Run Live Scan to fetch Tower Research jobs")
        st.stop()

    df_live = st.session_state.tower_live.drop_duplicates(subset=["id"])

    df_live = apply_region_filter(df_live, "tower_region")

    st.markdown("### 📊 Tower Research")
    st.markdown(f"**Total roles currently listed:** `{len(df_live)}`")

    df_live["url"] = df_live["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
    st.markdown(df_live.to_html(escape=False, index=False), unsafe_allow_html=True)


# ===========================
# CLIFFORD DISPLAY
# ===========================
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

            df_live = apply_region_filter(df_live, f"clifford_{key}")

            st.markdown(f"**Total roles currently listed:** `{len(df_live)}`")

            df_live["url"] = df_live["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
            st.markdown(df_live.to_html(escape=False, index=False), unsafe_allow_html=True)
