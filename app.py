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
# Dedup storage (history only)
# -------------------------------
def diff_and_store(df_live, file):
    path = f"{DATA_DIR}/{file}"

    # Detect ID column automatically
    if "job_id" in df_live.columns:
        key = "job_id"
    elif "id" in df_live.columns:
        key = "id"
    else:
        raise ValueError("No ID column found")

    # Deduplicate current live
    df_live = df_live.drop_duplicates(subset=[key])

    if os.path.exists(path):
        df_old = pd.read_csv(path)
    else:
        df_old = pd.DataFrame(columns=df_live.columns)

    # New jobs = in live but not in old
    df_new = df_live[~df_live[key].astype(str).isin(df_old[key].astype(str))]

    # Update history
    df_store = pd.concat([df_old, df_new], ignore_index=True)
    df_store = df_store.drop_duplicates(subset=[key])

    df_store.to_csv(path, index=False)

    return df_store, df_new


source = st.selectbox("Select Hiring Source", ["Clifford Chance", "Tower Research"])

if st.button("🚀 Run Live Scan"):

    # ===========================
    # Tower Research
    # ===========================
    if source == "Tower Research":
        with st.spinner("🔍 Scanning Tower Research..."):
            df_live = run_tower()

        # Deduplicate live
        df_live = df_live.drop_duplicates(subset=["id"])

        total_live = len(df_live)

        df_store, df_new = diff_and_store(df_live, "tower.csv")
        new_count = len(df_new)

        st.markdown("### 📊 Tower Research")
        st.markdown(f"**Total roles currently listed:** `{total_live}`")

        if new_count > 0:
            st.success(f"🆕 {new_count} new Tower jobs detected!")
        else:
            st.info("No new Tower jobs since last scan")

        # Show LIVE jobs, not history
        df_live["url"] = df_live["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
        st.markdown(df_live.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ===========================
    # Clifford Chance
    # ===========================
    else:
        with st.spinner("🔍 Scanning Clifford Chance global careers site..."):
            data = run_clifford()

        tabs = st.tabs(["Experienced Lawyers", "Business Professionals", "Early Careers"])

        mapping = {
            "Experienced Lawyers": ("Experienced_Lawyers", "clifford_experienced.csv"),
            "Business Professionals": ("Business_Professionals", "clifford_business.csv"),
            "Early Careers": ("Early_Careers", "clifford_early.csv")
        }

        for i, (label, (key, file)) in enumerate(mapping.items()):
            with tabs[i]:

                # LIVE jobs from website
                df_live = pd.DataFrame(data[key])

                # Deduplicate live
                df_live = df_live.drop_duplicates(subset=["job_id"])

                total_live = len(df_live)

                # Compare with history
                df_store, df_new = diff_and_store(df_live, file)
                new_count = len(df_new)

                st.markdown(f"**Total roles currently listed:** `{total_live}`")

                if new_count > 0:
                    st.success(f"🆕 {new_count} new roles detected!")
                else:
                    st.info("No new roles since last scan")

                # Show LIVE jobs
                df_live["url"] = df_live["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
                st.markdown(df_live.to_html(escape=False, index=False), unsafe_allow_html=True)
