import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_handler import parse_watchlist_csv
from utils.market_data import format_ticker, get_live_price, get_historical_data
from utils.indicators import calculate_all_indicators
from utils.db import init_db, get_watchlist, add_ticker, remove_ticker

# Initialize DB
init_db()

st.title("🔍 Watchlist & Research")

# Load existing watchlist
watchlist_df = get_watchlist()

tab1, tab2, tab3 = st.tabs(["📁 Manage Watchlist", "📊 Live Metrics", "📈 Technical Analysis"])

# --- TAB 1: MANAGE WATCHLIST ---
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Add Ticker")
        new_ticker = st.text_input("Enter Ticker (e.g., INFY, TCS.NS)").strip().upper()
        if st.button("➕ Add Ticker"):
             if new_ticker:
                 if add_ticker(new_ticker):
                     st.success(f"Added {new_ticker}")
                     st.rerun()
                 else:
                     st.warning("Ticker already exists.")
        
        st.divider()
        st.header("Upload CSV")
        uploaded_file = st.file_uploader("Upload simple CSV (one ticker per line)", type=['csv'])
        if uploaded_file:
            parsed_df = parse_watchlist_csv(uploaded_file)
            if not parsed_df.empty:
                count = 0
                for t in parsed_df['ticker']:
                     if add_ticker(t):
                         count += 1
                st.success(f"Imported {count} new tickers.")
                st.rerun()
    
    with col2:
        st.header("Current Watchlist")
        if not watchlist_df.empty:
             for idx, row in watchlist_df.iterrows():
                 c1, c2 = st.columns([0.8, 0.2])
                 c1.text(row['ticker'])
                 if c2.button("🗑️", key=f"del_{row['ticker']}"):
                     remove_ticker(row['ticker'])
                     st.rerun()
        else:
             st.info("Watchlist is empty.")

# --- TAB 2: LIVE METRICS ---
with tab2:
    if watchlist_df.empty:
        st.info("Watchlist is empty.")
    else:
        if st.button("Refresh Data", key='refresh_wl'):
             st.cache_data.clear()
             st.rerun()
             
        st.write("Fetching live prices...")
        
        results = []
        progress = st.progress(0)
        
        for i, row in watchlist_df.iterrows():
             ticker = row['ticker']
             price = get_live_price(ticker)
             results.append({'Ticker': ticker, 'Price': price})
             progress.progress((i+1)/len(watchlist_df))
             
        progress.empty()
        res_df = pd.DataFrame(results)
        
        st.dataframe(
            res_df, 
            column_config={
                "Price": st.column_config.NumberColumn("Price", format="₹%.2f")
            },
            use_container_width=True
        )

# --- TAB 3: TECHNICAL ANALYSIS ---
with tab3:
    if watchlist_df.empty:
         st.info("Watchlist is empty.")
    else:
        selected_ticker = st.selectbox("Select Ticker", watchlist_df['ticker'].tolist())
        
        if selected_ticker:
            formatted_ticker = format_ticker(selected_ticker)
            st.markdown(f"**Analyzing {formatted_ticker}...**")
            
            # Fetch History
            try:
                # Need YF Ticker object for indicators usually, but our market_data wrapper returns simple data
                # We need O/H/L/C for SuperTrend
                import yfinance as yf
                full_hist = yf.Ticker(formatted_ticker).history(period="2y") # Increased history for EMA/MA
                
                if not full_hist.empty:
                    indicators = calculate_all_indicators(full_hist)
                    
                    # Display Indicators
                    c1, c2, c3, c4 = st.columns(4)
                    cur_price = full_hist['Close'].iloc[-1]
                    
                    c1.metric("Current Price", f"₹{cur_price:.2f}")
                    c2.metric("RSI (14)", f"{indicators['rsi']:.1f}" if indicators['rsi'] else "N/A")
                    c3.metric("MA 50", f"₹{indicators['ma50']:.1f}" if indicators['ma50'] else "N/A")
                    c4.metric("MA 200", f"₹{indicators['ma200']:.1f}" if indicators['ma200'] else "N/A")
                    
                    # Signals
                    st.subheader("Signals")
                    col1, col2 = st.columns(2)
                    with col1:
                        # RSI Interpretation
                        rsi = indicators['rsi']
                        if rsi:
                            if rsi > 70: st.warning(f"⚠️ Overbought (RSI: {rsi:.0f})")
                            elif rsi < 30: st.success(f"✅ Oversold (RSI: {rsi:.0f})")
                            else: st.info(f"Neutral (RSI: {rsi:.0f})")
                    
                    with col2:
                        # Trend Interpretation (using 10,3 as primary)
                        st_val = indicators['st_10_3'][-1] if indicators['st_10_3'] else None
                        if st_val:
                            trend = "Bullish 🐂" if cur_price > st_val else "Bearish 🐻"
                            st.metric("SuperTrend (10,3)", trend, f"Level: {st_val:.2f}")

                    # Charting
                    st.subheader("Interactive Chart")
                    
                    # Date Range Slider
                    # Zoom to last 6 months by default
                    
                    fig = go.Figure()
                    
                    # Candlestick
                    fig.add_trace(go.Candlestick(
                        x=full_hist.index,
                        open=full_hist['Open'],
                        high=full_hist['High'],
                        low=full_hist['Low'],
                        close=full_hist['Close'],
                        name='Price'
                    ))
                    
                    # SuperTrends - Add traces only if data exists
                    colors = {'st_10_2': 'blue', 'st_10_3': 'purple', 'st_20_5': 'green'}
                    for st_key, color in colors.items():
                        if indicators.get(st_key):
                            fig.add_trace(go.Scatter(
                                x=full_hist.index, 
                                y=indicators[st_key], 
                                name=f"SuperTrend ({st_key.replace('st_', '').replace('_', ',')})", 
                                line=dict(width=1, dash='dot', color=color)
                            ))
                    
                    # Moving Averages
                    if indicators.get('ma50_series') is not None:
                         fig.add_trace(go.Scatter(x=full_hist.index, y=indicators['ma50_series'], name='MA 50', line=dict(color='orange', width=1)))
                    
                    if indicators.get('ma200_series') is not None:
                         fig.add_trace(go.Scatter(x=full_hist.index, y=indicators['ma200_series'], name='MA 200', line=dict(color='red', width=1)))

                    # EMA
                    if indicators.get('ema20_series') is not None:
                         fig.add_trace(go.Scatter(x=full_hist.index, y=indicators['ema200_series'], name='EMA 20', line=dict(color='cyan', width=1)))

                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=700,
                        title=f"{formatted_ticker} Technical Chart",
                        yaxis_title="Price",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                         
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error("No data found.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")
