import streamlit as st

# --- CONFIG ---
HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}

# --- CUSTOM CSS FOR GIANT BUTTONS ---
st.markdown("""
    <style>
    /* Make the number input buttons huge */
    button[step="1"] { width: 60px !important; height: 60px !important; }
    /* Centering and sizing the hole labels */
    .hole-label { font-size: 22px; font-weight: bold; margin-bottom: -10px; }
    /* Team Header */
    .team-header { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'auth' not in st.session_state:
    st.title("⛳ Golf Login")
    pin = st.text_input("Enter Team PIN", type="password")
    if st.button("Access Scorecard"):
        # Logic to pull names from your 'Setup' tab goes here
        st.session_state.auth = pin
        st.session_state.names = "John, Bill, & Dave" # Replace with sheet lookup
        st.session_state.start_hole = 4 # Replace with sheet lookup
        st.rerun()
else:
    # --- TEAM HEADER ---
    st.markdown(f"""
        <div class="team-header">
            <h2 style='margin:0;'>Team: {st.session_state.names}</h2>
            <p style='margin:0; font-size: 18px;'>Starting on <b>Hole {st.session_state.start_hole}</b></p>
        </div>
        """, unsafe_allow_html=True)

    # --- BIG SCORECARD ---
    scores = {}
    for i in range(1, 10):
        # We wrap each hole in a container to give it space
        with st.container():
            st.markdown(f"<div class='hole-label'>Hole {i} (Par {HOLE_PARS[i]})</div>", unsafe_allow_html=True)
            # 'label_visibility' hidden keeps it clean but accessible
            scores[i] = st.number_input(f"H{i}", min_value=1, max_value=10, value=HOLE_PARS[i], key=f"h{i}", label_visibility="collapsed")
            st.divider()

    # --- FOOTER ---
    total = sum(scores.values())
    par_total = sum(HOLE_PARS.values())
    diff = total - par_total
    
    st.markdown(f"### Total Score: {total} ({diff:+ if diff != 0 else 'E'})")
    
    if st.button("SUBMIT FINAL SCORE"):
        st.balloons()
        st.success("Scores Saved! You can close this page.")
