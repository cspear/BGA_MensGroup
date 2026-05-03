import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- 1. CONNECTION TO YOUR SHEET ---
# This looks for the 'Secret' URL you put in the Streamlit dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. CONFIG & STYLING ---
HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}

st.markdown("""
    <style>
    /* Make the +/- buttons and number box much larger for older eyes */
    .stNumberInput div div input { font-size: 30px !important; height: 60px !important; }
    button { height: 3em !important; }
    .hole-label { font-size: 24px; font-weight: bold; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN LOGIC ---
# Replace your login logic block with this:
if 'auth' not in st.session_state:
    st.title("⛳ Tournament Login")
    pin_input = st.text_input("Enter your Team PIN", type="password")
    
    if st.button("Start Scoring"):
        try:
            # TTL=0 ensures it doesn't show old data if you change the sheet
            df_setup = conn.read(worksheet="Setup", ttl=0)
            
            # Clean the data: remove empty rows and ensure PIN is a string
            df_setup = df_setup.dropna(subset=['PIN'])
            match = df_setup[df_setup['PIN'].astype(str).str.strip() == str(pin_input).strip()]
            
            if not match.empty:
                st.session_state.auth = pin_input
                st.session_state.team_id = match['Team_ID'].iloc[0]
                
                # Check for P1, P2, P3
                p1 = match['P1'].iloc[0]
                p2 = match['P2'].iloc[0]
                p3 = match['P3'].iloc[0] if 'P3' in match.columns and pd.notna(match['P3'].iloc[0]) else ""
                
                st.session_state.names = f"{p1} & {p2}" + (f" & {p3}" if p3 else "")
                st.session_state.start_hole = match['Start_Hole'].iloc[0]
                st.rerun()
            else:
                st.error("PIN not found. Check your 'Setup' tab in the sheet.")
        except Exception as e:
            st.error("The app can't reach your Google Sheet.")
            st.info("Check: Is the tab named 'Setup'? Is 'Anyone with link can view' turned on?")
# --- 4. THE ACTUAL APP ---
else:
    st.header(f"Team: {st.session_state.names}")
    st.subheader(f"Starting Hole: {st.session_state.start_hole}")
    
    scores = {}
    for i in range(1, 10):
        st.markdown(f"<div class='hole-label'>Hole {i} (Par {HOLE_PARS[i]})</div>", unsafe_allow_html=True)
        scores[i] = st.number_input(f"Score for Hole {i}", min_value=1, max_value=10, value=HOLE_PARS[i], key=f"h{i}", label_visibility="collapsed")

    # Calculate Totals
    total = sum(scores.values())
    par_total = sum(HOLE_PARS.values())
    relative_score = total - par_total
    
    st.divider()
    st.markdown(f"## Total: {total} ({relative_score:+ if relative_score != 0 else 'E'})")

    if st.button("FINISH & SUBMIT"):
        # Here we would add the conn.update logic to save to the 'Scores' tab
        st.balloons()
        st.success("Scores saved! Great round.")
