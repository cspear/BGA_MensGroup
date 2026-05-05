import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets.get("admin_pin", "9999"))
# This is the 'POST' version of your form link
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScUZ7SratHRVeibtWRg-iFBKHVTt2ueXpwa5WNRXlgkNaOAng/formResponse"

# Public URL for reading setup data
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. MOBILE UI STYLING ---
st.markdown("""
    <style>
    .stNumberInput div div input { font-size: 45px !important; height: 90px !important; text-align: center; }
    .stNumberInput button { width: 100px !important; height: 90px !important; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; margin-bottom: 20px; text-align: center;}
    .hole-number { font-size: 50px; font-weight: bold; color: #007bff; text-align: center; }
    .par-label { font-size: 20px; text-align: center; color: #666; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "login"
if 'scores' not in st.session_state:
    st.session_state.scores = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}

# --- 4. LOGIN ---
if st.session_state.step == "login":
    st.title("⛳ Tournament Login")
    pin_input = st.text_input("Enter Team PIN", type="password").strip()
    
    if st.button("Start Scoring", use_container_width=True):
        try:
            df = pd.read_csv(SETUP_URL)
            # Master Admin check
            if pin_input == ADMIN_PIN:
                st.session_state.step = "admin"
                st.rerun()

            # PIN Match logic
            df['PIN_STR'] = df['PIN'].astype(str).str.replace('.0', '', regex=False).str.strip()
            match = df[df['PIN_STR'] == pin_input]
            
            if not match.empty:
                row = match.iloc[0]
                st.session_state.team_id = str(row['TEAM_ID'])
                p1, p2 = str(row['PLAYER_1']), str(row['PLAYER_2'])
                st.session_state.names = f"{p1} & {p2}"
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("PIN not found.")
        except:
            st.error("Could not connect to Spreadsheet. Check Sharing settings.")

# --- 5. ONE HOLE PER PAGE ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
    
    st.markdown(f"<div class='hole-number'>Hole {h}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='par-label'>Par {HOLE_PARS[h]}</div>", unsafe_allow_html=True)
    
    st.session_state.scores[h] = st.number_input("Score", 1, 10, st.session_state.scores[h], key=f"h{h}", label_visibility="collapsed")

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

# --- 6. REVIEW & SUBMIT ---
elif st.session_state.step == "review":
    st.title("Review Scores")
    total = sum(st.session_state.scores.values())
    st.markdown(f'<div class="team-card"><h3>{st.session_state.names}</h3></div>', unsafe_allow_html=True)
    st.metric("Total Score", total)
    
    if st.button("SUBMIT FINAL SCORES", type="primary", use_container_width=True):
        # MAPPING YOUR GOOGLE FORM IDs
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
            requests.post(FORM_URL, data=payload)
            st.balloons()
            st.success("Successfully Submitted!")
            st.session_state.step = "done"
        except:
            st.error("Submission failed. Check your internet connection.")

elif st.session_state.step == "done":
    st.title("⛳ Round Complete!")
    st.write("Your scores are recorded. See you at the 19th hole.")

elif st.session_state.step == "admin":
    st.title("🛠 Admin Dashboard")
    if st.button("Logout"):
        st.session_state.step = "login"
        st.rerun()
