import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# URLS
NSE_INDICES_URLS = {
    "NIFTY 50": [
        "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    ],
    "NIFTY BANK": [
        "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv"
    ],
    "NIFTY IT": [
        "https://archives.nseindia.com/content/indices/ind_niftyitlist.csv"
    ],
    "NIFTY 500": [
         "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    ],
    "NIFTY NEXT 50": [
        "https://archives.nseindia.com/content/indices/ind_nifty_next50list.csv"
    ]
}

# SGB HANDLING
GOLD_PROXY = "GC=F"
USD_INR_TICKER = "INR=X"
SGB_HOLDINGS_IDENTIFIERS = ["SGB"] # Simplified check
SGB_MAPPING = {
    # Add specific mappings if needed, otherwise rely on string matching 'SGB'
}

# GLOBAL INDICES FOR HOME PAGE
GLOBAL_INDICES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "Agri": "^NSEAGRI",
    "Auto": "^NSEAUTO",
    "Pharma": "^CNXPHARMA",
    "Comex Gold": "GC=F",
    "Silver": "SI=F",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI"
}

# CONSTANTS
TROY_OZ_TO_GRAMS = 31.1035
