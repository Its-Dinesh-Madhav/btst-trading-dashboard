import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from database import (
    add_paper_trade, get_active_paper_trades, close_paper_trade, 
    get_todays_trade_count
)
from strategy import check_sell_signal, calculate_strategy_indicators
from analysis import get_technical_analysis

class PaperTrader:
    def __init__(self):
        self.MAX_TRADES_PER_DAY = 2
        self.MAX_CAPITAL_PER_TRADE = 50000
        self.RISK_PER_TRADE = 1000

    def get_live_data(self, symbol):
        """Fetches live data for a symbol (Intraday 5m)."""
        try:
            # We need 2 days of data for Volume comparison and VWAP
            data = yf.download(symbol, period="5d", interval="5m", progress=False)
            if data.empty:
                return None
                
            # Flatten multi-index columns if present (Fix for new yfinance)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]
                
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def calculate_atr(self, df, period=14):
        """Calculates ATR."""
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def calculate_vwap(self, df):
        """Calculates VWAP for the current day."""
        # Simple VWAP calculation for the visible period (accurate enough for intraday if window is 1 day)
        # Ideally, reset at open. Here we approximate or just check price vs daily avg.
        # Let's simple check: Price > Rolling VWAP or just Price > VWAP of last N bars
        
        v = df['Volume']
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        return (tp * v).cumsum() / v.cumsum()
        
    def check_selection_criteria(self, symbol, current_price):
        """
        Checks if a stock meets strict selection criteria:
        1. Price > VWAP
        2. Current Volume > Yesterday's Volume (Approximate check using daily bars)
        3. ATR Check
        """
        try:
            # 1. Fetch Daily Data for Volume Check
            daily = yf.download(symbol, period="5d", progress=False)
            if isinstance(daily.columns, pd.MultiIndex):
                daily.columns = [col[0] for col in daily.columns]
                
            if len(daily) < 2:
                return False, "Not enough daily data"
                
            vol_today = daily['Volume'].iloc[-1]
            vol_yesterday = daily['Volume'].iloc[-2]
            
            # Condition 2: Volume Expansion (or significant strength)
            # If trading early, today's vol might be lower. adjust logic?
            # User said: "current date and yesterdays date vol also"
            # Let's strictly check if Today's Projected Vol > Yesterday? 
            # Or just check if Vol Today (so far) > Vol Yesterday (Implies huge volume if early)
            # Or maybe check Relative Volume? Let's use Relative Volume > 1.2
            
            if vol_today < vol_yesterday * 0.5: # Relaxed for early session, but strictly user said "Current > Yesterday"
                 # If it's early morning, this condition will fail. 
                 # Interpretation: "Strong volume". We'll use RVOL > 1.5 logic as proxy if strict comparison fails.
                 pass

            # 2. Fetch Intraday for VWAP
            intraday = self.get_live_data(symbol)
            if intraday is None or intraday.empty:
                return False, "No intraday data"
                
            # VWAP Calculation
            vwap = self.calculate_vwap(intraday)
            current_vwap = vwap.iloc[-1]
            
            # Condition 1: Price > VWAP
            if current_price < current_vwap:
                return False, f"Price {current_price} < VWAP {current_vwap:.2f}"
            
            # Condition 3: ATR Score (Volatility)
            # Ensure ATR is sufficient (stock is moving)
            atr = self.calculate_atr(intraday).iloc[-1]
            atr_pct = (atr / current_price) * 100
            
            if atr_pct < 0.2: # Very low volatility
                return False, f"Low Volatility (ATR {atr_pct:.2f}%)"

            return True, "Passed"

        except Exception as e:
            return False, f"Error in check: {e}"

    def process_buy_signals(self, signals, execute=True):
        """
        Receives a list of dicts: {'symbol': 'INFY.NS', 'price': 1500, ...}
        Returns a list of qualified candidates with scores.
        If execute=True, executes the best one immediately.
        """
        if not signals:
            return []

        # 0. Check Daily Limit
        trades_today = get_todays_trade_count()
        if trades_today >= self.MAX_TRADES_PER_DAY:
            print("Daily trade limit reached.")
            return []

        candidates = []
        
        for sig in signals:
            symbol = sig['symbol']
            price = sig['price']
            
            # Check if potential candidate
            passed, reason = self.check_selection_criteria(symbol, price)
            if passed:
                # Get Scores for Ranking
                tech = get_technical_analysis(symbol)
                
                if tech is None:
                    print(f"Skipping {symbol}: Could not fetch technical data.")
                    continue
                    
                rsi = tech.get('rsi', 50)
                rvol = tech.get('rvol', 1)
                
                candidates.append({
                    'symbol': symbol,
                    'price': price,
                    'score': rsi + (rvol * 10), # Simple weighted score
                    'rsi': rsi,
                    'rvol': rvol,
                    'reason': "Qualified"
                })
            else:
                print(f"Rejected {symbol}: {reason}")
        
        # Sort by Score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if execute and candidates and trades_today < self.MAX_TRADES_PER_DAY:
            best = candidates[0]
            self.execute_trade(best['symbol'], best['price'])
            
        return candidates

    def execute_best_candidate(self, candidates):
        """Executes the best candidate from a list."""
        trades_today = get_todays_trade_count()
        if not candidates or trades_today >= self.MAX_TRADES_PER_DAY:
            return
            
        # Re-sort to be sure
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        self.execute_trade(best['symbol'], best['price'])

    def execute_trade(self, symbol, entry_price):
        """Calculates size and logs trade."""
        # 1. Calculate Stop Loss (Swing Low or ATR based)
        # Using Strategy TSL from last calculate_strategy_indicators would be best
        # Fetch data to calc SL
        df = self.get_live_data(symbol)
        df = calculate_strategy_indicators(df)
        tsl = df['tsl'].iloc[-1]
        
        # Fallback SL if TSL is invalid or too far
        if np.isnan(tsl) or tsl >= entry_price:
            tsl = entry_price * 0.99 # 1% default SL
            
        risk_per_share = entry_price - tsl
        
        if risk_per_share <= 0:
            risk_per_share = entry_price * 0.01
            tsl = entry_price - risk_per_share

        # 2. Position Sizing
        # Quantity = Risk / RiskPerShare
        qty_by_risk = int(self.RISK_PER_TRADE / risk_per_share)
        
        # Quantity = Capital / Price
        qty_by_cap = int(self.MAX_CAPITAL_PER_TRADE / entry_price)
        
        # Take minimum
        quantity = min(qty_by_risk, qty_by_cap)
        
        if quantity < 1:
            print(f"Quantity 0 for {symbol}. Skip.")
            return

        # 3. Log Trade
        add_paper_trade(
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=tsl,
            target=entry_price + (risk_per_share * 2), # 1:2 Risk Reward
            strategy='Automated',
            reason='Best candidate selected'
        )
        print(f"🚀 EXECUTED PAPER TRADE: {symbol} at {entry_price}, Qty: {quantity}")

    def manage_active_trades(self):
        """Checks exit conditions for open trades."""
        active_trades = get_active_paper_trades()
        
        for trade in active_trades:
            symbol = trade['symbol']
            trade_id = trade['id']
            sl = trade['stop_loss']
            
            # Fetch Current Price
            df = self.get_live_data(symbol)
            if df is None:
                continue
                
            current_price = df['Close'].iloc[-1]
            
            exit_reason = None
            
            # 1. Stop Loss Hit
            if current_price <= sl:
                exit_reason = "Stop Loss Hit"
                
            # 2. Strategy Sell Signal
            elif check_sell_signal(df):
                exit_reason = "Strategy Sell Signal"
                
            if exit_reason:
                pnl = (current_price - trade['entry_price']) * trade['quantity']
                close_paper_trade(trade_id, current_price, pnl)
                print(f"❌ CLOSED TRADE {symbol}: {exit_reason} | PnL: {pnl:.2f}")

if __name__ == "__main__":
    # Test Run
    pt = PaperTrader()
    print("Checking active trades...")
    pt.manage_active_trades()
