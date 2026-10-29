import streamlit as st

CSS = '''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family: 'DM Sans', system-ui, sans-serif;}
.stApp {background: #F6F8FC; color: #203047;}
[data-testid="stSidebar"] {background: #102338;}
[data-testid="stSidebar"] * {color: #e5ecf4 !important;}
[data-testid="stSidebarNavLink"][aria-current="page"] {background: #203e58;}
.block-container {max-width: 1220px; padding-top: 2.1rem; padding-bottom: 3rem;}
h1, h2, h3 {letter-spacing: -0.025em; color: #14273B;}
[data-testid="stMetric"] {background: #fff; border: 1px solid #E4E9F2; border-radius: 13px; padding: 13px 18px;}
[data-testid="stMetricLabel"] {font-weight: 600;}
[data-testid="stForm"], [data-testid="stExpander"] {border: 1px solid #E4E9F2; background: #FFF; border-radius: 13px;}
.stButton > button[kind="primary"] {background: #176f8e; border-color: #176f8e; border-radius: 8px; font-weight: 650;}
.stButton > button {border-radius: 8px;}
[data-testid="stDataFrame"] {background: white; border-radius: 10px;}
.hero {padding: 1.35rem 1.6rem; background: linear-gradient(100deg,#112B43,#244B61); border-radius: 16px; margin-bottom: 1.5rem;}
.hero h1 {color:#FFF; margin: 0; font-size: 2rem;}
.hero p {color:#d8e7ec; margin: .55rem 0 0 0; font-size: .99rem;}
.pill {display: inline-block; padding: .25rem .65rem; border-radius: 20px; background: #E1F2F0; color: #175C62; font-size:.84rem; font-weight:700;}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {padding-top:1.3rem;}
</style>
'''


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, description):
    # title and description authored by project, never from user fields
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{description}</p></div>', unsafe_allow_html=True)
