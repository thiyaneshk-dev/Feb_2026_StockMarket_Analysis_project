import streamlit.components.v1 as components
import json

def render_tradingview_ticker(symbols: list, title: str = None):
    """
    Render a TradingView Ticker Tape widget.
    
    Args:
        symbols (list): List of dictionaries with 'proName' and 'title'.
                        Example: [{'proName': 'NSE:NIFTY', 'title': 'Nifty 50'}]
        title (str, optional): Title to display above the widget (rendered as subheader).
    """
    if title:
        import streamlit as st
        st.subheader(title)
        
    # Construct the widget HTML
    widget_config = {
        "symbols": symbols,
        "showSymbolLogo": True,
        "isTransparent": False,
        "displayMode": "adaptive",
        "colorTheme": "light",
        "locale": "in"
    }
    
    html_code = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {json.dumps(widget_config)}
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    
    components.html(html_code, height=70)
