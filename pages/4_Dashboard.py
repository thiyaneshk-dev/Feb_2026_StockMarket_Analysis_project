import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.db import get_historical_data, get_watchlist, get_portfolio_db
from utils.ui_components import render_tradingview_ticker

# Page Config
st.set_page_config(page_title="Deep Dive Dashboard", page_icon="🕵️", layout="wide")

st.title("🕵️ Deep Dive Analysis")

# Sidebar - Ticker Selection
st.sidebar.header("Configuration")

# Get tickers from DB
watchlist_df = get_watchlist()
portfolio_df = get_portfolio_db()

all_tickers = set()
if not watchlist_df.empty:
    all_tickers.update(watchlist_df['ticker'].tolist())
if not portfolio_df.empty:
    all_tickers.update(portfolio_df['ticker'].tolist())

sorted_tickers = sorted(list(all_tickers))

if not sorted_tickers:
    st.warning("No tickers found. Please add stocks to your Watchlist or Portfolio and run the batch job.")
    st.stop()

selected_ticker = st.sidebar.selectbox("Select Ticker", sorted_tickers)

# Log Scale Toggle
use_log_scale = st.sidebar.checkbox("Logarithmic Scale", value=False)

# Main Content
if selected_ticker:
    # 1. TradingView Widget for selected ticker
    # We need to format it for TV: "EXCHANGE:SYMBOL"
    # Assuming .NS suffix -> NSE
    tv_symbol = selected_ticker
    if selected_ticker.endswith(".NS"):
        tv_symbol = f"NSE:{selected_ticker.replace('.NS', '')}"
    elif selected_ticker.endswith(".BO"):
        tv_symbol = f"BSE:{selected_ticker.replace('.BO', '')}"
        
    render_tradingview_ticker([{"proName": tv_symbol, "title": selected_ticker}])
    
    # 2. Fetch Data from DB
    df = get_historical_data(selected_ticker)
    
    if df.empty:
        st.error(f"No historical data found for {selected_ticker}. Please run the batch job.")
    else:
        # Latest Close & Indicators
        latest = df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Close", f"{latest['close']:,.2f}")
        c2.metric("RSI (14)", f"{latest['rsi']:.2f}")
        c3.metric("Slow MA (200)", f"{latest['ma200']:,.2f}")
        # SuperTrend Status
        st_val = latest['supertrend']
        st_color = "green" if latest['close'] > st_val else "red"
        st_status = "Bullish" if latest['close'] > st_val else "Bearish"
        c4.markdown(f"**SuperTrend**: :{st_color}[{st_status}] ({st_val:,.2f})")

        # 3. Interactive Chart & Data Table Layout
        col_chart, col_data = st.columns([3, 1])

        with col_chart:
            # Create subplots: Row 1 = Price, Row 2 = Volume, Row 3 = RSI
            fig = make_subplots(
                rows=3, cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.6, 0.2, 0.2],
                subplot_titles=(f"{selected_ticker} Price Action", "Volume", "RSI")
            )

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df['date'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'],
                name='OHLC'
            ), row=1, col=1)

            # Overlays: MA50, MA200, SuperTrend
            fig.add_trace(go.Scatter(x=df['date'], y=df['ma50'], line=dict(color='orange', width=1), name='MA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['ma200'], line=dict(color='blue', width=2), name='MA 200'), row=1, col=1)
            
            # SuperTrend (Green/Red dots or line)
            # Ensure mode is lines so it draws even if points are close
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['supertrend'], 
                line=dict(color='purple', dash='dot', width=2), 
                mode='lines',
                name='SuperTrend'
            ), row=1, col=1)

            # Volume
            colors = ['red' if row['open'] - row['close'] > 0 else 'green' for index, row in df.iterrows()]
            fig.add_trace(go.Bar(x=df['date'], y=df['volume'], marker_color=colors, name='Volume'), row=2, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], line=dict(color='purple', width=2), name='RSI'), row=3, col=1)
            # RSI Levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

            # Layout Updates
            fig.update_layout(height=800, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=40, b=20))
            
            if use_log_scale:
                fig.update_yaxes(type="log", row=1, col=1)

            st.plotly_chart(fig, use_container_width=True)
            st.caption("Charts powered by Plotly & DuckDB")

        with col_data:
            st.subheader("📋 Data View")
            # Prepare display dataframe
            display_df = df[['date', 'close', 'rsi', 'supertrend', 'volume']].sort_values(by='date', ascending=False)
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                display_df, 
                use_container_width=True, 
                height=800,
                column_config={
                    "close": st.column_config.NumberColumn("Close", format="%.2f"),
                    "rsi": st.column_config.NumberColumn("RSI", format="%.1f"),
                    "supertrend": st.column_config.NumberColumn("ST", format="%.2f"),
                    "volume": st.column_config.NumberColumn("Vol", format="%d compact"),
                }
            )
