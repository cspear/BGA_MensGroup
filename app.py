import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets["admin_pin"])
ENTRY_SCRIPT = st.secrets["entry_script_url"]
FORM_URL = st.secrets["form_url"]

# Data URLs
MASTER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Master_Teams"
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"
COURSE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Course_Data"
SCORES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Scores"

st.set_page_config(page_title="Golf Scramble Pro", layout="centered")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stButton > button { width: 100% !important; border-radius: 10px !important; }
    /* Scoring Button Style */
    div[data-testid="stHorizontalBlock"] div.stButton > button { 
        background-color: #007bff !important; color: white !important; font-size: 45px !important; height: 100px !important; 
    }
    .floating-digit { font-size: 100px; font-weight: bold; color: #007bff; display: block; text-align: center; line-height: 100px; }
    .hole-nav { background-color: #f8f9fa; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .admin-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    .birdie { border: 2px solid #007bff; border-radius: 50%; padding: 5px; }
    .bogey { border: 2px solid #dc3545; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "login"
if 'scores' not in st.session_state: st.session_state.scores = {i: 4 for i in range(1, 10)}
if 'team_data' not in st.session_state: st.session_state.team_data = None

# --- 4. NAVIGATION LOGIC ---
def nav_to(step):
    st.session_state.step = step
    st.rerun()

# --- 5. LOGIN SCREEN ---
if st.session_state.step == "login":
    st.title("⛳ Scramble Login")
    phone_in = st.text_input("PHONE NUMBER").strip()
    pass_in = st.text_input("PASSWORD", type="password")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("LOGIN / JOIN WEEKLY"):
            if phone_in.lower() == "admin" and str(pass_in) == ADMIN_PIN:
                nav_to("admin")
            try:
                m_df = pd.read_csv(MASTER_URL)
                m_df['PHONE'] = m_df['PHONE'].astype(str).str.strip()
                user = m_df[m_df['PHONE'] == phone_in]
                if not user.empty and str(user.iloc[0]['PASSWORD']) == str(pass_in):
                    st.session_state.team_data = user.iloc[0]
                    nav_to("verify_entry")
                else:
                    st.error("Invalid Phone or Password.")
            except:
                st.error("Could not connect to Master Teams list.")
    with c2:
        reg_url = st.secrets.get("reg_form_url", "#")
        st.link_button("NEW TEAM REGISTER", reg_url)

# --- 6. WEEKLY ENTRY VERIFICATION ---
elif st.session_state.step == "verify_entry":
    t = st.session_state.team_data
    st.title("Confirm Weekly Entry")
    st.subheader(f"{t['PLAYER_1']} & {t['PLAYER_2']}")
    st.write(f"Email: {t['EMAIL']}")
    
    if st.button("ENTER THIS WEEK'S TOURNAMENT", type="primary"):
        params = {"PHONE": t['PHONE'], "P1": t['PLAYER_1'], "P2": t['PLAYER_2']}
        try:
            r = requests.get(ENTRY_SCRIPT, params=params)
            if "Success" in r.text:
                st.success("Entry Confirmed! Please see Admin to pay and get your hole.")
                if st.button("Back to Login"): nav_to("login")
            else:
                st.error("Submission failed.")
        except:
            st.error("Connection Error.")
    
    if st.button("Start Scoring (If Paid/Assigned)"):
        nav_to(1)

# --- 7. SCORING SCREENS (1-9) ---
elif isinstance(st.session_state.step, int) and 1 <= st.session_state.step <= 9:
    h = st.session_state.step
    st.markdown(f"<div class='hole-nav'><h3>Hole {h}</h3></div>", unsafe_allow_html=True)
    
    # Large Score Adjuster
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("−", key=f"min_{h}"):
            if st.session_state.scores[h] > 1: st.session_state.scores[h] -= 1; st.rerun()
    with col2:
        st.markdown(f"<span class='floating-digit'>{st.session_state.scores[h]}</span>", unsafe_allow_html=True)
    with col3:
        if st.button("+", key=f"plus_{h}"):
            if st.session_state.scores[h] < 20: st.session_state.scores[h] += 1; st.rerun()

    # Navigation
    st.write("---")
    n1, n2, n3 = st.columns(3)
    if h > 1: n1.button("⬅ Previous", on_click=nav_to, args=(h-1,))
    if h < 9: n2.button("Next ➡", on_click=nav_to, args=(h+1,))
    else: n3.button("FINISH 🏁", on_click=nav_to, args=("review",))

# --- 8. REVIEW & SUBMIT ---
elif st.session_state.step == "review":
    st.title("Review Scores")
    total = sum(st.session_state.scores.values())
    
    cols = st.columns(3)
    for i in range(1, 10):
        cols[(i-1)%3].metric(f"Hole {i}", st.session_state.scores[i])
    
    st.subheader(f"Total Score: {total}")
    
    if st.button("SUBMIT FINAL SCORECARD", type="primary"):
        # Payload headers must match your doPost logic
        payload = {
            "TEAM_ID": st.session_state.team_data['PHONE'],
            "TOTAL": total
        }
        for i in range(1, 10): payload[f"H{i}"] = st.session_state.scores[i]
        
        try:
            r = requests.post(FORM_URL, data=payload)
            if "Success" in r.text:
                st.balloons()
                st.success("Round Submitted! Great job.")
                if st.button("Logout"): nav_to("login")
            else: st.error("Error submitting.")
        except: st.error("Connection error during submission.")

# --- 9. ADMIN DASHBOARD ---
elif st.session_state.step == "admin":
    st.title("🛠 Admin Dashboard")
    t1, t2, t3, t4 = st.tabs(["💰 CASHIER", "🚀 STARTER", "📊 LEADERBOARD", "⚙️ RESET"])
    
    with t1:
        st.subheader("Unpaid Teams")
        try:
            s_df = pd.read_csv(SETUP_URL)
            unpaid = s_df[s_df['PAID'].astype(str).str.upper() == 'FALSE']
            for _, row in unpaid.iterrows():
                st.markdown(f"<div class='admin-card'><b>{row['PLAYER_1']} & {row['PLAYER_2']}</b></div>", unsafe_allow_html=True)
        except: st.write("No active entries found.")

    with t2:
        st.subheader("Hole Assignments")
        # Logic to display Starting Holes from Setup sheet
    
    with t3:
        st.subheader("Leaderboard (Private)")
        # Sorting and tie-breaker logic will be triggered here
        
    if st.button("LOGOUT"): nav_to("login")
