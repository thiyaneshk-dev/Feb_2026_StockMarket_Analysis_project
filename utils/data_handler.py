import pandas as pd
import json
import os
import streamlit as st
from utils.constants import PORTFOLIO_FILE, WATCHLIST_FILE

def parse_holdings_csv(uploaded_file):
    """Parse holdings CSV with robust error handling"""
    try:
        # Read CSV with quote handling
        df = pd.read_csv(uploaded_file, quotechar='"', escapechar='\\')
        
        # Clean column names
        df.columns = [col.strip('"').strip() for col in df.columns]
        
        # Find columns by partial match
        ticker_col = next((c for c in df.columns if 'instrument' in c.lower() or 'symbol' in c.lower()), None)
        qty_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower()), None)
        price_col = next((c for c in df.columns if 'avg' in c.lower() or 'cost' in c.lower() or 'price' in c.lower()), None)
        
        if not all([ticker_col, qty_col, price_col]):
             st.error(f"Required columns not found. Found: {list(df.columns)}")
             return pd.DataFrame()
        
        # Extract and clean data
        holdings = pd.DataFrame({
            'ticker': df[ticker_col].astype(str).str.strip(),
            'shares': pd.to_numeric(df[qty_col], errors='coerce'),
            'buy_price': pd.to_numeric(df[price_col], errors='coerce')
        })
        
        # Identify Asset Type (SGB vs Equity)
        holdings['asset_type'] = holdings['ticker'].apply(
            lambda x: 'SGB' if 'SGB' in x.upper() else 'EQUITY'
        )
        
        # Filter invalid rows
        valid_mask = (
            (holdings['ticker'].str.len() > 0) & 
            (holdings['shares'] > 0) & 
            (holdings['buy_price'] >= 0)
        )
        
        return holdings[valid_mask].reset_index(drop=True)
        
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return pd.DataFrame()

def parse_watchlist_csv(uploaded_file):
    """Parse watchlist CSV (one ticker per line)"""
    try:
        df = pd.read_csv(uploaded_file, header=None, names=['ticker'])
        df['ticker'] = df['ticker'].astype(str).str.strip().str.upper()
        return df[df['ticker'].str.len() > 0].reset_index(drop=True)
    except Exception as e:
        st.error(f"Error parsing Watchlist CSV: {str(e)}")
        return pd.DataFrame()

def save_to_json(data_df, filepath):
    """Save DataFrame to JSON"""
    try:
        data = data_df.to_dict('records')
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving to {filepath}: {e}")
        return False

def load_from_json(filepath):
    """Load DataFrame from JSON"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading {filepath}: {e}")
    return pd.DataFrame()
