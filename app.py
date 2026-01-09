import streamlit as st
import pandas as pd
import os
from Clifford_chance import run_clifford
from tower import run_tower
import smtplib
from email.message import EmailMessage
from io import BytesIO
# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Job Intelligence Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# def export_excel(clifford_tabs, tower_df):
#     os.makedirs("data", exist_ok=True)
#     path = "data/asia_hiring_report.xlsx"

#     with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
#         clifford_tabs["Experienced_Lawyers"].to_excel(writer, sheet_name="Clifford_Lawyers", index=False)
#         clifford_tabs["Business_Professionals"].to_excel(writer, sheet_name="Clifford_Business", index=False)
#         clifford_tabs["Early_Careers"].to_excel(writer, sheet_name="Clifford_Early", index=False)
#         tower_df.to_excel(writer, sheet_name="Tower", index=False)

#     return path


def build_excel_in_memory(clifford_tabs, tower_df):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        clifford_tabs["Experienced_Lawyers"].to_excel(writer, sheet_name="Clifford_Lawyers", index=False)
        clifford_tabs["Business_Professionals"].to_excel(writer, sheet_name="Clifford_Business", index=False)
        clifford_tabs["Early_Careers"].to_excel(writer, sheet_name="Clifford_Early", index=False)
        tower_df.to_excel(writer, sheet_name="Tower", index=False)

    buffer.seek(0)
    return buffer

def send_email_excel(buffer):
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not password:
        raise Exception("GMAIL_APP_PASSWORD not found")

    msg = EmailMessage()
    msg["Subject"] = "Asia Hiring Radar – Daily Report"
    msg["From"] = "glane.gonsalves9@gmail.com"
    msg["To"] = "glane.gonsalves9@gmail.com"
    msg.set_content("Attached: Asia hiring jobs for Clifford Chance and Tower Research.")

    msg.add_attachment(
        buffer.read(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="asia_hiring_report.xlsx"
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.set_debuglevel(1)   # <-- THIS
        smtp.login("glane.gonsalves9@gmail.com", password)
        smtp.send_message(msg)




# -------------------------------
# Session cache
# -------------------------------
if "tower_live" not in st.session_state:
    st.session_state.tower_live = None
if "clifford_live" not in st.session_state:
    st.session_state.clifford_live = None
if "excel_path" not in st.session_state:
    st.session_state.excel_path = None
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

# -------------------------------
# Init persistent exports
# -------------------------------
if "asia_clifford_export" not in st.session_state:
    st.session_state.asia_clifford_export = {
        "Experienced_Lawyers": pd.DataFrame(),
        "Business_Professionals": pd.DataFrame(),
        "Early_Careers": pd.DataFrame()
    }

if "tower_asia_export" not in st.session_state:
    st.session_state.tower_asia_export = pd.DataFrame()

# -------------------------------
# Run Scan
# -------------------------------
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

    # Save Asia snapshot for email
    st.session_state.tower_asia_export = df_asia.copy()

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

            # Save Asia data for email
            st.session_state.asia_clifford_export[key] = df_asia.copy()

            today, new, removed = compare(df_asia, CLIFFORD_SNAPSHOT, "job_id")
            save_snapshot(today, CLIFFORD_SNAPSHOT)

            st.markdown(f"**Asia jobs visible today:** `{len(today)}`")
            st.success(f"🆕 New since last scan: `{len(new)}`")
            st.warning(f"🗑 Removed since last scan: `{len(removed)}`")

            today["url"] = today["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
            st.markdown(today.to_html(escape=False, index=False), unsafe_allow_html=True)

# -------------------------------
# EMAIL BUTTON
# -------------------------------
st.divider()

if st.button("📧 Send Email"):
    try:
        excel_buffer = build_excel_in_memory(
            st.session_state.asia_clifford_export,
            st.session_state.tower_asia_export
        )
        send_email_excel(excel_buffer)
        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Email failed: {e}")
