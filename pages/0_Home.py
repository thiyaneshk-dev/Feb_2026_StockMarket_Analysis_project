import streamlit as st
import pandas as pd
import requests
from streamlit_lottie import st_lottie
from streamlit_autorefresh import st_autorefresh
from utils.constants import GLOBAL_INDICES
from utils.market_data import get_live_price, format_ticker

# Page Config
st.set_page_config(page_title="Stock Dashboard", page_icon="📈", layout="wide")

# Auto-refresh every 60 seconds
count = st_autorefresh(interval=60 * 1000, limit=None, key="fizzbuzzcounter")

# Helper: Load Lottie
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load Assets
lottie_stock = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_hcipoqvc.json")

# Header Section
col1, col2 = st.columns([1, 2])

with col1:
    if lottie_stock:
        st_lottie(lottie_stock, height=300, key="stock_anim")
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=200)

with col2:
    st.title("🚀 Stock Market Command Center")
    st.markdown("### Welcome to your personal finance dashboard.")
    st.markdown(f"**Last Updated:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
    st.info("💡 Navigate using the sidebar to manage Portfolio, Watchlist, or Compare stocks.")

st.divider()

# Live Market Overview
st.subheader("🌍 Global Market Pulse")

# Fetch Data for Indices
metrics = []
for name, ticker in GLOBAL_INDICES.items():
    price = get_live_price(ticker)
    metrics.append({"Index": name, "Price": price, "Ticker": ticker})

# Display Metrics in Rows of 4
cols = st.columns(5)
for i, metric in enumerate(metrics):
    with cols[i % 5]:
        price_val = metric['Price']
        if price_val:
            st.metric(metric['Index'], f"{price_val:,.2f}")
        else:
            st.metric(metric['Index'], "Loading...")

st.divider()

# Quick Actions
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 💼 Portfolio")
    st.caption("Track your holdings and SGBs.")
    st.page_link("pages/1_Portfolio.py", label="Go to Portfolio", icon="💼")

with c2:
    st.markdown("### 🔍 Watchlist")
    st.caption("Analyze potential investments.")
    st.page_link("pages/2_Watchlist.py", label="Go to Watchlist", icon="🔍")

with c3:
    st.markdown("### 🚀 Compare")
    st.caption("Benchmark stock performance.")
    st.page_link("pages/3_Compare.py", label="Compare Stocks", icon="📈")
