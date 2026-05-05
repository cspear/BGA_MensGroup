import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets.get("admin_pin", "9999"))
FORM_URL = st.secrets["form_url"] # Must end in /formResponse
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. MOBILE-FIRST UI STYLING ---
st.markdown("""
    <style>
    .stNumberInput button { width: 100px !important; height: 90px !important; background-color: #007bff !important; color: white !important; }
    .stNumberInput div div input { font-size: 45px !important; height: 90px !important; text-align: center; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; margin-bottom: 20px; text-align: center; }
    .hole-number { font-size: 50px; font-weight: bold; color: #007bff; text-align: center; margin-bottom: 0px; }
    .par-label { font-size: 22px; text-align: center; color: #666; margin-bottom: 20px; }
    .player-header { text-align: center; margin-bottom: 20px; color: #444; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "login"
if 'scores' not in st.session_state:
    st.session_state.scores = {i: 4 for i in range(1, 10)}

# --- 4. LOGIN & CONNECTION TEST ---
if st.session_state.step == "login":
    st.title("⛳ Tournament Login")
    pin_input = st.text_input("Enter Team PIN", type="password").strip()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Scoring", use_container_width=True):
            try:
                df = pd.read_csv(SETUP_URL)
                if pin_input == ADMIN_PIN:
                    st.session_state.step = "admin"
                    st.rerun()

                df['PIN_STR'] = df['PIN'].astype(str).str.replace('.0', '', regex=False).str.strip()
                match = df[df['PIN_STR'] == pin_input]
                
                if not match.empty:
                    row = match.iloc[0]
                    st.session_state.team_id = str(row['TEAM_ID'])
                    st.session_state.names = f"{row['PLAYER_1']} & {row['PLAYER_2']}"
                    st.session_state.step = int(row['STARTING_HOLE'])
                    st.session_state.start_hole_const = int(row['STARTING_HOLE'])
                    st.rerun()
                else:
                    st.error("PIN not recognized.")
            except:
                st.error("Connection error.")

    with col2:
        if st.button("Check Connection", use_container_width=True):
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success("✅ Connected!")
                st.write("Columns:", list(test_df.columns))
            except Exception as e:
                st.error(f"❌ Failed: {e}")

# --- 5. SCORING PAGE ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
    st.markdown(f"<div class='player-header'><h3>{st.session_state.names}</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hole-number'>Hole {h}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='par-label'>Par {HOLE_PARS[h]}</div>", unsafe_allow_html=True)
    
    st.session_state.scores[h] = st.number_input("Score", 1, 15, st.session_state.scores[h], step=1, key=f"h{h}", label_visibility="collapsed")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ PREV", use_container_width=True):
            st.session_state.step = 9 if h == 1 else h - 1
            st.rerun()
    with c2:
        if st.button("NEXT ➡️", use_container_width=True):
            st.session_state.step = 1 if h == 9 else h + 1
            st.rerun()
            
    if st.button("GO TO REVIEW PAGE", use_container_width=True):
        st.session_state.step = "review"
        st.rerun()

# --- 6. REVIEW & SUBMIT ---
elif st.session_state.step == "review":
    st.title("Review Scores")
    total = sum(st.session_state.scores.values())
    
    cols = st.columns(3)
    for i in range(1, 10):
        with cols[(i-1)%3]:
            st.metric(f"Hole {i}", st.session_state.scores[i])
            
    st.markdown(f'<div class="team-card"><h4>Tournament Total</h4><h2>{total}</h2></div>', unsafe_allow_html=True)

    if st.button("⬅️ BACK TO SCORING", use_container_width=True):
        st.session_state.step = 1 # Returns to Hole 1
        st.rerun()

    if st.button("🏁 FINISH & SUBMIT", type="primary", use_container_width=True):
        # Using the exact IDs from your pre-filled link
        payload = {
            "entry.355673787": st.session_state.team_id,
            "entry.570799081": st.session_state.scores[1],
            "entry.1718629908": st.session_state.scores[2],
            "entry.1485908234": st.session_state.scores[3],
            "entry.1352458145": st.session_state.scores[4],
            "entry.1082590215": st.session_state.scores[5],
            "entry.1051512403": st.session_state.scores[6],
            "entry.1802952445": st.session_state.scores[7],
            "entry.1396264906": st.session_state.scores[8],
            "entry.2066803273": st.session_state.scores[9],
            "entry.766763420": total
        }
        
        try:
            r = requests.post(FORM_URL, data=payload)
            if r.status_code == 200:
                st.balloons()
                st.session_state.step = "done"
                st.rerun()
            else:
                st.error(f"Submission failed. Server responded with: {r.status_code}")
        except Exception as e:
            st.error(f"Submission Error: {e}")

elif st.session_state.step == "done":
    st.title("⛳ Success!")
    st.success("Your scores are submitted. Good game!")
