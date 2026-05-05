import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets["admin_pin"])
ENTRY_SCRIPT = st.secrets["entry_script_url"]
FORM_URL = st.secrets["form_url"]

# Data URLs (Added cache-busting headers)
MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"
SCORES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Scores"

st.set_page_config(page_title="Golf Scramble Pro", layout="centered")

# --- 2. CONNECTION TEST (THE MUST-HAVE) ---
def verify_connection(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

# --- 3. DATA LOADING (FORCE REFRESH) ---
@st.cache_data(ttl=5) # Refresh every 5 seconds
def load_data(url):
    return pd.read_csv(url)

# --- 4. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'scores' not in st.session_state: st.session_state.scores = {i: 4 for i in range(1, 10)}
if 'team_data' not in st.session_state: st.session_state.team_data = None

# --- 5. LOGIN SCREEN ---
if st.session_state.step == "login":
    st.title("⛳ Scramble Login")
    
    if not verify_connection(MASTER_URL):
        st.error("📡 DATABASE OFFLINE: Check gsheet_id in Secrets.")
    
    phone_in = st.text_input("PHONE NUMBER").strip()
    pass_in = st.text_input("PASSWORD", type="password")

    if st.button("LOGIN / JOIN WEEKLY"):
        if phone_in.lower() == "admin" and str(pass_in) == ADMIN_PIN:
            st.session_state.step = "admin"
            st.rerun()
        
        m_df = load_data(MASTER_URL)
        m_df['PHONE'] = m_df['PHONE'].astype(str).str.strip()
        user = m_df[m_df['PHONE'] == phone_in]
        
        if not user.empty and str(user.iloc[0]['PASSWORD']) == str(pass_in):
            st.session_state.team_data = user.iloc[0].to_dict()
            st.session_state.step = "verify_entry"
            st.rerun()
        else:
            st.error("Invalid Login.")

# --- 6. WEEKLY ENTRY & PAID GATEKEEPER ---
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Confirm Weekly Entry")
    st.subheader(f"{t['PLAYER_1']} & {t['PLAYER_2']}")
    
    # Check if team is already in Setup and PAID
    s_df = load_data(SETUP_URL)
    s_df['PHONE'] = s_df['PHONE'].astype(str).str.strip()
    current_entry = s_df[s_df['PHONE'] == str(t['PHONE'])]
    
    is_paid = False
    if not current_entry.empty:
        is_paid = str(current_entry.iloc[0]['PAID']).upper() == 'TRUE'

    if current_entry.empty:
        if st.button("ENTER THIS WEEK'S TOURNAMENT"):
            params = {"PHONE": t['PHONE'], "P1": t['PLAYER_1'], "P2": t['PLAYER_2']}
            requests.get(ENTRY_SCRIPT, params=params)
            st.success("Entry Sent! Refreshing...")
            st.rerun()
    else:
        if is_paid:
            st.success("✅ Payment Verified!")
            if st.button("START SCORING"):
                st.session_state.step = 1
                st.rerun()
        else:
            st.warning("⏳ Status: UNPAID. Please see Admin to unlock scoring.")
            if st.button("Check Payment Status Again"):
                st.rerun()

# --- 7. ADMIN DASHBOARD (FORCED REFRESH) ---
elif st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    t1, t2, t3, t4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    
    with t1:
        s_df = load_data(SETUP_URL)
        unpaid = s_df[s_df['PAID'].astype(str).str.upper() == 'FALSE']
        if unpaid.empty:
            st.success("Leaderboard is clear of unpaid teams.")
        else:
            for _, row in unpaid.iterrows():
                st.info(f"UNPAID: {row['PLAYER_1']} & {row['PLAYER_2']} (Phone: {row['PHONE']})")

    if st.button("LOGOUT"):
        st.session_state.step = "login"
        st.rerun()

# --- 8. SCORING MODE ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    st.header(f"Hole {h}")
    # ... (Insert your big button +/- logic here) ...
    if st.button("Next Hole"):
        st.session_state.step = h + 1 if h < 9 else "review"
        st.rerun()
