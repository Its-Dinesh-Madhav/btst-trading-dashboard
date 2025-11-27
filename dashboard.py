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
import subprocess
import sys

st.set_page_config(
    page_title="Algo Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Indian Stock Market Algo Scanner")
st.markdown("Real-time signals based on **Accurate Swing Trading System**")

# Sidebar controls
st.sidebar.header("Scanner Controls")

if st.sidebar.button("🚀 Run Full Scan"):
    st.sidebar.info("Starting scan... check terminal for progress.")
    # Run scanner.py in a separate process
    subprocess.Popen([sys.executable, "scanner.py"])
    st.sidebar.success("Scanner started in background!")

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
tab_scanner, tab_watchlist, tab_market, tab_pred = st.tabs(["📡 Scanner", "⭐ Watchlist", "🌍 Market Overview", "🔮 Tomorrow's Prediction"])

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
        st.subheader("Live Buy Signals")
        # Fetch data
        signals = get_recent_signals(limit=100)

        if signals:
            df = pd.DataFrame(signals)
            # Reorder columns
            df = df[['symbol', 'price', 'signal_date', 'trend_prediction', 'timestamp']]
            df.columns = ['Symbol', 'Price (INR)', 'Signal Date', 'Trend', 'Scanned At']
            
            # Convert Timestamp to IST
            try:
                df['Scanned At'] = pd.to_datetime(df['Scanned At'])
                # Assuming DB saves in UTC (default), convert to IST (UTC+5:30)
                df['Scanned At'] = df['Scanned At'] + pd.Timedelta(hours=5, minutes=30)
                df['Scanned At'] = df['Scanned At'].dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                pass # Keep original if conversion fails

            # Apply Filter
            if trend_filter != "All":
                df = df[df['Trend'].str.contains(trend_filter, na=False)]
            
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
                selection_mode="single-row"
            )
            
            # Get Selected Stock
            if len(event.selection.rows) > 0:
                selected_index = event.selection.rows[0]
                selected_stock = df.iloc[selected_index]['Symbol']
            else:
                selected_stock = None
        else:
            st.info("No signals found yet. Click 'Run Full Scan' to start.")
            selected_stock = None

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
    time.sleep(10) # Slower refresh to allow reading details
    st.rerun()
