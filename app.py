import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets.get("admin_pin", "1102"))
FORM_URL = st.secrets["form_url"].strip() # .strip() removes accidental spaces
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stButton > button { width: 100% !important; font-size: 20px !important; height: 60px !important; border-radius: 10px !important; }
    div[data-testid="stHorizontalBlock"] div.stButton > button { background-color: #007bff !important; color: white !important; font-size: 40px !important; height: 100px !important; }
    .floating-digit { font-size: 100px; font-weight: bold; color: #007bff; display: block; text-align: center; line-height: 100px; }
    .team-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #007bff; margin-bottom: 20px; text-align: center; }
    .hole-number { font-size: 50px; font-weight: bold; color: #333; text-align: center; }
    .par-label { font-size: 22px; text-align: center; color: #666; margin-bottom: 20px; }
    .player-header { text-align: center; margin-bottom: 20px; color: #444; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "login"
if 'scores' not in st.session_state:
    st.session_state.scores = {i: 4 for i in range(1, 10)}

# --- 4. LOGIN ---
if st.session_state.step == "login":
    st.title("⛳ Tournament Login")
    pin_input = st.text_input("Enter Team PIN", type="password").strip()
    
    c_a, c_b = st.columns(2)
    with c_a:
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
    with c_b:
        if st.button("Test Connection", use_container_width=True):
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success(f"✅ Connected! Sample: {test_df['PLAYER_1'].iloc[0]}")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

# --- 5. SCORING ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
    st.markdown(f"<div class='player-header'><h3>{st.session_state.names}</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hole-number'>Hole {h}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='par-label'>Par {HOLE_PARS[h]}</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("−", key=f"m_{h}"):
            if st.session_state.scores[h] > 1:
                st.session_state.scores[h] -= 1
                st.rerun()
    with col2:
        st.markdown(f"<span class='floating-digit'>{st.session_state.scores[h]}</span>", unsafe_allow_html=True)
    with col3:
        if st.button("+", key=f"p_{h}"):
            if st.session_state.scores[h] < 20:
                st.session_state.scores[h] += 1
                st.rerun()

    st.write("---")
    n1, n2 = st.columns(2)
    with n1:
        if st.button("⬅️ PREV"):
            st.session_state.step = 9 if h == 1 else h - 1
            st.rerun()
    with n2:
        if st.button("NEXT ➡️"):
            st.session_state.step = 1 if h == 9 else h + 1
            st.rerun()
    if st.button("GO TO REVIEW PAGE"):
        st.session_state.step = "review"
        st.rerun()

# --- 6. REVIEW ---
elif st.session_state.step == "review":
    st.title("Review Scores")
    total = sum(st.session_state.scores.values())
    cols = st.columns(3)
    for i in range(1, 10):
        with cols[(i-1)%3]:
            st.metric(f"Hole {i}", st.session_state.scores[i])
    st.markdown(f'<div class="team-card"><h4>Team Total</h4><h2>{total}</h2></div>', unsafe_allow_html=True)
    if st.button("⬅️ BACK TO SCORING"):
        st.session_state.step = st.session_state.start_hole_const
        st.rerun()
    if st.button("🏁 FINISH & SUBMIT", type="primary"):
        payload = {
            "entry.355673787": st.session_state.team_id,
            "entry.766763420": str(total)
        }
        e_map = {1:"570799081", 2:"1718629908", 3:"1485908234", 4:"1352458145", 5:"1082590215", 6:"1051512403", 7:"1802952445", 8:"1396264906", 9:"2066803273"}
        for i in range(1, 10):
            payload[f"entry.{e_map[i]}"] = str(st.session_state.scores[i])
        
        try:
            # Added headers to look like a browser
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            r = requests.post(FORM_URL, data=payload, headers=headers)
            if r.status_code == 200:
                st.balloons()
                st.session_state.step = "done"
                st.rerun()
            else:
                st.error(f"Error {r.status_code}. Please check Form Privacy Settings.")
        except Exception as e:
            st.error(f"Failed: {e}")

elif st.session_state.step == "done":
    st.title("⛳ Round Complete!")
    st.success("Scores Submitted.")
