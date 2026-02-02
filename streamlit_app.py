import streamlit as st
import os

st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

# Define pages
pg = st.navigation([
    st.Page("pages/0_Home.py", title="Home", icon="🏠"),
    st.Page("pages/1_Portfolio.py", title="Portfolio Review", icon="💼"),
    st.Page("pages/2_Watchlist.py", title="Watchlist & Research", icon="🔍"),
    st.Page("pages/3_Compare.py", title="Compare Performance", icon="🚀"),
])

pg.run()
