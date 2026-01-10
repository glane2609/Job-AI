import streamlit as st
import pandas as pd
import os
from Clifford_chance import run_clifford
from tower import run_tower
import smtplib
from email.message import EmailMessage
from io import BytesIO
import io
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
def build_tower_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Tower Asia Jobs", index=False)
    buffer.seek(0)
    return buffer


def build_clifford_excel(tabs):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        tabs["Experienced_Lawyers"].to_excel(writer, sheet_name="Experienced Lawyers", index=False)
        tabs["Business_Professionals"].to_excel(writer, sheet_name="Business Professionals", index=False)
        tabs["Early_Careers"].to_excel(writer, sheet_name="Early Careers", index=False)
    buffer.seek(0)
    return buffer

def build_excel_in_memory(source, clifford_tabs=None, tower_df=None):
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:

        if source == "Clifford Chance" and clifford_tabs is not None:
            clifford_tabs["Experienced_Lawyers"].to_excel(writer, sheet_name="Clifford_Lawyers", index=False)
            clifford_tabs["Business_Professionals"].to_excel(writer, sheet_name="Clifford_Business", index=False)
            clifford_tabs["Early_Careers"].to_excel(writer, sheet_name="Clifford_Early", index=False)

        elif source == "Tower Research" and tower_df is not None:
            tower_df.to_excel(writer, sheet_name="Tower", index=False)

    buffer.seek(0)
    return buffer
from io import BytesIO

def build_excel_for_download(source, clifford_tabs=None, tower_df=None):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:

        if source == "Clifford Chance":
            clifford_tabs["Experienced_Lawyers"].to_excel(writer, sheet_name="Experienced Lawyers", index=False)
            clifford_tabs["Business_Professionals"].to_excel(writer, sheet_name="Business Professionals", index=False)
            clifford_tabs["Early_Careers"].to_excel(writer, sheet_name="Early Careers", index=False)

        elif source == "Tower Research":
            tower_df.to_excel(writer, sheet_name="Tower Asia Jobs", index=False)

    buffer.seek(0)
    return buffer 
import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

def send_email_excel(source, buffer):

    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        raise Exception("SENDGRID_API_KEY not set")

    sender = "glane.gonsalves9@gmail.com"      # must be SendGrid-verified
    recipient = "glane.gonsalves9@gmail.com"  # change later to HR / company

    subject = f"Asia Hiring Radar – {source}"

    body = f"""
Hello,

Attached is the latest Asia hiring report for **{source}**.

Regards  
Job-AI
"""

    # Make sure buffer is at start
    buffer.seek(0)

    # Convert Excel to base64
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    attachment = Attachment(
        FileContent(encoded),
        FileName(f"{source.lower().replace(' ','_')}_asia_jobs.xlsx"),
        FileType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        Disposition("attachment")
    )

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        plain_text_content=body
    )

    message.attachment = attachment

    sg = SendGridAPIClient(api_key)
    response = sg.send(message)

    if response.status_code not in (200, 202):
        raise Exception(f"SendGrid failed: {response.status_code} – {response.body}")





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

/* ===== Animated Gradient Background ===== */
.stApp {
    background:
        radial-gradient(circle at top left, #0f4c75 0%, transparent 40%),
        radial-gradient(circle at bottom right, #0a2540 0%, transparent 45%),
        linear-gradient(180deg, #050b14 0%, #0b1f2a 40%, #0a2540 100%);
    color: white;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    background:
        linear-gradient(120deg,
            transparent 20%,
            rgba(0,200,255,0.05) 40%,
            rgba(255,255,255,0.07) 50%,
            rgba(0,200,255,0.05) 60%,
            transparent 80%);
    animation: aurora 14s linear infinite;
    pointer-events: none;
    z-index: 0;
}

@keyframes aurora {
    from { transform: translateX(-100%); }
    to { transform: translateX(100%); }
}

@keyframes lightSweep {
    from { transform: translateX(-100%); }
    to { transform: translateX(100%); }
}

@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* ===== Global Typography ===== */
h1, h2, h3, h4 {
    color: white;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* ===== Glassmorphism Cards ===== */
.block-container {
    backdrop-filter: blur(10px);
}

/* ===== Premium Buttons ===== */
.stButton>button {
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 30px;
    padding: 12px 28px;
    border: none;
    font-weight: 700;
    letter-spacing: 0.5px;
    box-shadow: 0 0 20px rgba(0,198,255,0.6);
    transition: all 0.3s ease-in-out;
}

.stButton>button:hover {
    transform: scale(1.08);
    box-shadow: 0 0 40px rgba(0,198,255,0.9);
}

.stDownloadButton>button {
    background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
    color: white !important;
    border-radius: 30px !important;
    padding: 12px 28px !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 0 25px rgba(0,198,255,0.7) !important;
    transition: all 0.3s ease-in-out !important;
}

.stDownloadButton>button:hover {
    transform: scale(1.08);
    box-shadow: 0 0 45px rgba(0,198,255,1);
}
/* ===== DataFrame Glass Effect ===== */
[data-testid="stDataFrame"], table {
    background: rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(12px);
    border-radius: 16px;
    overflow: hidden;
}

/* ===== Smooth Animations ===== */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.stMarkdown, .stDataFrame, .stButton {
    animation: slideUp 0.7s ease-in-out;
}

/* ===== Tab Glow ===== */
button[data-baseweb="tab"] {
    color: white !important;
    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid #00c6ff !important;
    color: #00c6ff !important;
}

/* ===== Remove Streamlit Branding ===== */
#MainMenu, footer, header {
    visibility: hidden;
}

/* ===== Title Animations ===== */
.title-left {
    font-size: 48px;
    font-weight: 800;
    color: white;
    animation: slideFromLeft 1s ease-out;
}

.title-right {
    font-size: 48px;
    font-weight: 800;
    color: white;
    animation: slideFromRight 1s ease-out;
}

.title-sub {
    text-align: center;
    margin-top: 10px;
    font-size: 18px;
    color: #ccecff;
    animation: fadeUp 1.2s ease-out;
}

/* Animations */
@keyframes slideFromLeft {
    from { opacity: 0; transform: translateX(-200px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideFromRight {
    from { opacity: 0; transform: translateX(200px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(40px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ===== KPI Cards ===== */
.kpi-row {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin: 30px 0;
}

.kpi-card {
    width: 220px;
    height: 140px;
    background: linear-gradient(135deg, #0b1f2a, #132f42);
    border-radius: 20px;
    text-align: center;
    padding-top: 25px;
    font-size: 18px;
    font-weight: 700;
    color: white;
    box-shadow: 0 0 40px rgba(0,180,255,0.25);
    animation: popCenter 0.8s ease-out;
}

.kpi-number {
    font-size: 48px;
    font-weight: 800;
    margin-top: 10px;
}

.kpi-green {
    background: linear-gradient(135deg, #003b19, #0a4f2b);
    box-shadow: 0 0 40px rgba(0,255,140,0.4);
}

.kpi-red {
    background: linear-gradient(135deg, #3a0a0a, #5a1414);
    box-shadow: 0 0 40px rgba(255,80,80,0.4);
}

/* ===== Center pop animation ===== */
@keyframes popCenter {
    from { opacity: 0; transform: scale(0.6); }
    to { opacity: 1; transform: scale(1); }
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display:flex; justify-content:center; align-items:center; gap:20px; margin-top:20px;">
    <div class="title-left">📊 Live Hiring</div>
    <div class="title-right">Intelligence</div>
</div>
<div class="title-sub">Clifford Chance & Tower Research</div>
""", unsafe_allow_html=True)

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

    # st.markdown(f"**Asia jobs visible today:** `{len(today)}`")
    # st.success(f"🆕 New since last scan: `{len(new)}`")
    # st.warning(f"🗑 Removed since last scan: `{len(removed)}`")
    st.markdown(f"""
        <div class="kpi-row">
        
          <div class="kpi-card">
            🌏 Asia Jobs
            <div class="kpi-number">{len(today)}</div>
          </div>
        
          <div class="kpi-card kpi-green">
            🆕 New
            <div class="kpi-number">{len(new)}</div>
          </div>
        
          <div class="kpi-card kpi-red">
            🗑 Removed
            <div class="kpi-number">{len(removed)}</div>
          </div>
        
        </div>
        """, unsafe_allow_html=True)


    today["url"] = today["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
    #st.markdown(today.to_html(escape=False, index=False), unsafe_allow_html=True)
    left, center, right = st.columns([1, 3, 1])

    with center:
        st.markdown(f"""
        <div class="table-center">
            {today.to_html(escape=False, index=False)}
        </div>
        """, unsafe_allow_html=True)
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

            # st.markdown(f"**Asia jobs visible today:** `{len(today)}`")
            # st.success(f"🆕 New since last scan: `{len(new)}`")
            # st.warning(f"🗑 Removed since last scan: `{len(removed)}`")
            st.markdown(f"""
            <div class="kpi-row">
            
              <div class="kpi-card kpi-center">
                🌏 Asia Jobs
                <div class="kpi-number">{len(today)}</div>
              </div>
            
              <div class="kpi-card kpi-center kpi-green">
                🆕 New
                <div class="kpi-number">{len(new)}</div>
              </div>
            
              <div class="kpi-card kpi-center kpi-red">
                🗑 Removed
                <div class="kpi-number">{len(removed)}</div>
              </div>
            
            </div>
            """, unsafe_allow_html=True)

            today["url"] = today["url"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
            #st.markdown(today.to_html(escape=False, index=False), unsafe_allow_html=True)
            left, center, right = st.columns([1, 3, 1])

            with center:
                st.markdown(f"""
                <div class="table-center">
                    {today.to_html(escape=False, index=False)}
                </div>
                """, unsafe_allow_html=True)
# -------------------------------
# EMAIL BUTTON
# -------------------------------
st.divider()

left, col1, col2, right = st.columns([1, 2, 2, 1])

# ======================
# CLIFFORD
# ======================
if source == "Clifford Chance":

    if any(len(df) > 0 for df in st.session_state.asia_clifford_export.values()):

        # Build Excel once
        buffer = build_excel_for_download(
            source="Clifford Chance",
            clifford_tabs=st.session_state.asia_clifford_export
        )

        with col1:
            st.download_button(
                label="📥 Download Clifford Asia Excel",
                data=buffer,
                file_name="clifford_asia_jobs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False
            )

        with col2:
            if st.button("📧 Send Clifford Email", use_container_width=False):
                try:
                    send_email_excel("Clifford Chance", buffer)
                    st.success("Clifford email sent successfully!")
                except Exception as e:
                    st.error(f"Email failed: {e}")

# ======================
# TOWER
# ======================
if source == "Tower Research" and not st.session_state.tower_asia_export.empty:

    buffer = build_excel_for_download(
        source="Tower Research",
        tower_df=st.session_state.tower_asia_export
    )

    with col1:
        st.download_button(
            label="📥 Download Tower Asia Excel",
            data=buffer,
            file_name="tower_asia_jobs.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=False
        )

    with col2:
        if st.button("📧 Send Tower Email", use_container_width=False):
            try:
                send_email_excel("Tower Research", buffer)
                st.success("Tower email sent successfully!")
            except Exception as e:
                st.error(f"Email failed: {e}")
