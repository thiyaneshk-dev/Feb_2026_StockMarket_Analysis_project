import pandas as pd
import yfinance as yf
from tqdm import tqdm
import time
from utils.db import init_db, get_watchlist, get_portfolio_db, save_historical_data
from utils.indicators import calculate_all_indicators
from utils.market_data import format_ticker

def get_all_tickers():
    """Get unique tickers from Watchlist and Portfolio"""
    watchlist_df = get_watchlist()
    portfolio_df = get_portfolio_db()
    
    tickers = set()
    
    if not watchlist_df.empty:
        tickers.update(watchlist_df['ticker'].tolist())
        
    if not portfolio_df.empty:
        tickers.update(portfolio_df['ticker'].tolist())
        
    return list(tickers)

def fetch_and_process(ticker):
    """Fetch data, calculate indicators, and save to DB"""
    try:
        formatted_ticker = format_ticker(ticker)
        print(f"Processing {ticker} ({formatted_ticker})...")
        
        # Fetch Data (1 Year)
        # Using auto_adjust=True to get adjusted close as 'Close'
        df = yf.download(formatted_ticker, period="1y", interval="1d", auto_adjust=True, progress=False)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return False
            
        # Ensure flat columns if MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Calculate Indicators
        indicators = calculate_all_indicators(df)
        
        # Add indicators to DataFrame
        # calculate_all_indicators returns dict of Series and latest values
        # We need the Series for historical storage
        
        if 'rsi_series' in indicators:
            df['rsi'] = indicators['rsi_series']
            
        if 'ma50_series' in indicators:
            df['ma50'] = indicators['ma50_series']
            
        if 'ma200_series' in indicators:
            df['ma200'] = indicators['ma200_series']
            
        # For SuperTrend, implementation returns a list, make it a Series
        if 'st_10_3' in indicators:
            df['supertrend'] = pd.Series(indicators['st_10_3'], index=df.index)
            
        # Save to DB
        success = save_historical_data(ticker, df)
        return success
        
    except Exception as e:
        print(f"Failed to process {ticker}: {e}")
        return False

def main():
    print("🚀 Starting Batch Job...")
    
    # Initialize DB to ensure table exists
    init_db()
    
    tickers = get_all_tickers()
    print(f"Found {len(tickers)} unique tickers.")
    
    if not tickers:
        print("No tickers found in DB. Add stocks to Watchlist or Portfolio first.")
        return

    success_count = 0
    with tqdm(total=len(tickers)) as pbar:
        for ticker in tickers:
            if fetch_and_process(ticker):
                success_count += 1
            pbar.update(1)
            time.sleep(0.5) # Slight delay to be nice to API
            
    print(f"✅ Batch Job Completed. Uploaded {success_count}/{len(tickers)} tickers.")

if __name__ == "__main__":
    main()
