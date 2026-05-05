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
@st.cache_data(ttl=5)
def load_sheet(url):
    df = pd.read_csv(url)
    # Clean headers to ensure they are exactly what we expect
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

# --- 3. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'team_data' not in st.session_state: st.session_state.team_data = None

# --- 4. LOGIN SCREEN ---
if st.session_state.step == "login":
    st.title("⛳ Scramble Login")
    phone_in = st.text_input("PHONE NUMBER").strip()
    pass_in = st.text_input("PASSWORD", type="password")

    if st.button("LOGIN / JOIN WEEKLY"):
        if phone_in.lower() == "admin" and str(pass_in) == ADMIN_PIN:
            st.session_state.step = "admin"
            st.rerun()
        
        try:
            m_df = load_sheet(MASTER_URL)
            # Match against PHONE column in Master_Teams
            user = m_df[m_df['PHONE'].astype(str) == phone_in]
            
            if not user.empty and str(user.iloc[0]['PASSWORD']) == str(pass_in):
                st.session_state.team_data = user.iloc[0].to_dict()
                st.session_state.step = "verify_entry"
                st.rerun()
            else:
                st.error("Invalid Credentials.")
        except Exception as e:
            st.error(f"Error connecting to Master_Teams: {e}")

# --- 5. VERIFY WEEKLY ENTRY (Matches your Setup Tab) ---
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Confirm Weekly Entry")
    st.subheader(f"{t['PLAYER_1']} & {t['PLAYER_2']}")
    
    try:
        s_df = load_sheet(SETUP_URL)
        # Look for the phone number in the TEAM_ID column (per your screenshot)
        current_entry = s_df[s_df['TEAM_ID'].astype(str) == str(t['PHONE'])]
        
        if current_entry.empty:
            if st.button("ENTER THIS WEEK'S TOURNAMENT"):
                params = {
                    "PHONE": t['PHONE'], 
                    "P1": t['PLAYER_1'], 
                    "P2": t['PLAYER_2'], 
                    "P3": t.get('PLAYER_3', '')
                }
                requests.get(ENTRY_SCRIPT, params=params)
                st.success("Entry Sent! Refreshing...")
                st.rerun()
        else:
            # Check PAID status and STARTING_HOLE from Setup tab
            is_paid = str(current_entry.iloc[0].get('PAID', 'FALSE')).upper() == 'TRUE'
            hole = current_entry.iloc[0].get('STARTING_HOLE', 'TBD')
            
            if is_paid:
                st.success(f"✅ PAID - You are starting on Hole {hole}")
                if st.button("START SCORING"):
                    st.session_state.step = 1
                    st.rerun()
            else:
                st.warning("⏳ Status: UNPAID. Please see Admin to unlock scoring.")
                if st.button("Check Status Again"): st.rerun()
    except Exception as e:
        st.error(f"Setup sheet error: {e}")

# --- 6. ADMIN VIEW ---
elif st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    if st.button("LOGOUT"):
        st.session_state.step = "login"
        st.rerun()
    
    try:
        s_df = load_sheet(SETUP_URL)
        unpaid = s_df[s_df['PAID'].astype(str).str.upper() == 'FALSE']
        st.subheader("Unpaid Teams")
        if unpaid.empty:
            st.write("No unpaid teams.")
        else:
            st.dataframe(unpaid[['TEAM_ID', 'PLAYER_1', 'PLAYER_2']])
    except:
        st.write("Could not load Setup data.")
