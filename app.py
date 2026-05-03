import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & SECRETS ---
# Ensure "gsheet_id" is set in your Streamlit Secrets
if "gsheet_id" in st.secrets:
    SHEET_ID = st.secrets["gsheet_id"]
else:
    st.error("Missing 'gsheet_id' in Streamlit Secrets!")
    st.stop()

# URL format to pull tabs as CSV (Bulletproof for older users/spotty signal)
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}

st.set_page_config(page_title="Club Golf Scramble", layout="centered")

# --- 2. GIANT BUTTON STYLING ---
st.markdown("""
    <style>
    /* Make the +/- buttons and number box massive */
    .stNumberInput div div input { font-size: 35px !important; height: 75px !important; }
    .stNumberInput button { width: 80px !important; height: 75px !important; }
    .hole-label { font-size: 26px; font-weight: bold; margin-bottom: -15px; margin-top: 15px; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN LOGIC ---
if 'auth' not in st.session_state:
    st.title("⛳ Tournament Login")
    pin_input = st.text_input("Enter Team PIN", type="password")
    
    if st.button("Start Scoring"):
        try:
            # Direct read bypassing the library's HTTP handshake
            df_setup = pd.read_csv(SETUP_URL)
            df_setup = df_setup.dropna(subset=['PIN'])
            
            match = df_setup[df_setup['PIN'].astype(str).str.strip() == str(pin_input).strip()]
            
            if not match.empty:
                st.session_state.auth = pin_input
                st.session_state.team_id = match['Team_ID'].iloc[0]
                
                # Dynamic Name Logic
                p1 = str(match['P1'].iloc[0])
                p2 = str(match['P2'].iloc[0])
                p3 = str(match['P3'].iloc[0]) if 'P3' in match.columns and pd.notna(match['P3'].iloc[0]) else ""
                
                st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 and p3.lower() != 'nan' else "")
                st.session_state.start_hole = match['Start_Hole'].iloc[0]
                st.rerun()
            else:
                st.error("PIN not found. Check with the Admin.")
        except Exception as e:
            st.error("Cannot reach the spreadsheet.")
            st.info("Check: Is the tab named 'Setup'? Is 'Anyone with link can view' ON?")

# --- 4. THE SCORECARD APP ---
else:
    st.markdown(f"""
        <div class="team-card">
            <h2 style='margin:0;'>{st.session_state.names}</h2>
            <p style='margin:0; font-size: 20px;'>Starting Hole: <b>{st.session_state.start_hole}</b></p>
        </div>
        """, unsafe_allow_html=True)
    
    scores = {}
    for i in range(1, 10):
        st.markdown(f"<div class='hole-label'>Hole {i} (Par {HOLE_PARS[i]})</div>", unsafe_allow_html=True)
        scores[i] = st.number_input(f"H{i}", 1, 10, HOLE_PARS[i], key=f"h{i}", label_visibility="collapsed")
        st.divider()

    total = sum(scores.values())
    diff = total - sum(HOLE_PARS.values())
    
    st.markdown(f"## Total: {total} ({diff:+ if diff != 0 else 'E'})")

    if st.button("FINISH & SUBMIT"):
        # For PoC, we show success. 
        # Writing back requires the Service Account key we discussed.
        st.balloons()
        st.success(f"Score of {total} locked in for {st.session_state.names}!")
