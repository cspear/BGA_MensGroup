import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SECURE CONFIG ---
if "gsheet_id" in st.secrets and "script_url" in st.secrets:
    SHEET_ID = st.secrets["gsheet_id"]
    SCRIPT_URL = st.secrets["script_url"]
    ADMIN_PIN = str(st.secrets.get("admin_pin", "9999"))
else:
    st.error("Missing 'gsheet_id' or 'script_url' in Streamlit Secrets!")
    st.stop()

# Public URL for reading setup data
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. MOBILE-FIRST UI STYLING ---
st.markdown("""
    <style>
    .stNumberInput div div input { font-size: 45px !important; height: 90px !important; text-align: center; }
    .stNumberInput button { width: 100px !important; height: 90px !important; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; margin-bottom: 20px; text-align: center;}
    .hole-number { font-size: 50px; font-weight: bold; color: #007bff; text-align: center; margin-bottom: 0px; }
    .par-label { font-size: 20px; text-align: center; color: #666; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = "login"
if 'scores' not in st.session_state:
    # Initialize scores to Par values
    st.session_state.scores = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}

# --- 4. LOGIN & DIAGNOSTICS ---
if st.session_state.step == "login":
    st.title("⛳ Tournament Login")
    pin_input_raw = st.text_input("Enter Team PIN", type="password").strip()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Scoring", use_container_width=True):
            try:
                df_setup = pd.read_csv(SETUP_URL)
                if pin_input_raw == ADMIN_PIN:
                    st.session_state.step = "admin"
                    st.rerun()

                def clean_pin(val):
                    try: return str(int(float(val)))
                    except: return str(val).strip()

                df_setup['PIN_CLEAN'] = df_setup['PIN'].apply(clean_pin)
                user_pin_clean = clean_pin(pin_input_raw)
                match = df_setup[df_setup['PIN_CLEAN'] == user_pin_clean]
                
                if not match.empty:
                    row = match.iloc[0]
                    st.session_state.team_id = str(row['TEAM_ID'])
                    p1, p2 = str(row['PLAYER_1']), str(row['PLAYER_2'])
                    p3 = str(row['PLAYER_3']) if 'PLAYER_3' in row and pd.notna(row['PLAYER_3']) else ""
                    st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 and p3.lower() != 'nan' and p3.strip() != "" else "")
                    st.session_state.start_hole = int(row['STARTING_HOLE'])
                    st.session_state.step = 1 # Move to first hole
                    st.rerun()
                else:
                    st.error("PIN not recognized.")
            except Exception as e:
                st.error("Connection Error.")

    with col2:
        if st.button("Check Connection", use_container_width=True):
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success("Connected!")
                st.write("Columns:", list(test_df.columns))
                st.dataframe(test_df.head(3))
            except Exception as e:
                st.error(f"Error: {e}")

# --- 5. ONE HOLE PER PAGE SCORECARD ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
    
    st.markdown(f"<div class='hole-number'>Hole {h}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='par-label'>Par {HOLE_PARS[h]}</div>", unsafe_allow_html=True)
    
    # Large score selector
    st.session_state.scores[h] = st.number_input("Score", 1, 10, st.session_state.scores[h], key=f"h{h}", label_visibility="collapsed")

    st.write("") # Spacer
    c1, c2 = st.columns(2)
    with c1:
        if h > 1:
            if st.button("⬅️ PREV", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
    with c2:
        label = "REVIEW ➡️" if h == 9 else "NEXT ➡️"
        if st.button(label, use_container_width=True):
            st.session_state.step = h + 1 if h < 9 else "review"
            st.rerun()

# --- 6. REVIEW & SUBMIT PAGE ---
elif st.session_state.step == "review":
    st.title("Final Review")
    st.markdown(f'<div class="team-card"><h3>{st.session_state.names}</h3></div>', unsafe_allow_html=True)
    
    total = sum(st.session_state.scores.values())
    st.metric("Total Score", total, delta=total-36, delta_color="inverse")
    
    # Display a summary table
    df_review = pd.DataFrame([st.session_state.scores.values()], columns=[f"H{i}" for i in range(1,10)])
    st.table(df_review)

    if st.button("FINISH & SUBMIT SCORES", type="primary", use_container_width=True):
        try:
            payload = {
                "TEAM_ID": st.session_state.team_id,
                "TOTAL": total
            }
            # Add each hole score to payload
            for i in range(1, 10):
                payload[f"H{i}"] = st.session_state.scores[i]
            
            # Send to Google Script Bridge
            response = requests.post(SCRIPT_URL, json=payload)
            
            if response.status_code == 200:
                st.balloons()
                st.success("Successfully Submitted! See you at the 19th hole.")
                st.session_state.step = "done"
            else:
                st.error("Submit failed. Contact admin.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- 7. DONE / ADMIN ---
elif st.session_state.step == "done":
    st.title("⛳ Round Complete")
    st.success("Your scores have been recorded.")
    if st.button("Submit another round (Admin only)"):
        st.session_state.step = "login"
        st.rerun()

elif st.session_state.step == "admin":
    st.title("🛠 Admin Dashboard")
    if st.button("← Back to Login"):
        st.session_state.step = "login"
        st.rerun()
    st.write("Current Leaderboard data would load here.")
