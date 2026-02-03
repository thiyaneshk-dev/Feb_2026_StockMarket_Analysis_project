import streamlit as st
import pandas as pd
import requests
from streamlit_lottie import st_lottie
from streamlit_autorefresh import st_autorefresh
from utils.constants import GLOBAL_INDICES
from utils.market_data import get_live_price, get_live_prices_bulk, format_ticker

# Page Config
st.set_page_config(page_title="Stock Dashboard", page_icon="📈", layout="wide")

# Helper: Load Lottie
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load Assets
lottie_stock = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_hcipoqvc.json")

# Header Section
# ... imports remain same ...

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

# ------------------------------------------------------------------------------
# DETAILED MARKET PULSE (Python - Cached)
# ------------------------------------------------------------------------------
st.subheader("📊 Detailed Market Pulse (Cached)")
st.caption("Data fetched via Yahoo Finance (15-min delayed for some indices). Refreshes every 5 seconds.")

@st.fragment(run_every=5)
def render_market_pulse():
    # Fetch Data for Indices in Bulk
    tickers = list(GLOBAL_INDICES.values())
    bulk_data = get_live_prices_bulk(tickers)
    
    metrics = []
    for name, ticker in GLOBAL_INDICES.items():
        formatted_ticker = format_ticker(ticker)
        data = bulk_data.get(formatted_ticker)
        
        if data and isinstance(data, dict):
             metrics.append({
                 "Index": name, 
                 "Price": data.get('price'), 
                 "Change": data.get('change', 0.0), 
                 "Pct": data.get('pct', 0.0), 
                 "Ticker": ticker
             })
        else:
             # Fallback if data is missing or unexpected format
             metrics.append({"Index": name, "Price": None, "Ticker": ticker})

    # Display Metrics in Rows of 5
    cols = st.columns(5)
    for i, metric in enumerate(metrics):
        with cols[i % 5]:
            price_val = metric['Price']
            if price_val is not None:
                change = metric.get('Change', 0.0)
                pct = metric.get('Pct', 0.0)
                st.metric(
                    label=metric['Index'], 
                    value=f"{price_val:,.2f}", 
                    delta=f"{change:+.2f} ({pct:+.2f}%)"
                )
            else:
                st.metric(metric['Index'], "Loading...")

render_market_pulse()

st.divider()

import streamlit.components.v1 as components
from utils.ui_components import render_tradingview_ticker

# ------------------------------------------------------------------------------
# TRADINGVIEW WIDGETS (Real-time Streaming)
# ------------------------------------------------------------------------------

# ROW 1: INDIA INDICES
india_tickers = [
    { "proName": "NSE:NIFTY", "title": "Nifty 50" },
    { "proName": "NSE:BANKNIFTY", "title": "Bank Nifty" },
    { "proName": "NSE:NIFTYNEXT50", "title": "Nifty Next 50" },
    { "proName": "NSE:CNXIT", "title": "Nifty IT" },
    { "proName": "BSE:SENSEX", "title": "Sensex" }
]
render_tradingview_ticker(india_tickers, "🇮🇳 Indian Market Pulse")

# ROW 2: US TECH & INDICES
us_tickers = [
    { "proName": "FOREXCOM:SPXUSD", "title": "S&P 500" },
    { "proName": "NASDAQ:IXIC", "title": "NASDAQ" },
    { "proName": "NASDAQ:META", "title": "Meta" },
    { "proName": "NASDAQ:GOOGL", "title": "Google" },
    { "proName": "NASDAQ:AAPL", "title": "Apple" },
    { "proName": "NASDAQ:AMZN", "title": "Amazon" },
    { "proName": "NASDAQ:TSLA", "title": "Tesla" },
    { "proName": "NASDAQ:MSFT", "title": "Microsoft" }
]
render_tradingview_ticker(us_tickers, "🇺🇸 US Tech & Indices")

# ROW 3: COMMODITIES
commodity_tickers = [
    { "proName": "TVC:GOLD", "title": "Gold" },
    { "proName": "TVC:SILVER", "title": "Silver" },
    { "proName": "TVC:USOIL", "title": "Crude Oil" }
]
render_tradingview_ticker(commodity_tickers, "🛢️ Commodities")

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
