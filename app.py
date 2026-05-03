import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SECURE CONFIG ---
if "gsheet_id" in st.secrets:
    SHEET_ID = st.secrets["gsheet_id"]
    ADMIN_PIN = str(st.secrets.get("admin_pin", "9999"))
else:
    st.error("Missing 'gsheet_id' in Streamlit Secrets!")
    st.stop()

# Using the official connection for writing, and CSV for fast reading
conn = st.connection("gsheets", type=GSheetsConnection)
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stNumberInput div div input { font-size: 35px !important; height: 75px !important; }
    .stNumberInput button { width: 80px !important; height: 75px !important; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; }
    .hole-label { font-size: 26px; font-weight: bold; margin-bottom: -15px; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN & DIAGNOSTICS ---
if 'auth' not in st.session_state:
    st.title("⛳ Tournament Login")
    pin_input_raw = st.text_input("Enter Team PIN", type="password").strip()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Scoring"):
            try:
                df_setup = pd.read_csv(SETUP_URL)
                if pin_input_raw == ADMIN_PIN:
                    st.session_state.auth = "admin"
                    st.rerun()

                # Robust PIN cleaning
                def clean_pin(val):
                    try: return str(int(float(val)))
                    except: return str(val).strip()

                df_setup['PIN_CLEAN'] = df_setup['PIN'].apply(clean_pin)
                user_pin_clean = clean_pin(pin_input_raw)
                
                match = df_setup[df_setup['PIN_CLEAN'] == user_pin_clean]
                
                if not match.empty:
                    row = match.iloc[0]
                    st.session_state.auth = user_pin_clean
                    st.session_state.team_id = row['TEAM_ID']
                    p1, p2 = str(row['P1']), str(row['P2'])
                    p3 = str(row['P3']) if 'P3' in row and pd.notna(row['P3']) else ""
                    st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 and p3.lower() != 'nan' else "")
                    st.session_state.start_hole = int(row['START_HOLE'])
                    st.rerun()
                else:
                    st.error("PIN not recognized.")
            except Exception as e:
                st.error("Connection Failed. Check your Column Headers in the sheet.")

    with col2:
        if st.button("Check Connection"):
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success("Connected!")
                st.write("Columns found (Should be ALL CAPS):", list(test_df.columns))
                st.dataframe(test_df.head(3))
            except Exception as e:
                st.error(f"Error: {e}")

# --- 4. PLAYER SCORECARD ---
elif st.session_state.auth != "admin":
    st.markdown(f'<div class="team-card"><h2>{st.session_state.names}</h2>'
                f'Starting Hole: <b>{st.session_state.start_hole}</b></div>', unsafe_allow_html=True)
    
    HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
    scores = {}
    for i in range(1, 10):
        st.markdown(f"<div class='hole-label'>Hole {i} (Par {HOLE_PARS[i]})</div>", unsafe_allow_html=True)
        scores[i] = st.number_input(f"H{i}", 1, 10, HOLE_PARS[i], key=f"h{i}", label_visibility="collapsed")
        st.divider()

    total = sum(scores.values())
    if st.button("FINISH & SUBMIT SCORES"):
        try:
            # Prepare data for SCORES tab
            new_data = pd.DataFrame([{
                "TEAM_ID": st.session_state.team_id,
                "TOTAL": total,
                "TIMESTAMP": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **{f"H{i}": scores[i] for i in range(1, 10)}
            }])
            conn.update(worksheet="Scores", data=new_data)
            st.balloons()
            st.success("Final Scores Saved! You can close this page.")
        except Exception as e:
            st.error("Submit failed. Admin: Ensure 'Scores' tab exists and sharing is Editor.")

# --- 5. ADMIN DASHBOARD ---
else:
    st.title("🛠 Admin Dashboard")
    if st.button("← Back"):
        del st.session_state.auth
        st.rerun()
    st.write("Leaderboard and Flighting logic goes here.")
