import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets["admin_pin"])
ENTRY_SCRIPT = st.secrets["entry_script_url"]

MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble Pro", layout="wide")

# --- 2. STYLING ---
st.markdown("""
    <style>
    .section-break { border-bottom: 3px solid #444; margin: 10px 0; }
    .stButton > button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA HELPERS ---
@st.cache_data(ttl=1)
def load_sheet(url):
    df = pd.read_csv(url).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

def check_db():
    try: return requests.head(MASTER_URL, timeout=2).status_code == 200
    except: return False

# --- 4. APP LOGIC ---
db_status = "🟢" if check_db() else "🔴"
st.markdown(f"## ⛳ Scramble Management {db_status}")

if 'step' not in st.session_state: st.session_state.step = "login"

# --- ADMIN DASHBOARD ---
if st.session_state.step == "admin":
    tab1, tab2, tab3, tab4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    s_df = load_sheet(SETUP_URL)
    
    with tab1:
        st.subheader("Tournament Check-In")
        # Format for display: Combine names and handle sorting
        s_df['HOLE_SORT'] = s_df['STARTING_HOLE'].astype(str)
        s_df = s_df.sort_values(by='HOLE_SORT')

        for idx, row in s_df.iterrows():
            # Show all 3 player names
            p3 = f", {row['PLAYER_3']}" if row['PLAYER_3'] else ""
            st.write(f"**Team:** {row['PLAYER_1']}, {row['PLAYER_2']}{p3}")
            
            c1, c2, c3 = st.columns([2, 2, 1])
            
            # Paid Status Toggle
            current_paid = str(row['PAID']).upper() == "TRUE"
            if c1.button(f"{'✅ PAID' if current_paid else '❌ UNPAID'}", key=f"pay_{idx}"):
                new_status = "FALSE" if current_paid else "TRUE"
                requests.get(ENTRY_SCRIPT, params={"ACTION": "UPDATE_TEAM", "PHONE": row['TEAM_ID'], "PAID": new_status})
                st.rerun()

            # Hole Selection (including A options)
            hole_options = ["", "1", "2", "2A", "3", "4", "5", "5A", "6", "7", "7A", "8", "9"]
            current_hole = str(row['STARTING_HOLE']).replace(".0", "")
            try:
                h_idx = hole_options.index(current_hole)
            except:
                h_idx = 0
                
            new_hole = c2.selectbox("Hole", hole_options, index=h_idx, key=f"hole_{idx}")
            if new_hole != current_hole:
                requests.get(ENTRY_SCRIPT, params={"ACTION": "UPDATE_TEAM", "PHONE": row['TEAM_ID'], "HOLE": new_hole})
                st.rerun()
            
            st.markdown("<div class='section-break'></div>", unsafe_allow_html=True)

    if st.button("LOGOUT"):
        st.session_state.step = "login"
        st.rerun()

# (Login & Registration logic remains exactly as previous verified version)
elif st.session_state.step == "login":
    # ... previous login code ...
    pass
