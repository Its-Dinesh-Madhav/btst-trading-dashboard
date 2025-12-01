import streamlit as st
import pandas as pd
import subprocess
import sys
from database import get_swing_signals
from plotting import plot_stock_chart
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(
    page_title="Swing Trading Dashboard",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 Daily Swing Trading Watchlist")
st.markdown("Automated screening for **Breakouts**, **Pullbacks**, and **Volume Pockets**.")

# --- Sidebar ---
st.sidebar.header("Scanner Controls")
strategy_map = {
    "All Strategies": "all",
    "Breakout Swing": "breakout",
    "Pullback to Trend": "pullback",
    "Volume Pocket": "volume_pocket"
}
selected_scan = st.sidebar.selectbox("Select Scan Type", list(strategy_map.keys()))

if st.sidebar.button("🚀 Run Swing Scanner"):
    st.sidebar.info(f"Starting {selected_scan} scan...")
    subprocess.Popen([sys.executable, "swing_scanner.py", "--strategy", strategy_map[selected_scan]])
    st.sidebar.success("Scanner running in background!")

# --- Main Tabs ---
tab_breakout, tab_pullback, tab_pocket = st.tabs([
    "💥 Breakout Swing", 
    "📉 Pullback to Trend", 
    "👜 Volume Pocket"
])

def display_swing_signals(strategy_type, description):
    signals = get_swing_signals(strategy_type=strategy_type, limit=100)
    
    if signals:
        df = pd.DataFrame(signals)
        # Format columns
        df['signal_date'] = pd.to_datetime(df['signal_date']).dt.strftime('%Y-%m-%d')
        
        # Display Metrics
        st.metric("Signals Found", len(df))
        
        # Display Table
        st.dataframe(
            df[['symbol', 'price', 'signal_date', 'reason']],
            use_container_width=True,
            column_config={
                "price": st.column_config.NumberColumn(format="₹%.2f"),
                "symbol": "Stock Symbol",
                "reason": "Technical Reason"
            },
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun"
        )
        
        # Charting for top signal or selection
        st.divider()
        st.subheader("📊 Chart Analysis")
        
        # Default to first, or user selection if implemented (Streamlit selection is tricky in tabs without unique keys)
        # For simplicity, let's just show a chart for the first one or allow a selectbox
        selected_stock = st.selectbox(f"Select Stock to Analyze ({strategy_type})", df['symbol'], key=f"sel_{strategy_type}")
        
        if selected_stock:
            chart_data = plot_stock_chart(selected_stock)
            if chart_data:
                renderLightweightCharts(
                    charts=[{
                        "chart": chart_data['chartOptions'],
                        "series": chart_data['series']
                    }],
                    key=f"chart_{strategy_type}"
                )
    else:
        st.info(f"No {strategy_type} signals found. Try running the scanner.")
        st.markdown(f"**Strategy Logic:**\n{description}")

with tab_breakout:
    st.header("Strategy 1: Breakout Swing")
    desc = """
    *   **Logic:** Price near 20-day high + Tight Consolidation + Volume Rising (>20%).
    *   **Entry:** Buy when price breaks above the consolidation range.
    *   **Stop Loss:** Below consolidation low.
    """
    display_swing_signals('Breakout', desc)

with tab_pullback:
    st.header("Strategy 2: Pullback to Trend")
    desc = """
    *   **Logic:** Uptrend (Price > 50 & 200 EMA) + Pullback (3-6%) + RSI (35-50).
    *   **Entry:** Buy on bullish reversal candle.
    *   **Stop Loss:** Below pullback low.
    """
    display_swing_signals('Pullback', desc)

with tab_pocket:
    st.header("Strategy 3: Volume Pocket")
    desc = """
    *   **Logic:** Massive Volume Spike (>2.5x avg) + New 20-day High.
    *   **Concept:** Institutional accumulation creating momentum.
    *   **Exit:** Ride until volume dries up.
    """
    display_swing_signals('VolumePocket', desc)
