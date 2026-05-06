import streamlit as st
import pandas as pd
import requests
import time
import re

# --- 1. CONFIG ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets["admin_pin"])
ENTRY_SCRIPT = st.secrets["entry_script_url"]

MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble Pro", layout="wide")

# --- 2. STYLING (Ultra-Compact) ---
st.markdown("""
    <style>
    /* Compact the buttons and dropdowns */
    .stButton > button { width: 100%; padding: 0px !important; height: 35px !important; }
    div[data-baseweb="select"] > div { height: 35px !important; min-height: 35px !important; }
    /* Dark line break for hole groups */
    .group-break { border-bottom: 3px solid #222; margin: 12px 0px; }
    /* Tighten vertical spacing between rows */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA HELPERS & SORTING ---
@st.cache_data(ttl=2)
def load_sheet(base_url):
    fetch_url = f"{base_url}&_={int(time.time())}"
    df = pd.read_csv(fetch_url).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

@st.cache_data(ttl=60)
def check_db():
    try: return requests.get(MASTER_URL, timeout=2).status_code == 200
    except: return False

# Natural sorting for Hole numbers (1, 2, 2A, 3...)
def natural_hole_sort(h):
    h_str = str(h).upper().strip().replace(".0", "")
    match = re.match(r"(\d+)([A-Z]*)", h_str)
    if match: return (int(match.group(1)), match.group(2))
    return (999, h_str) # Puts unassigned/blanks at the bottom

# --- 4. CALLBACK FUNCTIONS ---
def toggle_paid(phone, current_paid):
    new_status = "FALSE" if current_paid else "TRUE"
    requests.get(ENTRY_SCRIPT, params={"ACTION": "UPDATE_TEAM", "PHONE": phone, "PAID": new_status})
    load_sheet.clear()

def update_hole(phone, new_hole):
    requests.get(ENTRY_SCRIPT, params={"ACTION": "UPDATE_TEAM", "PHONE": phone, "HOLE": new_hole})
    load_sheet.clear()

# --- 5. APP LOGIC ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'team_data' not in st.session_state: st.session_state.team_data = None

def nav_to(step):
    st.session_state.step = step
    st.rerun()

# --- ADMIN DASHBOARD ---
if st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    tab1, tab2, tab3, tab4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    
    s_df = load_sheet(SETUP_URL)
    
    with tab1:
        # Clean and sort holes natively
        s_df['CLEAN_HOLE'] = s_df['STARTING_HOLE'].apply(lambda x: str(x).upper().strip().replace(".0", ""))
        s_df['SORT_KEY'] = s_df['CLEAN_HOLE'].apply(natural_hole_sort)
        s_df = s_df.sort_values(by='SORT_KEY')

        st.markdown("**Team Names &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Payment &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Hole Assignment**")
        
        last_hole = None
        for idx, row in s_df.iterrows():
            current_hole_val = row['CLEAN_HOLE']
            
            # Insert dark line ONLY when the hole group changes (skip the very first line)
            if last_hole is not None and current_hole_val != last_hole:
                st.markdown("<div class='group-break'></div>", unsafe_allow_html=True)
            last_hole = current_hole_val

            has_p3 = bool(str(row['PLAYER_3']).strip())
            p3_text = f", {row['PLAYER_3']}" if has_p3 else ""
            team_str = f"{row['PLAYER_1']}, {row['PLAYER_2']}{p3_text}"
            amount_due = "$15" if has_p3 else "$10"
            current_paid = str(row['PAID']).upper() == "TRUE"
            
            # Single-line columns: [Names (50%), Paid (25%), Hole (25%)]
            c1, c2, c3 = st.columns([4, 2, 2])
            
            c1.markdown(f"<div style='margin-top: 5px; font-size: 15px;'><b>{team_str}</b></div>", unsafe_allow_html=True)
            
            btn_text = "✅ PAID" if current_paid else f"❌ ({amount_due})"
            c2.button(btn_text, key=f"pay_{idx}", on_click=toggle_paid, args=(row['TEAM_ID'], current_paid))

            hole_options = ["", "1", "2", "2A", "3", "4", "5", "5A", "6", "7", "7A", "8", "9"]
            try: h_idx = hole_options.index(current_hole_val)
            except: h_idx = 0
                
            # label_visibility="collapsed" hides the word "Hole" to save space
            selected_hole = c3.selectbox("Hole", hole_options, index=h_idx, key=f"h_{idx}", label_visibility="collapsed")
            if selected_hole != current_hole_val:
                update_hole(row['TEAM_ID'], selected_hole)
                st.rerun()

    if st.button("LOGOUT"): nav_to("login")

# --- REGISTRATION ---
elif st.session_state.step == "register_team":
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

# --- LOGIN ---
elif st.session_state.step == "login":
    dot_color = "green" if check_db() else "red"
    st.markdown(f"## ⛳ Scramble Login :{dot_color}[●]")
    
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

# --- VERIFY WEEKLY ENTRY ---
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Weekly Check-In")
    st.subheader(f"Team: {t['PLAYER_1']} & {t['PLAYER_2']}")
    
    s_df = load_sheet(SETUP_URL)
    current_entry = s_df[s_df['TEAM_ID'].astype(str) == str(t['PHONE'])]
    
    if current_entry.empty:
        if st.button("ENTER THIS WEEK'S TOURNAMENT"):
            params = {
                "PHONE": t['PHONE'], "PIN": t['PASSWORD'], 
                "P1": t['PLAYER_1'], "P2": t['PLAYER_2'], "P3": t.get('PLAYER_3', '')
            }
            requests.get(ENTRY_SCRIPT, params=params)
            load_sheet.clear()
            st.rerun()
    else:
        is_paid = str(current_entry.iloc[0].get('PAID', 'FALSE')).upper() == 'TRUE'
        hole = str(current_entry.iloc[0].get('STARTING_HOLE', 'TBD')).replace(".0", "")
        if is_paid:
            st.success(f"✅ PAID - Starting on Hole {hole}")
            if st.button("START SCORING"): nav_to(1)
        else:
            st.warning("⏳ Status: UNPAID. See Admin to pay and get a hole number.")
            if st.button("Refresh"): 
                load_sheet.clear()
                st.rerun()
