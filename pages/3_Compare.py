import streamlit as st
import pandas as pd
import plotly.express as px
from utils.market_data import get_nse_stock_list, get_historical_data, calculate_relative_return, format_ticker
from utils.constants import NSE_INDICES_URLS

st.title("🚀 Compare Performance")

# 1. Select Index/Universe
indices = list(NSE_INDICES_URLS.keys())
selected_index = st.selectbox("Select Index", indices)

# 2. Fetch Tickers for Index
if selected_index:
    with st.spinner(f"Loading {selected_index} tickers..."):
        available_tickers = get_nse_stock_list(selected_index)
        
    if available_tickers:
        # 3. Select Tickers to Compare
        default_tickers = available_tickers[:3] if len(available_tickers) >=3 else available_tickers
        selected_tickers = st.multiselect(
            "Select Stocks to Compare", 
            options=available_tickers,
            default=default_tickers
        )
        
        if selected_tickers:
            if st.button("Compare", type="primary"):
                with st.spinner("Fetching historical data..."):
                    # Format tickers just in case
                    formatted_tickers = [format_ticker(t) for t in selected_tickers]
                    
                    # Fetch Data (1 Year)
                    df_close = get_historical_data(formatted_tickers, period="1y")
                    
                    if not df_close.empty:
                        # Calculate Relative Return
                        rel_ret = calculate_relative_return(df_close)
                        
                        # Plot
                        st.subheader("Relative Return Comparison (1 Year)")
                        fig = px.line(
                            rel_ret, 
                            title="Cumulative Returns",
                            labels={"value": "Return", "Date": "Date", "variable": "Ticker"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Table
                        st.subheader("Performance Metrics")
                        total_ret = rel_ret.iloc[-1] * 100
                        ret_df = pd.DataFrame(total_ret).reset_index()
                        ret_df.columns = ['Ticker', 'Total Return %']
                        st.dataframe(ret_df.sort_values('Total Return %', ascending=False), hide_index=True)
                        
                    else:
                        st.error("No data fetched.")
    else:
        st.warning("Could not load tickers for this index.")
