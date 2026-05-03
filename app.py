import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. SECURE CONFIG ---
if "gsheet_id" in st.secrets:
    SHEET_ID = st.secrets["gsheet_id"]
    ADMIN_PIN = str(st.secrets.get("admin_pin", "9999")) # Default to 9999
else:
    st.error("Missing 'gsheet_id' in Streamlit Secrets!")
    st.stop()

SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stNumberInput div div input { font-size: 35px !important; height: 75px !important; }
    .stNumberInput button { width: 80px !important; height: 75px !important; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; }
    .admin-box { background-color: #fff3cd; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN & DIAGNOSTICS ---
if 'auth' not in st.session_state:
    st.title("⛳ Tournament Login")
    pin_input = st.text_input("Enter Team PIN", type="password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Scoring"):
            try:
                # Standard Login Flow
                df_setup = pd.read_csv(SETUP_URL)
                
                # Check for Master Admin PIN first
                if pin_input == ADMIN_PIN:
                    st.session_state.auth = "admin"
                    st.rerun()
                
                # Check for Team PIN
                match = df_setup[df_setup['PIN'].astype(str).str.strip() == str(pin_input).strip()]
                if not match.empty:
                    st.session_state.auth = pin_input
                    st.session_state.team_id = match['Team_ID'].iloc[0]
                    p1, p2 = str(match['P1'].iloc[0]), str(match['P2'].iloc[0])
                    p3 = str(match['P3'].iloc[0]) if 'P3' in match.columns and pd.notna(match['P3'].iloc[0]) else ""
                    st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 and p3.lower() != 'nan' else "")
                    st.session_state.start_hole = match['Start_Hole'].iloc[0]
                    st.rerun()
                else:
                    st.error("PIN not found.")
            except Exception as e:
                st.error("Connection Failed. Use 'Check Connection' for details.")

    with col2:
        if st.button("Check Connection"):
            st.info("Diagnostic Info:")
            st.code(f"Target URL: {SETUP_URL}")
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success(f"Successfully reached Sheet! Found {len(test_df)} teams.")
                st.write("First few rows of data:")
                st.dataframe(test_df.head(3))
            except Exception as e:
                st.error(f"Error: {e}")

# --- 4. ADMIN DASHBOARD ---
elif st.session_state.auth == "admin":
    st.title("🛠 Admin Dashboard")
    if st.button("← Back to Scoring"):
        del st.session_state.auth
        st.rerun()
    
    st.markdown("### Scramble Management")
    # Add your logic here later to see all scores or clear the sheet
    st.write("You are logged in as Admin. This is where you will see the leaderboard later.")

# --- 5. PLAYER SCORECARD ---
else:
    st.markdown(f'<div class="team-card"><h2>{st.session_state.names}</h2>'
                f'Starting Hole: <b>{st.session_state.start_hole}</b></div>', unsafe_allow_html=True)
    
    scores = {}
    for i in range(1, 10):
        st.markdown(f"**Hole {i}**")
        scores[i] = st.number_input(f"H{i}", 1, 10, 4, key=f"h{i}", label_visibility="collapsed")
        st.divider()

    if st.button("FINISH & SUBMIT"):
        st.balloons()
        st.success("Scores Submitted!")
