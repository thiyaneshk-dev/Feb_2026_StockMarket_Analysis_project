import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_handler import parse_holdings_csv
from utils.market_data import get_live_price, get_gold_metrics, format_ticker
from utils.db import init_db, save_portfolio_db, get_portfolio_db

# Initialize DB
init_db()

st.title("💼 Portfolio Review")

# Load existing portfolio from DB
portfolio_df = get_portfolio_db()

tab1, tab2, tab3 = st.tabs(["📁 Upload Holdings", "📊 Performance View", "🥇 SGB vs Gold"])

# --- TAB 1: UPLOAD ---
with tab1:
    st.header("Upload Holdings CSV")
    st.markdown("Upload your broker's holdings CSV file (e.g., from Zerodha/Groww).")
    
    uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
    
    if uploaded_file:
        parsed_df = parse_holdings_csv(uploaded_file)
        
        if not parsed_df.empty:
            st.success(f"Successfully parsed {len(parsed_df)} holdings.")
            st.dataframe(parsed_df.head())
            
            if st.button("💾 Save to Portfolio"):
                if save_portfolio_db(parsed_df):
                    st.success("Portfolio saved successfully to Database!")
                    st.rerun()
        else:
            st.error("Failed to parse CSV. Please check the format.")

# --- TAB 2: PORTFOLIO VIEW ---
with tab2:
    if portfolio_df.empty:
        st.info("Please upload a holdings file in Tab 1.")
    else:
        st.header("Live Portfolio Performance")
        
        if st.button("🔄 Refresh Prices"):
            st.cache_data.clear()
            st.rerun()
            
        # Processing
        df = portfolio_df.copy()
        
        # Show progress for fetching prices
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        live_prices = []
        for i, ticker in enumerate(df['ticker']):
            status_text.text(f"Fetching price for {ticker}...")
            price = get_live_price(ticker)
            live_prices.append(price)
            progress_bar.progress((i + 1) / len(df))
            
        df['live_price'] = live_prices
        status_text.empty()
        progress_bar.empty()
        
        # Calculations
        df['current_value'] = df['shares'] * df['live_price'].fillna(0)
        df['invested_value'] = df['shares'] * df['buy_price']
        df['pnl'] = df['current_value'] - df['invested_value']
        df['pnl_pct'] = (df['pnl'] / df['invested_value'] * 100).fillna(0)
        
        # Metrics
        total_invested = df['invested_value'].sum()
        total_current = df['current_value'].sum()
        total_pnl = df['pnl'].sum()
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested", f"₹{total_invested:,.0f}")
        col2.metric("Current Value", f"₹{total_current:,.0f}")
        col3.metric("Total P&L", f"₹{total_pnl:,.0f}", f"{total_pnl_pct:.2f}%")
        
        # Table
        st.dataframe(
            df[['ticker', 'shares', 'buy_price', 'live_price', 'current_value', 'pnl_pct']],
            column_config={
                "live_price": st.column_config.NumberColumn("Price", format="₹%.2f"),
                "current_value": st.column_config.NumberColumn("Value", format="₹%.0f"),
                "pnl_pct": st.column_config.NumberColumn("P&L %", format="%.2f%%"),
            },
            use_container_width=True
        )
        
        # Chart
        st.subheader("Asset Allocation")
        fig = px.pie(df, values='current_value', names='ticker', title='Portfolio Allocation')
        st.plotly_chart(fig)

# --- TAB 3: SGB ANALYSIS ---
with tab3:
    if portfolio_df.empty:
        st.info("Upload portfolio first.")
    else:
        sgb_df = portfolio_df[portfolio_df['asset_type'] == 'SGB'].copy()
        
        if sgb_df.empty:
            st.warning("No SGB holdings found in your portfolio.")
        else:
            st.header("🥇 Sovereign Gold Bond Analysis")
            
            # Get Benchmarks
            metrics = get_gold_metrics()
            
            if metrics:
                col1, col2, col3 = st.columns(3)
                col1.metric("Comex Gold ($/oz)", f"${metrics['usd_oz']:.2f}")
                col2.metric("USD/INR", f"₹{metrics['usd_inr']:.2f}")
                col3.metric("Gold Benchmark (₹/g)", f"₹{metrics['inr_gram']:.0f}")
                
                # SGB Computations
                total_grams = sgb_df['shares'].sum()
                theoretical_value = total_grams * metrics['inr_gram']
                
                # For SGBs, we might not get live prices easily if they are illiquid, 
                # but let's assume we fetched them in Tab 2 logic (or re-fetch here if needed).
                # For now, let's reuse logic:
                sgb_df['live_price'] = sgb_df['ticker'].apply(get_live_price)
                sgb_df['market_value'] = sgb_df['shares'] * sgb_df['live_price'].fillna(0)
                actual_value = sgb_df['market_value'].sum()
                
                premium = actual_value - theoretical_value
                premium_pct = (premium / theoretical_value * 100) if theoretical_value > 0 else 0
                
                st.divider()
                c1, c2, c3 = st.columns(3)
                c1.metric("Your Gold (Grams)", f"{total_grams:.0f}g")
                c2.metric("Theoretical Value (Pure Gold)", f"₹{theoretical_value:,.0f}")
                c3.metric("Actual SGB Market Value", f"₹{actual_value:,.0f}", f"{premium_pct:.1f}% vs Gold")
                
                st.info(f"Market Gap: ₹{premium:,.0f} ({'Premium' if premium > 0 else 'Discount'})")
                
            else:
                st.warning("Could not fetch gold benchmark data (GC=F / INR=X).")
