import pandas as pd
import numpy as np

def calculate_ma(data, period):
    """Calculate Simple Moving Average"""
    if data is None or len(data) < period:
        return None
    return data.tail(period).mean()

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index (RSI)"""
    if data is None or len(data) < period:
        return None
    
    # Calculate price changes
    delta = data.diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Calculate RS
    rs = gain / loss.replace(0, np.nan)
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Return the last value
    return rsi.iloc[-1]

def calculate_supertrend(ohlc_data, period=10, multiplier=2):
    """Calculate SuperTrend indicator"""
    if ohlc_data is None or len(ohlc_data) < period:
        return None
    
    high = ohlc_data['High']
    low = ohlc_data['Low']
    close = ohlc_data['Close']
    
    # Calculate ATR
    hl_avg = (high + low) / 2
    tr = high - low
    atr = tr.rolling(period).mean()
    
    # Calculate Basic Bands
    basic_ub = hl_avg + multiplier * atr
    basic_lb = hl_avg - multiplier * atr
    
    # Initialize Final Bands
    final_ub = [None] * len(ohlc_data)
    final_lb = [None] * len(ohlc_data)
    
    # Initialize SuperTrend
    supertrend = [None] * len(ohlc_data)
    
    for i in range(len(ohlc_data)):
        if i == 0:
            final_ub[i] = basic_ub.iloc[i]
            final_lb[i] = basic_lb.iloc[i]
            supertrend[i] = final_ub[i]
            continue
            
        # Upper Band Logic
        if basic_ub.iloc[i] < final_ub[i-1] or close.iloc[i-1] > final_ub[i-1]:
            final_ub[i] = basic_ub.iloc[i]
        else:
            final_ub[i] = final_ub[i-1]
            
        # Lower Band Logic
        if basic_lb.iloc[i] > final_lb[i-1] or close.iloc[i-1] < final_lb[i-1]:
            final_lb[i] = basic_lb.iloc[i]
        else:
            final_lb[i] = final_lb[i-1]
            
        # SuperTrend Logic
        if supertrend[i-1] == final_ub[i-1]:
            if close.iloc[i] <= final_ub[i]:
                supertrend[i] = final_ub[i]
            else:
                supertrend[i] = final_lb[i]
        else:
            if close.iloc[i] >= final_lb[i]:
                supertrend[i] = final_lb[i]
            else:
                supertrend[i] = final_ub[i]
                
    return supertrend

def calculate_all_indicators(hist_data):
    """Calculate common indicators for a stock (returns full series for plotting)"""
    if hist_data is None or hist_data.empty:
        return {}
        
    st_10_2 = calculate_supertrend(hist_data, 10, 2)
    st_10_3 = calculate_supertrend(hist_data, 10, 3)
    st_20_5 = calculate_supertrend(hist_data, 20, 5)
    
    return {
        'ma50_series': calculate_ma_series(hist_data['Close'], 50),
        'ma200_series': calculate_ma_series(hist_data['Close'], 200),
        'ema20_series': calculate_ema_series(hist_data['Close'], 20), # Adding EMA20 sample or parameterized?
        'rsi_series': calculate_rsi_series(hist_data['Close'], 14),
        'st_10_2': st_10_2,
        'st_10_3': st_10_3,
        'st_20_5': st_20_5,
        # Latest values for metrics
        'rsi': calculate_rsi(hist_data['Close'], 14),
        'ma50': calculate_ma(hist_data['Close'], 50),
        'ma200': calculate_ma(hist_data['Close'], 200),
    }

def calculate_ma_series(data, period):
    return data.rolling(window=period).mean()

def calculate_ema_series(data, period):
    """Calculate Exponential Moving Average Series"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi_series(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
