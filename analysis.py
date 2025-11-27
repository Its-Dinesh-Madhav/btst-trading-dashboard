import yfinance as yf
import pandas as pd
import pandas_ta as ta
from textblob import TextBlob
from datetime import datetime, timedelta

def get_stock_news_sentiment(symbol):
    """
    Fetches recent news for a stock and calculates sentiment polarity.
    Returns: (sentiment_score, news_list)
    Score: -1 (Negative) to +1 (Positive)
    """
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            return 0.0, []
            
        sentiment_sum = 0
        count = 0
        processed_news = []
        
        for item in news:
            title = item.get('title', '')
            # Skip non-English or empty titles if needed
            if not title:
                continue
                
            # Calculate sentiment
            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            sentiment_sum += polarity
            count += 1
            
            processed_news.append({
                'title': title,
                'link': item.get('link', '#'),
                'publisher': item.get('publisher', 'Unknown'),
                'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M'),
                'sentiment': polarity
            })
            
        avg_sentiment = sentiment_sum / count if count > 0 else 0.0
        return avg_sentiment, processed_news
        
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return 0.0, []

# ---------------------------------------------------------------------------
# Helper functions for additional technical analysis
# ---------------------------------------------------------------------------

def _weekly_ema_trend(symbol):
    """Calculate weekly EMA-50 and return a simple trend label."""
    try:
        ticker = yf.Ticker(symbol)
        weekly = ticker.history(period="1y", interval="1wk")
        if weekly.empty:
            return "Sideways"
        weekly['ema50'] = weekly['close'].ewm(span=50, adjust=False).mean()
        if len(weekly) < 2:
             return "Sideways"
        # Compare last two EMA values
        if weekly['ema50'].iloc[-1] > weekly['ema50'].iloc[-2]:
            return "Uptrend"
        elif weekly['ema50'].iloc[-1] < weekly['ema50'].iloc[-2]:
            return "Downtrend"
        else:
            return "Sideways"
    except Exception:
        return "Sideways"

def _sector_lookup(symbol, mapping_path="sector_mapping.csv"):
    """Return sector name for a given symbol using a CSV mapping."""
    try:
        df = pd.read_csv(mapping_path)
        row = df.loc[df['symbol'] == symbol]
        if not row.empty:
            return row.iloc[0]['sector']
        return "Unknown"
    except Exception:
        return "Unknown"

def _vwap(df):
    """Calculate Volume-Weighted Average Price for the most recent day."""
    try:
        tp = (df['high'] + df['low'] + df['close']) / 3
        vwap = (tp * df['volume']).sum() / df['volume'].sum()
        return float(vwap)
    except Exception:
        return None

def _atr(df, period=14):
    """Calculate Average True Range using pandas-ta."""
    try:
        atr_series = df.ta.atr(length=period)
        return float(atr_series.iloc[-1])
    except Exception:
        return None

def _candlestick_pattern(df):
    """Detect simple bullish engulfing pattern or hammer."""
    try:
        if len(df) < 2:
            return "None"
        prev = df.iloc[-2]
        cur = df.iloc[-1]
        
        # Bullish Engulfing
        if prev['open'] > prev['close'] and cur['close'] > cur['open']:
            if cur['open'] <= prev['close'] and cur['close'] >= prev['open']:
                return "Bullish Engulfing"
                
        # Hammer
        body = abs(cur['close'] - cur['open'])
        lower_shadow = cur['open'] - cur['low'] if cur['close'] >= cur['open'] else cur['close'] - cur['low']
        if body < (cur['high'] - cur['low']) * 0.3 and lower_shadow > body * 2:
            return "Hammer"
            
        return "None"
    except Exception:
        return "None"

def _risk_reward(symbol, df, price):
    """Calculate stop-loss (recent 14-day low), target (1.5x risk) and R:R ratio."""
    try:
        recent_low = df['low'].rolling(window=14).min().iloc[-1]
        risk = price - recent_low
        if risk <= 0:
            return (None, None, None)
        target = price + 1.5 * risk
        rr = (target - price) / risk
        return (float(recent_low), float(target), float(rr))
    except Exception:
        return (None, None, None)

def get_general_market_news():
    """
    Fetches general market news (using Nifty 50 index as proxy).
    """
    try:
        ticker = yf.Ticker("^NSEI")
        news = ticker.news
        
        formatted_news = []
        for item in news:
            # Handle nested structure (common in new yfinance versions)
            content = item.get('content', item)
            
            # Title
            title = content.get('title')
            
            # Link
            link = None
            if 'clickThroughUrl' in content:
                link = content['clickThroughUrl'].get('url')
            elif 'canonicalUrl' in content:
                link = content['canonicalUrl'].get('url')
            else:
                link = content.get('link')
                
            # Publisher
            publisher = "Unknown"
            if 'provider' in content:
                publisher = content['provider'].get('displayName')
            else:
                publisher = content.get('publisher')
                
            if title and link:
                formatted_news.append({
                    'title': title,
                    'link': link,
                    'publisher': publisher,
                    'publishTime': content.get('pubDate')
                })
                
        return formatted_news
    except Exception:
        return []

def get_sector_performance(limit=50):
    """
    Fetches daily % change for stocks and aggregates by sector.
    Returns a DataFrame suitable for a Treemap.
    """
    try:
        # 1. Load Sector Map
        mapping_df = pd.read_csv("sector_mapping.csv")
        symbols = mapping_df['symbol'].tolist()[:limit]
        
        if not symbols:
            return pd.DataFrame()
            
        # 2. Batch Download
        # threads=True uses yfinance's internal threading
        data = yf.download(symbols, period="5d", progress=False)
        
        # yfinance returns a MultiIndex DataFrame if multiple symbols:
        # Columns: (Price, Ticker) e.g. ('Close', 'RELIANCE.NS')
        # Or just (Price) if single symbol.
        
        results = []
        
        # Check if we got data
        if data.empty:
            return pd.DataFrame()
            
        # Extract Close prices
        try:
            close_data = data['Close']
        except KeyError:
            # Fallback if 'Close' not found (sometimes lowercase 'close')
            if 'close' in data.columns:
                close_data = data['close']
            else:
                return pd.DataFrame()

        for sym in symbols:
            try:
                # Get series for this symbol
                if isinstance(close_data, pd.DataFrame) and sym in close_data.columns:
                    series = close_data[sym]
                elif isinstance(close_data, pd.Series) and len(symbols) == 1:
                    series = close_data
                else:
                    continue
                    
                # Drop NaNs
                series = series.dropna()
                
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    
                    if curr == 0 or pd.isna(curr) or pd.isna(prev):
                        continue
                        
                    change = ((curr - prev) / prev) * 100
                    sector = _sector_lookup(sym)
                    
                    results.append({
                        'Symbol': sym, 
                        'Sector': sector, 
                        'Change': change, 
                        'Price': float(curr)
                    })
            except Exception:
                continue
                    
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"Heatmap Error: {e}")
        return pd.DataFrame()

def _calculate_macd(df):
    """Calculates MACD, MACD Histogram, and MACD Signal."""
    # Default lengths: fast=12, slow=26, signal=9
    df.ta.macd(append=True)
    
    # Find the correct column names dynamically
    macd_cols = [col for col in df.columns if 'MACD_' in col and 'H' not in col and 'S' not in col]
    macdh_cols = [col for col in df.columns if 'MACDH_' in col]
    macds_cols = [col for col in df.columns if 'MACDS_' in col]

    if not macd_cols or not macdh_cols or not macds_cols:
        return {'macd': None, 'macdh': None, 'macds': None}

    return {
        'macd': df[macd_cols[0]].iloc[-1],
        'macdh': df[macdh_cols[0]].iloc[-1],
        'macds': df[macds_cols[0]].iloc[-1]
    }

def _calculate_bollinger_bands(df):
    """Calculates Bollinger Bands (BBANDS)."""
    # Default lengths: length=20, std=2
    df.ta.bbands(append=True)

    # Find the correct column names dynamically
    bb_upper_cols = [col for col in df.columns if 'BBU_' in col]
    bb_middle_cols = [col for col in df.columns if 'BBM_' in col]
    bb_lower_cols = [col for col in df.columns if 'BBL_' in col]

    if not bb_upper_cols or not bb_middle_cols or not bb_lower_cols:
        return {'bb_upper': None, 'bb_middle': None, 'bb_lower': None}

    return {
        'bb_upper': df[bb_upper_cols[0]].iloc[-1],
        'bb_middle': df[bb_middle_cols[0]].iloc[-1],
        'bb_lower': df[bb_lower_cols[0]].iloc[-1]
    }

def get_technical_analysis(symbol, df=None):
    """
    Calculates advanced technical indicators:
    - ADX (Trend Strength)
    - RSI (Momentum)
    - Relative Volume (Buying Pressure)
    - MACD (Trend Following)
    - Bollinger Bands (Volatility)
    
    Args:
        symbol (str): Stock symbol.
        df (pd.DataFrame, optional): Existing data. If None, fetches new data.
    """
    try:
        if df is None:
            ticker = yf.Ticker(symbol)
            # Fetch enough data for ADX (needs 14 periods + smoothing), MACD (26 periods), BB (20 periods)
            df = ticker.history(period="6mo", interval="1d")
        
        if df.empty or len(df) < 50: # Ensure enough data for indicators
            return None
            
        df.columns = [c.lower() for c in df.columns]
        
        # 1. Trend Strength (ADX)
        # ADX > 25 indicates a strong trend
        adx_df = df.ta.adx(length=14)
        current_adx = adx_df['ADX_14'].iloc[-1]
        
        # 2. Momentum (RSI)
        df.ta.rsi(length=14, append=True)
        current_rsi = df['RSI_14'].iloc[-1]
        
        # 3. Relative Volume (RVOL)
        # Compare current volume to 20-day average volume
        avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
        current_vol = df['volume'].iloc[-1]
        rvol = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        # 4. MACD
        macd_data = _calculate_macd(df)
        current_macd = macd_data['macd']
        current_macdh = macd_data['macdh']
        current_macds = macd_data['macds']

        # 5. Bollinger Bands
        bb_data = _calculate_bollinger_bands(df)
        bb_upper = bb_data['bb_upper']
        bb_middle = bb_data['bb_middle']
        bb_lower = bb_data['bb_lower']
        
        # 6. Trend Prediction
        trend_prediction = "Neutral"
        current_price = df['close'].iloc[-1]

        # Basic trend strength and direction
        if current_adx is not None and current_adx > 25:
            if current_rsi is not None and current_macdh is not None:
                if current_rsi > 60 and current_macdh > 0:
                    trend_prediction = "Strong Uptrend"
                elif current_rsi < 40 and current_macdh < 0:
                    trend_prediction = "Strong Downtrend"
                else:
                    trend_prediction = "Trending (Direction Unclear)"
            else:
                 trend_prediction = "Trending (Direction Unclear)"
        elif current_adx is not None and current_adx < 20:
            trend_prediction = "Sideways / Choppy"
        
        # Add MACD crossover signal
        if current_macd is not None and current_macds is not None and current_macdh is not None:
            if current_macd > current_macds and current_macdh > 0:
                trend_prediction += " (MACD Bullish Crossover)"
            elif current_macd < current_macds and current_macdh < 0:
                trend_prediction += " (MACD Bearish Crossover)"

        # Add Bollinger Band position
        if bb_upper is not None and bb_lower is not None and current_price is not None:
            if current_price > bb_upper:
                trend_prediction += " (Overbought - Above Upper BB)"
            elif current_price < bb_lower:
                trend_prediction += " (Oversold - Below Lower BB)"
            
        return {
            'adx': current_adx,
            'rsi': current_rsi,
            'rvol': rvol,
            'macd': current_macd,
            'macdh': current_macdh,
            'macds': current_macds,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'prediction': trend_prediction,
            'current_price': current_price,
            # New Metrics
            'weekly_trend': _weekly_ema_trend(symbol),
            'sector': _sector_lookup(symbol),
            'vwap': _vwap(df),
            'atr': _atr(df),
            'candlestick': _candlestick_pattern(df),
            'stop_loss': _risk_reward(symbol, df, current_price)[0],
            'target_price': _risk_reward(symbol, df, current_price)[1],
            'rr_ratio': _risk_reward(symbol, df, current_price)[2]
        }
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None
