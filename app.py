import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets["admin_pin"])
ENTRY_SCRIPT = st.secrets["entry_script_url"]
# Optional: If you have a script to handle new team creation, put it here.
# Otherwise, we use the same script with a 'new_team' flag.
REG_SCRIPT = st.secrets.get("reg_script_url", ENTRY_SCRIPT) 

# Data URLs
MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"
COURSE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Course_Data"

st.set_page_config(page_title="Golf Scramble Pro", layout="centered")

# --- 2. UI STYLING (The Big Button Look) ---
st.markdown("""
    <style>
    .stButton > button { width: 100% !important; border-radius: 10px !important; }
    div[data-testid="stHorizontalBlock"] div.stButton > button { 
        background-color: #007bff !important; color: white !important; font-size: 45px !important; height: 100px !important; 
    }
    .floating-digit { font-size: 100px; font-weight: bold; color: #007bff; display: block; text-align: center; line-height: 100px; }
    .admin-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA HELPERS ---
@st.cache_data(ttl=2)
def load_sheet(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

# --- 4. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'team_data' not in st.session_state: st.session_state.team_data = None
if 'scores' not in st.session_state: st.session_state.scores = {i: 4 for i in range(1, 10)}

# --- 5. LOGIN & REGISTRATION ---
if st.session_state.step == "login":
    st.title("⛳ Scramble Login")
    phone_in = st.text_input("PHONE NUMBER").strip()
    pass_in = st.text_input("PASSWORD", type="password")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("LOGIN / JOIN WEEKLY"):
            if phone_in.lower() == "admin" and str(pass_in) == ADMIN_PIN:
                st.session_state.step = "admin"
                st.rerun()
            
            m_df = load_sheet(MASTER_URL)
            user = m_df[m_df['PHONE'].astype(str) == phone_in]
            if not user.empty and str(user.iloc[0]['PASSWORD']) == str(pass_in):
                st.session_state.team_data = user.iloc[0].to_dict()
                st.session_state.step = "verify_entry"
                st.rerun()
            else:
                st.error("Invalid Credentials.")
    with c2:
        if st.button("NEW TEAM REGISTER"):
            st.session_state.step = "register_team"
            st.rerun()

elif st.session_state.step == "register_team":
    st.title("📝 New Team Registration")
    new_phone = st.text_input("Phone Number (This is your ID)")
    new_pass = st.text_input("Create Password/PIN", type="password")
    new_email = st.text_input("Email Address")
    p1 = st.text_input("Player 1 Name")
    p2 = st.text_input("Player 2 Name")
    p3 = st.text_input("Player 3 Name (Optional)")
    
    if st.button("CREATE TEAM"):
        reg_params = {
            "ACTION": "REGISTER",
            "PHONE": new_phone,
            "PASS": new_pass,
            "EMAIL": new_email,
            "P1": p1, "P2": p2, "P3": p3
        }
        r = requests.get(REG_SCRIPT, params=reg_params)
        if "Success" in r.text:
            st.success("Registration Successful! You can now log in.")
            if st.button("Back to Login"):
                st.session_state.step = "login"
                st.rerun()
        else:
            st.error("Registration failed. Check connection.")

# --- 6. WEEKLY CHECK-IN (Gatekeeper) ---
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Weekly Check-In")
    st.subheader(f"{t['PLAYER_1']}, {t['PLAYER_2']}" + (f", {t['PLAYER_3']}" if pd.notna(t.get('PLAYER_3')) else ""))
    
    s_df = load_sheet(SETUP_URL)
    current_entry = s_df[s_df['TEAM_ID'].astype(str) == str(t['PHONE'])]
    
    if current_entry.empty:
        if st.button("ENTER THIS WEEK'S TOURNAMENT", type="primary"):
            params = {"PHONE": t['PHONE'], "P1": t['PLAYER_1'], "P2": t['PLAYER_2'], "P3": t.get('PLAYER_3', '')}
            requests.get(ENTRY_SCRIPT, params=params)
            st.success("Entry Sent! Refreshing...")
            st.rerun()
    else:
        is_paid = str(current_entry.iloc[0].get('PAID', 'FALSE')).upper() == 'TRUE'
        if is_paid:
            st.success(f"✅ PAID - Hole {current_entry.iloc[0].get('STARTING_HOLE', 'TBD')}")
            if st.button("START SCORING"):
                st.session_state.step = 1
                st.rerun()
        else:
            st.warning("⏳ Status: UNPAID. See Admin to unlock.")
            if st.button("Refresh Status"): st.rerun()

# --- 7. ADMIN DASHBOARD ---
elif st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    tab1, tab2, tab3, tab4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    s_df = load_sheet(SETUP_URL)
    
    with tab1:
        unpaid = s_df[s_df['PAID'].astype(str).str.upper() != 'TRUE']
        for _, row in unpaid.iterrows():
            st.markdown(f"<div class='admin-card'><b>{row['PLAYER_1']} & {row['PLAYER_2']}</b></div>", unsafe_allow_html=True)
            
    with tab2:
        paid = s_df[s_df['PAID'].astype(str).str.upper() == 'TRUE']
        st.table(paid[['TEAM_ID', 'PLAYER_1', 'STARTING_HOLE']])

    if st.button("LOGOUT"):
        st.session_state.step = "login"
        st.rerun()

# --- 8. SCORING MODE (1-9) ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    st.markdown(f"<div class='floating-digit'>Hole {h}</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1,1])
    if c1.button("−"):
        if st.session_state.scores[h] > 1: st.session_state.scores[h] -= 1; st.rerun()
    c2.markdown(f"<div class='floating-digit'>{st.session_state.scores[h]}</div>", unsafe_allow_html=True)
    if c3.button("+"):
        if st.session_state.scores[h] < 20: st.session_state.scores[h] += 1; st.rerun()
        
    if st.button("NEXT HOLE" if h < 9 else "FINISH"):
        st.session_state.step = h + 1 if h < 9 else "review"
        st.rerun()
