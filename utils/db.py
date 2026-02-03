import duckdb
import os
import pandas as pd
from datetime import datetime
from utils.constants import DATA_DIR

DB_FILE = os.path.join(DATA_DIR, "stock_master.duckdb")

def get_connection():
    """Get DuckDB connection"""
    conn = duckdb.connect(DB_FILE)
    return conn

def init_db():
    """Initialize Database Tables"""
    conn = get_connection()
    
    # Watchlist Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker VARCHAR PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Holdings Table (Portfolio)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY,
            ticker VARCHAR,
            shares DOUBLE,
            buy_price DOUBLE,
            asset_type VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create sequence for holdings ID if needed
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_holdings_id START 1")
    
    # Historical Data Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historical_data (
            ticker VARCHAR,
            date TIMESTAMP,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            rsi DOUBLE,
            ma50 DOUBLE,
            ma200 DOUBLE,
            supertrend DOUBLE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    conn.close()

def add_ticker(ticker):
    """Add ticker to watchlist"""
    conn = get_connection()
    try:
        # Check if exists
        exists = conn.execute("SELECT 1 FROM watchlist WHERE ticker = ?", [ticker]).fetchone()
        if not exists:
            conn.execute("INSERT INTO watchlist (ticker) VALUES (?)", [ticker])
            return True
        return False # Already exists
    except Exception as e:
        print(f"Error adding ticker: {e}")
        return False
    finally:
        conn.close()

def remove_ticker(ticker):
    """Remove ticker from watchlist"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", [ticker])
        return True
    finally:
        conn.close()

def get_watchlist():
    """Get all watchlist tickers"""
    conn = get_connection()
    try:
        df = conn.execute("SELECT ticker FROM watchlist ORDER BY ticker").fetchdf()
        return df
    finally:
        conn.close()

def save_portfolio_db(df):
    """Save portfolio dataframe to DB (overwrite mode for now similar to JSON)"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM holdings")
        # DuckDB pandas insert
        conn.register('temp_df', df)
        conn.execute("""
            INSERT INTO holdings (ticker, shares, buy_price, asset_type)
            SELECT ticker, shares, buy_price, asset_type FROM temp_df
        """)
        return True
    except Exception as e:
        print(f"Error saving portfolio: {e}")
        return False
    finally:
        conn.close()

def get_portfolio_db():
    """Get portfolio holdings"""
    conn = get_connection()
    try:
        df = conn.execute("SELECT ticker, shares, buy_price, asset_type FROM holdings").fetchdf()
        return df
    finally:
        conn.close()

def save_historical_data(ticker, df):
    """Save historical data for a ticker (Upsert)"""
    conn = get_connection()
    try:
        # Add ticker column if missing
        df = df.copy()
        df['ticker'] = ticker
        df.reset_index(inplace=True) # Ensure Date is a column if it's index
        
        # Rename columns to match DB schema if needed
        # Expected: Date, Open, High, Low, Close, Volume, ticker, + indicators
        # Mapping standard yfinance/pandas names to lowercase DB columns
        df.columns = [c.lower() for c in df.columns]
        
        # Register for bulk insert
        conn.register('temp_hist', df)
        
        # Delete existing data for this ticker to define clean slate or range? 
        # For simplicity in batch, we can delete entries for this ticker and re-insert 
        # OR use ON CONFLICT DO UPDATE if DuckDB supports it nicely.
        # Let's use Delete + Insert for now to modify full history cleanly.
        conn.execute("DELETE FROM historical_data WHERE ticker = ?", [ticker])
        
        # Insert
        # Only selecting columns that exist in table
        conn.execute("""
            INSERT INTO historical_data (ticker, date, open, high, low, close, volume, rsi, ma50, ma200, supertrend)
            SELECT ticker, date, open, high, low, close, volume, rsi, ma50, ma200, supertrend 
            FROM temp_hist
        """)
        return True
    except Exception as e:
        print(f"Error saving history for {ticker}: {e}")
        return False
    finally:
        conn.close()

def get_historical_data(ticker, limit=365):
    """Get historical data for a ticker"""
    conn = get_connection()
    try:
        df = conn.execute(f"""
            SELECT * FROM historical_data 
            WHERE ticker = ? 
            ORDER BY date ASC
        """, [ticker]).fetchdf()
        return df
    except Exception as e:
        print(f"Error getting history for {ticker}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
