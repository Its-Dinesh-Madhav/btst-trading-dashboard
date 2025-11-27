import pandas as pd
import yfinance as yf
from strategy import calculate_strategy_indicators
from streamlit_lightweight_charts import renderLightweightCharts

def plot_stock_chart(symbol):
    """
    Creates a TradingView-style chart using streamlit-lightweight-charts.
    Returns the chart options dictionary.
    """
    try:
        # 1. Fetch Data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo", interval="1d")
        
        if df.empty:
            return None
            
        df.columns = [c.lower() for c in df.columns]
        
        # 2. Calculate Indicators
        df = calculate_strategy_indicators(df)
        
        # 3. Format Data for Lightweight Charts
        # Needs list of dicts: time (YYYY-MM-DD), open, high, low, close
        candle_data = []
        tsl_data = []
        markers = []
        
        for index, row in df.iterrows():
            time_str = index.strftime('%Y-%m-%d')
            
            # Candle
            candle_data.append({
                'time': time_str,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })
            
            # TSL Line (only if valid)
            if row['tsl'] > 0:
                tsl_data.append({
                    'time': time_str,
                    'value': row['tsl']
                })
                
        # Buy Markers
        # Logic: Crossover of Close > TSL (and prev Close < prev TSL)
        for i in range(1, len(df)):
            prev_close = df['close'].iloc[i-1]
            prev_tsl = df['tsl'].iloc[i-1]
            curr_close = df['close'].iloc[i]
            curr_tsl = df['tsl'].iloc[i]
            time_str = df.index[i].strftime('%Y-%m-%d')
            
            if prev_close < prev_tsl and curr_close > curr_tsl:
                markers.append({
                    'time': time_str,
                    'position': 'belowBar',
                    'color': '#2196F3', # Blue
                    'shape': 'arrowUp',
                    'text': 'BUY'
                })

        # 4. Chart Configuration
        chartOptions = {
            "layout": {
                "textColor": 'white',
                "background": {
                    "type": 'solid',
                    "color": '#131722' # TV Dark Theme
                }
            },
            "grid": {
                "vertLines": {"color": "#333"},
                "horzLines": {"color": "#333"},
            },
            "height": 500
        }
        
        seriesCandle = [{
            "type": 'Candlestick',
            "data": candle_data,
            "options": {
                "upColor": '#26a69a',
                "downColor": '#ef5350',
                "borderVisible": False,
                "wickUpColor": '#26a69a',
                "wickDownColor": '#ef5350'
            },
            "markers": markers
        }]
        
        seriesTSL = [{
            "type": 'Line',
            "data": tsl_data,
            "options": {
                "color": 'blue',
                "lineWidth": 2,
                "title": "TSL"
            }
        }]
        
        return {
            "chartOptions": chartOptions,
            "series": seriesCandle + seriesTSL
        }
        
    except Exception as e:
        print(f"Chart Error: {e}")
        return None
