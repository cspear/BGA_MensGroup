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

# --- 2. DATA LOADING & CONNECTION ---
@st.cache_data(ttl=2)
def load_sheet(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

def check_db():
    try:
        return requests.head(MASTER_URL, timeout=3).status_code == 200
    except:
        return False

# --- 3. TITLE & STATUS DOT ---
db_status = "🟢" if check_db() else "🔴"
st.markdown(f"## ⛳ Scramble Login {db_status}")

# --- 4. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'team_data' not in st.session_state: st.session_state.team_data = None

# --- 5. NAVIGATION HELPER ---
def nav_to(step):
    st.session_state.step = step
    st.rerun()

# --- 6. SCREENS ---

# REGISTRATION
if st.session_state.step == "register_team":
    st.title("📝 New Team Registration")
    new_phone = st.text_input("Phone Number (ID)")
    new_pass = st.text_input("Password", type="password")
    new_email = st.text_input("Email")
    p1 = st.text_input("Player 1")
    p2 = st.text_input("Player 2")
    p3 = st.text_input("Player 3")

    if st.button("CREATE TEAM"):
        params = {
            "ACTION": "REGISTER",
            "PHONE": new_phone,
            "PASS": new_pass,
            "EMAIL": new_email,
            "P1": p1, "P2": p2, "P3": p3
        }
        r = requests.get(ENTRY_SCRIPT, params=params)
        if "Success" in r.text:
            st.success("Team Created!")
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
            user = m_df[m_df['PHONE'].astype(str) == phone_in]
            if not user.empty and str(user.iloc[0]['PASSWORD']) == str(pass_in):
                st.session_state.team_data = user.iloc[0].to_dict()
                nav_to("verify_entry")
            else:
                st.error("Invalid Credentials.")
    with c2:
        if st.button("NEW TEAM REGISTER"):
            nav_to("register_team")

# ADMIN
elif st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    t1, t2, t3, t4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    s_df = load_sheet(SETUP_URL)
    
    with t1:
        st.subheader("Weekly Check-In List")
        for _, row in s_df.iterrows():
            paid_status = str(row.get('PAID', 'FALSE')).upper()
            color = "green" if paid_status == "TRUE" else "red"
            st.write(f"**{row['PLAYER_1']} & {row['PLAYER_2']}** | Status: :{color}[{paid_status}]")
            st.divider()

    if st.button("LOGOUT"): nav_to("login")

# VERIFY WEEKLY ENTRY
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Weekly Check-In")
    st.subheader(f"{t['PLAYER_1']} & {t['PLAYER_2']}")
    
    s_df = load_sheet(SETUP_URL)
    current_entry = s_df[s_df['TEAM_ID'].astype(str) == str(t['PHONE'])]
    
    if current_entry.empty:
        if st.button("ENTER THIS WEEK'S TOURNAMENT"):
            params = {"PHONE": t['PHONE'], "P1": t['PLAYER_1'], "P2": t['PLAYER_2'], "P3": t.get('PLAYER_3', '')}
            requests.get(ENTRY_SCRIPT, params=params)
            st.rerun()
    else:
        is_paid = str(current_entry.iloc[0].get('PAID', 'FALSE')).upper() == 'TRUE'
        if is_paid:
            st.success(f"✅ PAID - Hole {current_entry.iloc[0].get('STARTING_HOLE', 'TBD')}")
            if st.button("START SCORING"): nav_to(1)
        else:
            st.warning("⏳ Status: UNPAID.")
            if st.button("Refresh"): st.rerun()
