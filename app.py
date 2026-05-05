import streamlit as st
import pandas as pd
import requests
import time

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets.get("admin_pin", "1102"))
FORM_URL = st.secrets["form_url"].strip()

# Data URLs
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"
MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
COURSE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Course_Data"
SCORES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201"

st.set_page_config(page_title="Golf Scramble Pro", layout="centered")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stButton > button { width: 100% !important; border-radius: 10px !important; }
    /* Big Buttons for Scoring */
    div[data-testid="stHorizontalBlock"] div.stButton > button { 
        background-color: #007bff !important; color: white !important; font-size: 45px !important; height: 100px !important; 
    }
    .floating-digit { font-size: 100px; font-weight: bold; color: #007bff; display: block; text-align: center; line-height: 100px; }
    .player-header { text-align: center; margin-bottom: 20px; color: #444; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    .admin-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'scores' not in st.session_state: st.session_state.scores = {i: 4 for i in range(1, 10)}

# --- 4. LOGIN & MASTER TEAM LOOKUP ---
if st.session_state.step == "login":
    st.title("⛳ Scramble Login")
    email_in = st.text_input("EMAIL").lower().strip()
    pass_in = st.text_input("PASSWORD", type="password")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("LOGIN / JOIN WEEKLY", use_container_width=True):
            if email_in == "admin" and pass_in == ADMIN_PIN:
                st.session_state.step = "admin"
                st.rerun()
            try:
                master_df = pd.read_csv(MASTER_URL)
                # Filter using capitalized headers
                user = master_df[master_df['EMAIL'] == email_in]
                
                if not user.empty and str(user.iloc[0]['PASSWORD']) == str(pass_in):
                    st.session_state.team_data = user.iloc[0]
                    st.session_state.step = "verify_entry"
                    st.rerun()
                else:
                    st.error("Invalid Credentials.")
            except:
                st.error("Error connecting to Master Teams list.")
    with c2:
        if st.button("NEW TEAM REGISTER"):
            st.info("Direct players to your Registration Form link.")

# --- 5. VERIFY WEEKLY ENTRY ---
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Confirm Weekly Entry")
    st.write(f"**Team Members:** {t['PLAYER_1']} & {t['PLAYER_2']}")
    
    if st.button("ENTER THIS WEEK'S TOURNAMENT"):
        # This is where you would trigger a webhook or log to the Setup sheet
        st.success("Entry Received! Please see Admin to pay $40 and get your starting hole.")
        if st.button("Back to Login"):
            st.session_state.step = "login"
            st.rerun()

# --- 6. ADMIN DASHBOARD ---
elif st.session_state.step == "admin":
    st.title("🛠 Admin Command Center")
    tab1, tab2, tab3, tab4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])

    with tab1:
        st.subheader("Payment Collection")
        try:
            setup_df = pd.read_csv(SETUP_URL)
            unpaid = setup_df[setup_df['PAID'] == False]
            for idx, row in unpaid.iterrows():
                with st.container():
                    st.markdown(f"<div class='admin-card'><b>{row['PLAYER_1']} & {row['PLAYER_2']}</b></div>", unsafe_allow_html=True)
                    if st.button(f"MARK PAID: {row['TEAM_ID']}", key=f"pay_{idx}"):
                        st.success(f"Payment logged for Team {row['TEAM_ID']}")
        except:
            st.write("No unpaid teams found.")

    with tab2:
        st.subheader("Hole Assignments")
        st.write("Assign holes to teams that have confirmed payment.")

    with tab3:
        st.subheader("Private Leaderboard")
        # sorting logic for circles/boxes and tie-breakers goes here
        st.write("Leaderboard will populate as scores are submitted.")

    with tab4:
        if st.button("LOGOUT"):
            st.session_state.step = "login"
            st.rerun()

# --- 7. SCORING MODE (RETENTION OF PREVIOUS WORK) ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    st.markdown(f"<div class='hole-number'>Hole {h}</div>", unsafe_allow_html=True)
    
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
    # (Rest of scoring nav follows same as previous approved version)
