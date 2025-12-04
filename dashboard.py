import streamlit as st
import pandas as pd
import time
from database import get_recent_signals, add_to_portfolio, get_portfolio, remove_from_portfolio, close_position
from analysis import get_stock_news_sentiment, get_technical_analysis, get_sector_performance, get_general_market_news
from backtester import run_backtest
from plotting import plot_stock_chart
from streamlit_lightweight_charts import renderLightweightCharts
from forecasting import get_ai_price_prediction
from btst_strategy import get_btst_candidates
from stock_list import load_stock_list
import subprocess
import sys

# Cache the stock list to avoid re-fetching on every rerun
@st.cache_data
def get_all_symbols():
    return load_stock_list()

st.set_page_config(
    page_title="Algo Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Indian Stock Market Algo Scanner")
st.markdown("Real-time signals based on **Accurate Swing Trading System**")

# Sidebar controls
st.sidebar.header("Scanner Controls")

# Filter Section

# Filter Section
st.sidebar.header("Filters")
trend_filter = st.sidebar.selectbox(
    "Filter by Trend Prediction",
    ["All", "Strong Uptrend", "Strong Downtrend", "Trending (Direction Unclear)", "Sideways / Choppy", "Neutral"]
)

auto_refresh = st.sidebar.checkbox("Auto-refresh Data", value=True)

# Main Content
# Main Content
# Main Content
# Main Content
# Main Content
tab_scanner, tab_sniper, tab_golden, tab_watchlist, tab_market, tab_pred = st.tabs(["📡 Scanner", "🎯 Sniper Signals", "🏅 Golden Crossover", "⭐ Watchlist", "🌍 Market Overview", "🔮 Tomorrow's Prediction"])

with tab_pred:
    st.subheader("🚀 BTST (Buy Today, Sell Tomorrow) Predictor")
    st.markdown("""
    **Strategy:** Identifies stocks with strong momentum closing near their high, combined with an AI model trained to predict **Gap Ups**.
    *High Probability (>70%) indicates a strong chance of opening higher tomorrow.*
    """)
    
    if st.button("🔮 Scan for Tomorrow's Winners"):
        with st.spinner("Analyzing market momentum and running AI models..."):
            df_btst = get_btst_candidates(limit=100) # Increased limit
            
            if not df_btst.empty:
                st.success(f"Found {len(df_btst)} candidates based on Score!")
                
                # Format for display
                st.dataframe(
                    df_btst[['Symbol', 'Price', 'Change %', 'BTST Score', 'Reason', 'Gap Up Prob %']],
                    use_container_width=True,
                    column_config={
                        "BTST Score": st.column_config.ProgressColumn(
                            "Score (0-100)",
                            format="%d",
                            min_value=0,
                            max_value=100,
                        ),
                        "Gap Up Prob %": st.column_config.NumberColumn(format="%.1f%%"),
                        "Price": st.column_config.NumberColumn(format="₹%.2f"),
                        "Change %": st.column_config.NumberColumn(format="%.2f%%"),
                    }
                )
            else:
                st.warning("No stocks met the criteria. Market might be very weak.")
    else:
        st.info("Click the button to scan for stocks likely to give profits tomorrow.")

with tab_sniper:
    st.subheader("🎯 Sniper Signals (High Accuracy)")
    st.markdown("""
    **Criteria:**
    1.  ✅ **Trend:** Price > 200 EMA (Long-term Uptrend)
    2.  ✅ **Momentum:** RSI between 40 and 70
    3.  ✅ **Volume:** > 1.5x Average Volume
    """)
    
    if st.button("🎯 Run Sniper Scan"):
        st.info("Starting Sniper scan... check terminal for progress.")
        subprocess.Popen([sys.executable, "scanner.py", "--strategy", "sniper"])
        st.success("Sniper scanner started in background!")
    
    # Reuse the same data fetching logic but filter for Sniper
    signals = get_recent_signals(limit=500)
    if signals:
        df = pd.DataFrame(signals)
        
        # Define expected columns and their display names
        expected_cols = {
            'symbol': 'Symbol',
            'price': 'Price (INR)',
            'signal_date': 'Signal Date',
            'trend_prediction': 'Trend',
            'timestamp': 'Scanned At',
            'signal_strength': 'Strength'
        }
        
        # Ensure all expected columns exist, add with default if missing
        for col_db, col_display in expected_cols.items():
            if col_db not in df.columns:
                df[col_db] = 'N/A' # Default value for missing columns
        
        # Select and rename columns
        df = df[[col for col in expected_cols.keys() if col in df.columns]]
        df.columns = [expected_cols[col] for col in df.columns]
        
        # Handle missing signal_strength (backward compatibility) if it was added as 'N/A'
        if 'Strength' in df.columns:
            df['Strength'] = df['Strength'].replace('N/A', 'Standard')
        else:
            df['Strength'] = 'Standard' # Add if still missing after initial check
        
        # Filter for Sniper (case-insensitive)
        df_sniper = df[df['Strength'].str.contains("Sniper", case=False, na=False)]
        
        if not df_sniper.empty:
            # Convert Time to IST
            try:
                df_sniper['Scanned At'] = pd.to_datetime(df_sniper['Scanned At'])
                df_sniper['Scanned At'] = df_sniper['Scanned At'] + pd.Timedelta(hours=5, minutes=30)
                df_sniper['Scanned At'] = df_sniper['Scanned At'].dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
            
            st.dataframe(df_sniper, use_container_width=True, hide_index=True)
        else:
            st.info("No 'Sniper' signals found yet. These are rare but high probability.")
    else:
        st.info("No signals found. These are rare but high probability.")

with tab_golden:
    st.subheader("🏅 Golden Crossover Signals")
    st.markdown("""
    **Strategy:** Identifies stocks where the 50-day Simple Moving Average (SMA) crosses above the 200-day SMA.
    This is generally considered a bullish signal, indicating potential for an uptrend.
    """)

    if st.button("🏅 Run Golden Crossover Scan"):
        st.info("Starting Golden Crossover scan... check terminal for progress.")
        subprocess.Popen([sys.executable, "scanner.py", "--strategy", "golden"])
        st.success("Golden Crossover scanner started in background!")

    # Reuse the same data fetching logic but filter for Golden Crossover
    signals = get_recent_signals(limit=500)
    if signals:
        df = pd.DataFrame(signals)
        
        # Define expected columns and their display names
        expected_cols = {
            'symbol': 'Symbol',
            'price': 'Price (INR)',
            'signal_date': 'Signal Date',
            'trend_prediction': 'Trend',
            'timestamp': 'Scanned At',
            'signal_strength': 'Strength'
        }
        
        # Ensure all expected columns exist, add with default if missing
        for col_db, col_display in expected_cols.items():
            if col_db not in df.columns:
                df[col_db] = 'N/A' # Default value for missing columns
        
        # Select and rename columns
        df = df[[col for col in expected_cols.keys() if col in df.columns]]
        df.columns = [expected_cols[col] for col in df.columns]
        
        # Handle missing signal_strength (backward compatibility) if it was added as 'N/A'
        if 'Strength' in df.columns:
            df['Strength'] = df['Strength'].replace('N/A', 'Standard')
        else:
            df['Strength'] = 'Standard' # Add if still missing after initial check
        
        # Filter for Golden Crossover (case-insensitive)
        df_golden = df[df['Strength'].str.contains("Golden Crossover", case=False, na=False)]
        
        if not df_golden.empty:
            # Convert Time to IST
            try:
                df_golden['Scanned At'] = pd.to_datetime(df_golden['Scanned At'])
                df_golden['Scanned At'] = df_golden['Scanned At'] + pd.Timedelta(hours=5, minutes=30)
                df_golden['Scanned At'] = df_golden['Scanned At'].dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
            
            st.dataframe(df_golden, use_container_width=True, hide_index=True)
        else:
            st.info("No 'Golden Crossover' signals found yet. These signals indicate potential long-term uptrends.")
    else:
        st.info("No signals found. These signals indicate potential long-term uptrends.")

with tab_market:
    col_m1, col_m2 = st.columns([2, 1])
    
    with col_m1:
        st.subheader("🌍 Market Heatmap (Sector Rotation)")
        if st.button("🔄 Refresh Heatmap"):
            with st.spinner("Scanning market breadth..."):
                df_heat = get_sector_performance(limit=50) # Scan top 50 for speed
                
                if not df_heat.empty:
                    import plotly.express as px
                    
                    # Create Treemap
                    fig = px.treemap(
                        df_heat, 
                        path=['Sector', 'Symbol'], 
                        values='Price', # Size by price (proxy for importance)
                        color='Change',
                        color_continuous_scale='RdYlGn',
                        range_color=[-3, 3], # Clamp color range
                        title="Market Performance by Sector"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("""
                    **Heatmap Legend:**
                    *   🟩 **Green**: Positive Change (Price Up)
                    *   🟥 **Red**: Negative Change (Price Down)
                    *   **Box Size**: Represents Stock Price
                    """)
                else:
                    st.error("Failed to load market data. Check internet connection or API limits.")
        else:
            st.info("Click Refresh to load the latest market heatmap.")

    with col_m2:
        st.subheader("📰 Top Market News")
        market_news = get_general_market_news()
        if market_news:
            for news in market_news[:7]: # Show top 7
                st.markdown(f"**[{news['title']}]({news['link']})**")
                st.caption(f"Source: {news['publisher']}")
                st.divider()
        else:
            st.info("No market news available.")

with tab_scanner:
    col_main, col_detail = st.columns([1, 1])

    with col_main:
        st.subheader("Live Buy Signals (Standard)")
        
        # --- Scan Controls ---
        # Simplified layout for better visibility
        st.write("### Control Panel")
        c_ctrl1, c_ctrl2 = st.columns([1, 1])
        
        with c_ctrl1:
            scan_strategy = st.selectbox("Select Strategy", ["All", "Sniper", "Golden"], key="scan_strat_main")
            
        with c_ctrl2:
            # Align button with selectbox
            st.write("") 
            st.write("")
            if st.button("🚀 START SCANNING", type="primary", use_container_width=True):
                st.info(f"Starting {scan_strategy} scan... This will take ~1-2 minutes.")
                strategy_arg = scan_strategy.lower()
                subprocess.Popen([sys.executable, "scanner.py", "--strategy", strategy_arg])
                st.success("Scanner started! Results will appear below.")
                
        st.divider()

        # Fetch data
        signals = get_recent_signals(limit=500)

        if signals:
            df = pd.DataFrame(signals)
            
            # Handle missing signal_strength (backward compatibility)
            if 'signal_strength' not in df.columns:
                df['signal_strength'] = 'Standard'
                
            # Reorder columns
            df = df[['symbol', 'price', 'signal_date', 'trend_prediction', 'timestamp', 'signal_strength']]
            df.columns = ['Symbol', 'Price (INR)', 'Signal Date', 'Trend', 'Scanned At', 'Strength']
            
            # Convert Timestamp to IST
            try:
                df['Scanned At'] = pd.to_datetime(df['Scanned At'])
                # Assuming DB saves in UTC (default), convert to IST (UTC+5:30)
                df['Scanned At'] = df['Scanned At'] + pd.Timedelta(hours=5, minutes=30)
                df['Scanned At'] = df['Scanned At'].dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                pass # Keep original if conversion fails

            # Apply Trend Filter
            if trend_filter != "All":
                df = df[df['Trend'].str.contains(trend_filter, na=False)]
            
            # Sort by Scanned At (Descending) to show recent first
            try:
                df = df.sort_values(by='Scanned At', ascending=False)
            except Exception:
                pass

            # --- Date Filter ---
            time_filter = st.sidebar.selectbox(
                "Filter by Time",
                ["All", "Today", "Yesterday", "Last 7 Days"]
            )
            
            if time_filter != "All":
                try:
                    df['dt'] = pd.to_datetime(df['Scanned At'])
                    today = pd.Timestamp.now().normalize()
                    
                    if time_filter == "Today":
                        df = df[df['dt'].dt.date == today.date()]
                    elif time_filter == "Yesterday":
                        yesterday = today - pd.Timedelta(days=1)
                        df = df[df['dt'].dt.date == yesterday.date()]
                    elif time_filter == "Last 7 Days":
                        last_week = today - pd.Timedelta(days=7)
                        df = df[df['dt'] >= last_week]
                        
                    df = df.drop(columns=['dt'])
                except Exception:
                    pass

            # Display metrics
            c1, c2 = st.columns(2)
            c1.metric("Total Signals", len(df))
            if not df.empty:
                c2.metric("Latest", df.iloc[0]['Symbol'])

            # Display Table with Selection
            event = st.dataframe(
                df,
                use_container_width=True,
                height=400,
                on_select="rerun",
                selection_mode="single-row",
                hide_index=True
            )
            
            # Get Selected Stock (Priority: Search > Table Selection)
            selected_stock = None
            
            # --- Autocomplete Search ---
            all_symbols = get_all_symbols()
            # Add a placeholder option
            search_options = [""] + all_symbols
            
            search_query = st.selectbox(
                "🔍 Search for any stock (Type to search)",
                options=search_options,
                index=0,
                placeholder="Select or type symbol..."
            )
            
            if search_query:
                selected_stock = search_query
            elif len(event.selection.rows) > 0:
                selected_index = event.selection.rows[0]
                selected_stock = df.iloc[selected_index]['Symbol']
        else:
            st.info("No active buy signals found yet. Click 'START SCANNING' to run a new scan.")
            selected_stock = None
            
            # Allow search even if no signals
            all_symbols = get_all_symbols()
            search_options = [""] + all_symbols
            
            search_query = st.selectbox(
                "🔍 Search for any stock (Type to search)",
                options=search_options,
                index=0,
                placeholder="Select or type symbol..."
            )
            
            if search_query:
                selected_stock = search_query

    with col_detail:
        st.subheader("🤖 AI Analysis & Prediction")
        
        if selected_stock:
            st.markdown(f"### Analyzing: **{selected_stock}**")
            
            # Action Buttons
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("⭐ Add to Watchlist"):
                # Fetch current price for entry reference (optional)
                tech = get_technical_analysis(selected_stock)
                price = tech['current_price'] if tech else 0.0
                if add_to_portfolio(selected_stock, price, 'WATCHLIST'):
                    st.success(f"Added {selected_stock} to Watchlist!")
                else:
                    st.warning("Already in Watchlist.")
            
            # Backtest Button
            if c_btn2.button("🧪 Run Backtest (1 Year)"):
                with st.spinner(f"Backtesting {selected_stock}..."):
                    results = run_backtest(selected_stock)
                    if results:
                        st.success("Backtest Complete!")
                        b1, b2, b3 = st.columns(3)
                        b1.metric("Win Rate", f"{results['win_rate']:.1f}%")
                        b2.metric("Total Return", f"{results['total_return']:.1f}%")
                        b3.metric("Profit Factor", f"{results['profit_factor']:.2f}")
                        
                        with st.expander("See Trade Log"):
                            st.dataframe(pd.DataFrame(results['trades']))
                    else:
                        st.error("Backtest failed or insufficient data.")

            with st.spinner("Fetching AI insights..."):
                # 1. Technical Analysis
                tech_data = get_technical_analysis(selected_stock)
                
                # 2. Sentiment Analysis
                sentiment_score, news_items = get_stock_news_sentiment(selected_stock)
                
                if tech_data:
                    # Display Prediction
                    pred_color = "green" if "Uptrend" in tech_data['prediction'] else "orange"
                    st.markdown(f"#### Trend Prediction: :{pred_color}[{tech_data['prediction']}]")
                    
                    # Key Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("ADX (Trend Strength)", f"{tech_data['adx']:.1f}", help=">25 means Strong Trend")
                    m2.metric("RSI (Momentum)", f"{tech_data['rsi']:.1f}", help=">70 Overbought, <30 Oversold")
                    m3.metric("Relative Vol", f"{tech_data['rvol']:.1f}x", help=">1.5x means High Buying Pressure")
                    
                    st.divider()
                    
                    # --- CHART SECTION ---
                    st.markdown("#### 📊 Strategy Chart (TradingView Style)")
                    chart_data = plot_stock_chart(selected_stock)
                    if chart_data:
                        renderLightweightCharts(
                            charts=[{
                                "chart": chart_data['chartOptions'],
                                "series": chart_data['series']
                            }],
                            key='stock_chart'
                        )
                    else:
                        st.warning("Could not load chart.")
                    
                    st.divider()
                    
                    # --- AI FORECAST SECTION ---
                    st.markdown("#### 🧠 AI Price Forecast (Next 5 Days)")
                    with st.spinner("Running Random Forest Model..."):
                        ai_data = get_ai_price_prediction(selected_stock)
                        
                    if ai_data:
                        c_ai1, c_ai2, c_ai3 = st.columns(3)
                        
                        # Direction Color
                        dir_color = "off"
                        if ai_data['direction'] == "Bullish":
                            dir_color = "normal" # Streamlit metric delta color
                        elif ai_data['direction'] == "Bearish":
                            dir_color = "inverse"
                            
                        c_ai1.metric(
                            "Predicted Price", 
                            f"₹{ai_data['predicted_price']:.2f}",
                            f"{ai_data['change_pct']:.2f}%",
                            delta_color=dir_color
                        )
                        c_ai2.metric("AI Sentiment", ai_data['direction'])
                        c_ai3.metric("Model Confidence", f"{ai_data['confidence']:.1f}%", help="R² Score on historical data")
                    else:
                        st.info("Not enough data for AI prediction.")

                    st.divider()

                    # Additional Metrics in an expander to keep UI clean
                    with st.expander("More Technical Details"):
                        col_a, col_b = st.columns(2)
                        col_a.metric("Weekly Trend", tech_data.get('weekly_trend', 'N/A'))
                        col_a.metric("Sector", tech_data.get('sector', 'N/A'))
                        col_b.metric("VWAP", f"{tech_data.get('vwap'):.2f}" if tech_data.get('vwap') else "N/A")
                        col_b.metric("ATR", f"{tech_data.get('atr'):.2f}" if tech_data.get('atr') else "N/A")
                        st.metric("Candlestick Pattern", tech_data.get('candlestick', 'None'))
                        st.metric("Stop Loss", f"{tech_data.get('stop_loss'):.2f}" if tech_data.get('stop_loss') else "N/A")
                        st.metric("Target Price", f"{tech_data.get('target_price'):.2f}" if tech_data.get('target_price') else "N/A")
                        rr = tech_data.get('rr_ratio')
                        st.metric("R:R Ratio", f"{rr:.2f}" if rr else "N/A")
                        st.metric("MACD", f"{tech_data.get('macd'):.2f}" if tech_data.get('macd') else "N/A")
                        st.metric("MACD Signal", f"{tech_data.get('macds'):.2f}" if tech_data.get('macds') else "N/A")
                        st.metric("Bollinger Upper", f"{tech_data.get('bb_upper'):.2f}" if tech_data.get('bb_upper') else "N/A")
                        st.metric("Bollinger Lower", f"{tech_data.get('bb_lower'):.2f}" if tech_data.get('bb_lower') else "N/A")

                    st.divider()

                # Display Sentiment
                st.markdown("#### Market Sentiment (News)")
                if sentiment_score > 0.1:
                    st.success(f"Positive Sentiment ({sentiment_score:.2f})")
                elif sentiment_score < -0.1:
                    st.error(f"Negative Sentiment ({sentiment_score:.2f})")
                else:
                    st.warning(f"Neutral Sentiment ({sentiment_score:.2f})")
                    
                # Display News Headlines
                st.markdown("##### Recent News")
                for news in news_items[:3]:
                    st.markdown(f"- [{news['title']}]({news['link']}) *({news['publisher']})*")
                    
        else:
            st.info("Select a stock from the left to see advanced analysis.")

with tab_watchlist:
    st.subheader("⭐ My Watchlist")
    portfolio_items = get_portfolio()
    
    if portfolio_items:
        # Convert to DF
        pf_df = pd.DataFrame(portfolio_items)
        
        # Display simple table
        st.dataframe(
            pf_df[['symbol', 'added_date', 'notes']],
            use_container_width=True
        )
        
        # Management
        st.divider()
        c_man1, c_man2 = st.columns(2)
        to_remove = c_man1.selectbox("Select Stock to Remove", pf_df['symbol'])
        
        if c_man1.button("❌ Remove from Watchlist"):
            remove_from_portfolio(to_remove)
            st.success(f"Removed {to_remove}")
            st.rerun()
            
    else:
        st.info("Your watchlist is empty. Add stocks from the Scanner tab!")

# Auto-refresh logic
if auto_refresh:
    time.sleep(3) # Faster refresh for "instant" feel
    st.rerun()
