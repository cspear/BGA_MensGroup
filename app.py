import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
HOLE_PARS = {1:4, 2:3, 3:5, 4:4, 5:3, 6:4, 7:4, 8:4, 9:4}
# Tie-breaker priority based on your difficulty input (1 is hardest)
TIE_BREAKER_ORDER = [1, 8, 5, 7, 6, 9, 2, 3, 4] 

st.set_page_config(page_title="Golf Scramble", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3em; font-size: 20px; font-weight: bold; }
    .score-box { font-size: 24px; font-weight: bold; color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN SCREEN ---
if 'auth' not in st.session_state:
    st.title("⛳ Weekly Scramble")
    pin_input = st.text_input("Enter Team PIN", type="password")
    if st.button("Login"):
        # Replace this with your Google Sheet lookup logic later
        # For now, testing logic:
        if pin_input: 
            st.session_state.auth = pin_input
            st.rerun()
else:
    # --- SCORECARD APP ---
    st.header(f"Team Scorecard")
    st.info("Starting Hole: 4") # This will be dynamic from your sheet
    
    total_score = 0
    scores = {}
    
    cols = st.columns(3)
    for i in range(1, 10):
        with cols[(i-1)%3]:
            scores[i] = st.number_input(f"Hole {i} (Par {HOLE_PARS[i]})", min_value=1, max_value=10, value=HOLE_PARS[i])
            total_score += scores[i]
    
    par_diff = total_score - sum(HOLE_PARS.values())
    color = "red" if par_diff > 0 else "green"
    
    st.divider()
    st.markdown(f"### Total: {total_score} (<span style='color:{color}'>{par_diff:+}</span>)", unsafe_allow_html=True)
    
    if st.button("Submit Final Scores"):
        st.success("Scores Submitted to Admin!")
        # Logic to write scores back to the 'Scores' tab goes here
