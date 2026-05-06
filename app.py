import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets["admin_pin"])
ENTRY_SCRIPT = st.secrets["entry_script_url"]

MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble Pro", layout="centered")

# --- 2. DATA LOADING ---
@st.cache_data(ttl=2)
def load_sheet(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

def check_db():
    try: return requests.head(MASTER_URL, timeout=2).status_code == 200
    except: return False

# --- 3. TITLE & SMALL STATUS DOT ---
dot_color = "#28a745" if check_db() else "#dc3545"
st.markdown(f"""
    <h2 style='display: inline;'>⛳ Scramble Login </h2>
    <span style='height: 12px; width: 12px; background-color: {dot_color}; border-radius: 50%; display: inline-block; margin-left: 5px; vertical-align: middle;'></span>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'team_data' not in st.session_state: st.session_state.team_data = None

def nav_to(step):
    st.session_state.step = step
    st.rerun()

# --- 5. SCREENS ---

# REGISTRATION with Duplicate Check
if st.session_state.step == "register_team":
    st.title("📝 New Team Registration")
    new_phone = st.text_input("Phone Number (ID)")
    new_pass = st.text_input("Password", type="password")
    new_email = st.text_input("Email")
    p1 = st.text_input("Player 1")
    p2 = st.text_input("Player 2")
    p3 = st.text_input("Player 3 (Optional)")

    if st.button("CREATE TEAM"):
        m_df = load_sheet(MASTER_URL)
        if str(new_phone) in m_df['PHONE'].astype(str).values:
            st.error("This phone number is already registered. Please log in.")
        else:
            params = {"ACTION": "REGISTER", "PHONE": new_phone, "PASS": new_pass, "EMAIL": new_email, "P1": p1, "P2": p2, "P3": p3}
            r = requests.get(ENTRY_SCRIPT, params=params)
            if "Success" in r.text:
                st.success("Team Created! You can now log in.")
                st.button("Back to Login", on_click=nav_to, args=("login",))
    if st.button("Cancel"): nav_to("login")

# LOGIN
elif st.session_state.step == "login":
    phone_in = st.text_input("PHONE NUMBER").strip()
    pass_in = st.text_input("PASSWORD", type="password")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("LOGIN / JOIN WEEKLY"):
            if phone_in.lower() == "admin" and str(pass_in) == ADMIN_PIN:
                nav_to("admin")
            m_df = load_sheet(MASTER_URL)
            user = m_df[m_df['PHONE'].astype(str).str.strip() == phone_in]
            if not user.empty and str(user.iloc[0]['PASSWORD']).strip() == str(pass_in).strip():
                st.session_state.team_data = user.iloc[0].to_dict()
                nav_to("verify_entry")
            else: st.error("Invalid Credentials.")
    with c2:
        if st.button("NEW TEAM REGISTER"): nav_to("register_team")

# ADMIN (Table Format Restored)
elif st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    t1, t2, t3, t4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    s_df = load_sheet(SETUP_URL)
    
    with t1:
        st.subheader("Check-In Table")
        st.write("Edit 'PAID' and 'HOLE' in your Google Sheet to update this list.")
        # Filter for compact view
        display_df = s_df[['TEAM_ID', 'PLAYER_1', 'PAID', 'STARTING_HOLE']]
        st.table(display_df)

    if st.button("LOGOUT"): nav_to("login")

# VERIFY WEEKLY ENTRY
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Weekly Check-In")
    st.subheader(f"Team: {t['PLAYER_1']} & {t['PLAYER_2']}")
    
    s_df = load_sheet(SETUP_URL)
    current_entry = s_df[s_df['TEAM_ID'].astype(str) == str(t['PHONE'])]
    
    if current_entry.empty:
        if st.button("ENTER THIS WEEK'S TOURNAMENT"):
            params = {"PHONE": t['PHONE'], "P1": t['PLAYER_1'], "P2": t['PLAYER_2'], "P3": t.get('PLAYER_3', '')}
            requests.get(ENTRY_SCRIPT, params=params)
            st.rerun()
    else:
        is_paid = str(current_entry.iloc[0].get('PAID', 'FALSE')).upper() == 'TRUE'
        hole = current_entry.iloc[0].get('STARTING_HOLE', 'TBD')
        if is_paid:
            st.success(f"✅ PAID - Starting on Hole {hole}")
            if st.button("START SCORING"): nav_to(1)
        else:
            st.warning("⏳ Status: UNPAID. See Admin to pay and get a hole number.")
            if st.button("Refresh"): st.rerun()
