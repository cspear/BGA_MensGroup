import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & SECRETS ---
# Ensure these are in your Streamlit Cloud Secrets!
SHEET_ID = st.secrets["gsheet_id"]
ADMIN_PIN = str(st.secrets.get("admin_pin", "9999"))
FORM_URL = st.secrets["form_url"]

# Public URL for reading setup data (Setup tab)
SETUP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Setup"

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- 2. MOBILE-FIRST UI STYLING ---
st.markdown("""
    <style>
    /* Make the +/- buttons huge and blue */
    .stNumberInput button { 
        width: 100px !important; 
        height: 90px !important; 
        background-color: #007bff !important; 
        color: white !important;
    }
    /* Style the number input text */
    .stNumberInput div div input { 
        font-size: 45px !important; 
        height: 90px !important; 
        text-align: center; 
    }
    .team-card { 
        background-color: #f0f2f6; 
        padding: 20px; 
        border-radius: 15px; 
        border-left: 10px solid #007bff; 
        margin-bottom: 20px; 
        text-align: center;
    }
    .hole-number { font-size: 50px; font-weight: bold; color: #007bff; text-align: center; margin-bottom: 0px; }
    .par-label { font-size: 22px; text-align: center; color: #666; margin-bottom: 20px; }
    .player-header { text-align: center; margin-bottom: 20px; color: #444; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = "login"
if 'scores' not in st.session_state:
    # Default scores to standard Pars
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

                # Clean PIN matching logic
                df_setup['PIN_STR'] = df_setup['PIN'].astype(str).str.replace('.0', '', regex=False).str.strip()
                match = df_setup[df_setup['PIN_STR'] == pin_input_raw]
                
                if not match.empty:
                    row = match.iloc[0]
                    st.session_state.team_id = str(row['TEAM_ID'])
                    p1, p2 = str(row['PLAYER_1']), str(row['PLAYER_2'])
                    p3 = str(row['PLAYER_3']) if 'PLAYER_3' in row and pd.notna(row['PLAYER_3']) else ""
                    st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 and p3.lower() != 'nan' and p3.strip() != "" else "")
                    st.session_state.step = 1 
                    st.rerun()
                else:
                    st.error("PIN not recognized.")
            except:
                st.error("Connection error. Ensure Sheet is set to 'Anyone with link can view'.")

    with col2:
        if st.button("Check Connection", use_container_width=True):
            try:
                test_df = pd.read_csv(SETUP_URL)
                st.success("✅ Connected!")
                st.write("Columns:", list(test_df.columns))
                st.write("Live Data Sample:", test_df[['TEAM_ID', 'PLAYER_1']].head(1))
            except Exception as e:
                st.error(f"❌ Failed: {e}")

# --- 5. ONE HOLE PER PAGE ---
elif isinstance(st.session_state.step, int):
    h = st.session_state.step
    HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
    
    # Sticky Header with Player Names
    st.markdown(f"<div class='player-header'><h3>{st.session_state.names}</h3></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='hole-number'>Hole {h}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='par-label'>Par {HOLE_PARS[h]}</div>", unsafe_allow_html=True)
    
    # Large score selector with +/- buttons
    st.session_state.scores[h] = st.number_input(
        "Score", 1, 15, st.session_state.scores[h], step=1, key=f"h{h}", label_visibility="collapsed"
    )

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
    total = sum(st.session_state.scores.values())
    st.markdown(f'<div class="team-card"><h4>Team Score</h4><h2>{total}</h2></div>', unsafe_allow_html=True)
    
    # Summary Table
    df_review = pd.DataFrame([st.session_state.scores.values()], columns=[f"H{i}" for i in range(1,10)])
    st.table(df_review)

    if st.button("🏁 FINISH & SUBMIT SCORES", type="primary", use_container_width=True):
        # The Secret Entry IDs from your Form link
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
            st.success("Successfully Submitted! You can close this page.")
            st.session_state.step = "done"
        except:
            st.error("Error submitting. Please try again.")

elif st.session_state.step == "done":
    st.title("⛳ Done!")
    st.success("Your scores have been recorded.")
    if st.button("New Login"):
        st.session_state.step = "login"
        st.rerun()

elif st.session_state.step == "admin":
    st.title("🛠 Admin Mode")
    if st.button("Logout"):
        st.session_state.step = "login"
        st.rerun()
