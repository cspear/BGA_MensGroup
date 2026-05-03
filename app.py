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
    # Using a numeric-style input or stripping text to keep it flexible
    pin_input_raw = st.text_input("Enter Team PIN", type="password").strip()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Scoring"):
            if not pin_input_raw:
                st.warning("Please enter a PIN.")
                st.stop()
                
            try:
                # 1. Fetch the data
                df_setup = pd.read_csv(SETUP_URL)
                
                # 2. Check for Master Admin PIN (Exact string match)
                if pin_input_raw == ADMIN_PIN:
                    st.session_state.auth = "admin"
                    st.rerun()
                
                # 3. ROBUST MATCHING LOGIC:
                # We convert BOTH the sheet column and the user input to numeric strings.
                # This ignores if the sheet thinks it's 1234, 1234.0, or "1234".
                def clean_pin(val):
                    try:
                        # Convert to float first (to handle 1234.0), then int, then string
                        return str(int(float(val)))
                    except:
                        return str(val).strip()

                df_setup['PIN_CLEAN'] = df_setup['PIN'].apply(clean_pin)
                user_pin_clean = clean_pin(pin_input_raw)
                
                # 4. Search for the match
                match = df_setup[df_setup['PIN_CLEAN'] == user_pin_clean]
                
                if not match.empty:
                    row = match.iloc[0]
                    st.session_state.auth = user_pin_clean
                    st.session_state.team_id = row['Team_ID']
                    
                    p1 = str(row['P1'])
                    p2 = str(row['P2'])
                    p3 = str(row['P3']) if 'P3' in row and pd.notna(row['P3']) else ""
                    
                    st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 and p3.lower() != 'nan' else "")
                    st.session_state.start_hole = int(row['Start_Hole'])
                    st.rerun()
                else:
                    st.error(f"PIN '{pin_input_raw}' not recognized. Try again or see Admin.")
            except Exception as e:
                st.error("Error accessing PIN data.")
                st.write(e)

    with col2:
        if st.button("Check Connection"):
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success("Connected!")
                st.write("Columns found:", list(test_df.columns))
                st.dataframe(test_df.head(5))
            except Exception as e:
                st.error(f"Connection Error: {e}")

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
