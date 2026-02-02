import yfinance as yf
import pandas as pd
import requests
import streamlit as st
from io import StringIO
from utils.constants import NSE_INDICES_URLS, GOLD_PROXY, USD_INR_TICKER, TROY_OZ_TO_GRAMS

@st.cache_data(ttl=300)
def get_live_price(ticker):
    """Get live price for a single ticker"""
    if not ticker:
        return None
        
    symbol = format_ticker(ticker)
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except Exception:
        pass
    return None

@st.cache_data(ttl=60)
def get_live_prices_bulk(tickers):
    """Get live prices for multiple tickers in parallel"""
    if not tickers:
        return {}
    
    # Format all tickers
    symbols = [format_ticker(t) for t in tickers]
    formatted_str = " ".join(symbols)
    
    try:
        # Use bulk download
        data = yf.download(formatted_str, period="1d", threads=True, progress=False)
        
        # Helper to extract last price
        def get_last_price(df_or_series):
            if df_or_series.empty:
                return None
            return df_or_series.iloc[-1]

        results = {}
        
        # yfinance structure depends on number of tickers
        if len(symbols) == 1:
            sym = symbols[0]
            if 'Close' in data:
                 # Check if it's a series or dataframe
                 val = data['Close']
                 if isinstance(val, pd.Series):
                      results[sym] = val.iloc[-1]
                 else:
                      results[sym] = val.iloc[-1]
        else:
             if 'Close' in data:
                 close_data = data['Close']
                 for sym in symbols:
                     if sym in close_data:
                         results[sym] = close_data[sym].iloc[-1]
                     else:
                         results[sym] = None
        
        return results
    except Exception as e:
        print(f"Bulk fetch error: {e}")
        return {}


def format_ticker(ticker):
    """Ensure NSE tickers have .NS suffix"""
    ticker = str(ticker).strip().upper()
    
    # Known NSE keywords/patterns if not already suffixed
    nse_keywords = ['HDFC', 'RELI', 'ITC', 'LICI', 'NIFTY', 'BANK', 'SGB', 'GOLDBEES', 'SILVER', 'TATVA']
    
    if not ticker.endswith('.NS') and not ticker.endswith('.BO') and not '=' in ticker and not ticker.startswith('^'):
        # Heuristic: if it looks like an Indian stock, add .NS
        if any(k in ticker for k in nse_keywords) or len(ticker) < 10: # Assuming short tickers are likely symbols
             return f"{ticker}.NS"
             
    return ticker

@st.cache_data(ttl=300)
def get_gold_metrics():
    """Fetch Comex Gold, USD/INR and calculate Gold INR/gram"""
    try:
        gold = yf.Ticker(GOLD_PROXY).history(period="1d")
        usd = yf.Ticker(USD_INR_TICKER).history(period="1d")
        
        if not gold.empty and not usd.empty:
            price_usd_oz = gold['Close'].iloc[-1]
            usd_inr = usd['Close'].iloc[-1]
            
            price_inr_gram = (price_usd_oz * usd_inr) / TROY_OZ_TO_GRAMS
            
            return {
                'usd_oz': price_usd_oz,
                'usd_inr': usd_inr,
                'inr_gram': price_inr_gram
            }
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600)
def get_nse_stock_list(index_name):
    """Fetch list of stocks for a given NSE Index"""
    urls = NSE_INDICES_URLS.get(index_name, [])
    
    # Generic headers to avoid blocking
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.content.decode('utf-8')))
                
                # Find symbol column
                col = next((c for c in df.columns if 'symbol' in c.lower()), None)
                if col:
                    symbols = df[col].dropna().unique().tolist()
                    # Add .NS
                    return [f"{s}.NS" for s in symbols]
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue
            
    return []

def get_historical_data(tickers, period="1y"):
    """Fetch historical data for multiple tickers"""
    try:
        if isinstance(tickers, list):
            tickers_str = " ".join(tickers)
        else:
            tickers_str = tickers
            
        data = yf.download(tickers_str, period=period, progress=False)
        
        # Handle multi-index columns if essential
        if 'Adj Close' in data:
            return data['Adj Close']
        elif 'Close' in data:
            return data['Close']
        else:
            return data
    except Exception:
        return pd.DataFrame()

def calculate_relative_return(df):
    """Calculate relative return (cumulative product of pct_change)"""
    if df.empty:
        return df
    
    rel = df.pct_change()
    cumret = (1 + rel).cumprod() - 1
    return cumret.fillna(0)
