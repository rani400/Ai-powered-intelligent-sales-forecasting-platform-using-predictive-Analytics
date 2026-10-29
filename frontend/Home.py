"""Four-page app shell. Modules 5–6 are intentionally NOT exposed."""
import streamlit as st
from frontend.components.style import apply_style

st.set_page_config(page_title='SalesGenie AI', page_icon='◈', layout='wide', initial_sidebar_state='expanded')
apply_style()
with st.sidebar:
    st.markdown('### ◈ SalesGenie AI')
    st.caption('Lead intelligence · Milestone 1–2')
    st.divider()

nav = st.navigation([
    st.Page('pages/1_Lead_Management.py', title='Lead Management', icon=':material/contacts:'),
    st.Page('pages/2_Lead_Intelligence.py', title='Lead Intelligence', icon=':material/psychology:'),
    st.Page('pages/3_AI_Outreach.py', title='AI Outreach', icon=':material/mail:'),
    st.Page('pages/4_Lead_Scoring.py', title='Lead Scoring', icon=':material/insights:'),
])
nav.run()
