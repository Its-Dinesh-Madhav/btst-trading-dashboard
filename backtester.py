import yfinance as yf
import pandas as pd
import numpy as np
from strategy import calculate_strategy_indicators

def run_backtest(symbol, period="1y"):
    """
    Runs a backtest for the given symbol over the specified period.
    Returns a dictionary with performance metrics and a DataFrame of trades.
    """
    try:
        # 1. Fetch Data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        
        if df.empty or len(df) < 50:
            return None
            
        df.columns = [c.lower() for c in df.columns]
        
        # 2. Calculate Strategy Indicators
        df = calculate_strategy_indicators(df)
        
        # 3. Simulate Trades
        trades = []
        in_trade = False
        entry_price = 0.0
        stop_loss = 0.0
        target_price = 0.0
        entry_date = None
        
        # Iterate through the DataFrame
        # Start from index 20 to ensure indicators are valid
        for i in range(20, len(df)):
            curr_date = df.index[i]
            curr_close = df['close'].iloc[i]
            curr_high = df['high'].iloc[i]
            curr_low = df['low'].iloc[i]
            prev_close = df['close'].iloc[i-1]
            prev_tsl = df['tsl'].iloc[i-1]
            curr_tsl = df['tsl'].iloc[i]
            
            if not in_trade:
                # Check for Buy Signal (Crossover)
                if prev_close < prev_tsl and curr_close > curr_tsl:
                    # Buy at Close
                    entry_price = curr_close
                    entry_date = curr_date
                    
                    # Set Stop Loss: Lowest Low of last 10 days
                    # (Simple swing low approximation)
                    recent_low = df['low'].iloc[i-10:i].min()
                    stop_loss = recent_low if recent_low < entry_price else entry_price * 0.95 # Fallback
                    
                    # Set Target: 1.5x Risk
                    risk = entry_price - stop_loss
                    target_price = entry_price + (1.5 * risk)
                    
                    in_trade = True
            
            else:
                # Check for Exit
                # 1. Hit Stop Loss
                if curr_low <= stop_loss:
                    exit_price = stop_loss # Assume slippage/gap fill at SL
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({
                        'Entry Date': entry_date,
                        'Exit Date': curr_date,
                        'Entry Price': entry_price,
                        'Exit Price': exit_price,
                        'Result': 'Loss',
                        'P&L %': pnl
                    })
                    in_trade = False
                
                # 2. Hit Target
                elif curr_high >= target_price:
                    exit_price = target_price
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({
                        'Entry Date': entry_date,
                        'Exit Date': curr_date,
                        'Entry Price': entry_price,
                        'Exit Price': exit_price,
                        'Result': 'Win',
                        'P&L %': pnl
                    })
                    in_trade = False
                    
        # 4. Calculate Metrics
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'profit_factor': 0.0,
                'trades': []
            }
            
        trades_df = pd.DataFrame(trades)
        total_trades = len(trades_df)
        wins = len(trades_df[trades_df['Result'] == 'Win'])
        win_rate = (wins / total_trades) * 100
        total_return = trades_df['P&L %'].sum()
        
        gross_profit = trades_df[trades_df['P&L %'] > 0]['P&L %'].sum()
        gross_loss = abs(trades_df[trades_df['P&L %'] < 0]['P&L %'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'profit_factor': profit_factor,
            'trades': trades
        }
        
    except Exception as e:
        print(f"Backtest Error: {e}")
        return None
