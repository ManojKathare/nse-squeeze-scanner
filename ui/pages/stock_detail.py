"""Stock Detail Page - Individual stock analysis with charts"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.data_fetcher import fetch_stock_data
from core.squeeze_detector import detect_squeeze, get_squeeze_history
from database.db_manager import DatabaseManager
from ui.components.charts import create_squeeze_chart, create_squeeze_duration_chart


def render_stock_detail_page():
    """Render the stock detail page"""

    # Back button
    if st.button("← Back to Scanner"):
        st.switch_page("ui/pages/scanner.py")

    # Get selected stock
    if 'selected_stock' not in st.session_state:
        st.warning("No stock selected. Please select a stock from the Scanner page.")
        return

    symbol = st.session_state.selected_stock
    db = DatabaseManager()

    # Header
    st.title(f"📊 {symbol}")

    # Fetch data
    with st.spinner(f"Loading data for {symbol}..."):
        df = fetch_stock_data(symbol, period="1y")

    if df is None or df.empty:
        st.error(f"Could not fetch data for {symbol}")
        return

    # Calculate indicators
    df = detect_squeeze(df)

    # Get latest values
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

    # Price header
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Current Price",
            f"₹{latest['Close']:.2f}",
            f"{price_change:+.2f}%"
        )

    with col2:
        squeeze_status = "🟢 ON" if latest['Squeeze_On'] else "🔴 OFF"
        st.metric("Squeeze Status", squeeze_status)

    with col3:
        st.metric("Duration", f"{int(latest['Squeeze_Duration'])} days")

    with col4:
        direction = latest['Momentum_Direction']
        emoji = "📈" if "BULLISH" in str(direction) else "📉" if "BEARISH" in str(direction) else "➡️"
        st.metric("Momentum", f"{emoji} {direction}")

    st.divider()

    # Watchlist and Alert buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        if db.is_in_watchlist(symbol):
            if st.button("⭐ In Watchlist", use_container_width=True, disabled=True):
                pass
        else:
            if st.button("☆ Add to Watchlist", use_container_width=True):
                db.add_to_watchlist(symbol)
                st.success("Added to watchlist!")
                st.rerun()

    with col3:
        with st.popover("🔔 Set Alert"):
            alert_type = st.selectbox(
                "Alert Type",
                ["PRICE_ABOVE", "PRICE_BELOW", "SQUEEZE_FIRE"]
            )

            threshold = 0.0
            if alert_type in ["PRICE_ABOVE", "PRICE_BELOW"]:
                threshold = st.number_input(
                    "Price Threshold (₹)",
                    min_value=0.0,
                    value=float(latest['Close']),
                    step=1.0
                )

            if st.button("Create Alert", use_container_width=True):
                db.create_alert(symbol, alert_type, threshold)
                st.success("Alert created!")

    # Main chart
    st.subheader("Price Chart with Squeeze Indicators")

    fig = create_squeeze_chart(df, symbol)
    st.plotly_chart(fig, use_container_width=True)

    # Squeeze analysis
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Analysis")

        analysis_data = {
            "Indicator": ["BB Upper", "BB Middle", "BB Lower", "KC Upper", "KC Middle", "KC Lower", "BB Width", "ATR"],
            "Value": [
                f"₹{latest['BB_Upper']:.2f}",
                f"₹{latest['BB_Middle']:.2f}",
                f"₹{latest['BB_Lower']:.2f}",
                f"₹{latest['KC_Upper']:.2f}",
                f"₹{latest['KC_Middle']:.2f}",
                f"₹{latest['KC_Lower']:.2f}",
                f"{latest['BB_Width']:.2f}%",
                f"₹{latest['ATR']:.2f}"
            ]
        }

        st.dataframe(pd.DataFrame(analysis_data), hide_index=True, use_container_width=True)

    with col2:
        st.subheader("Squeeze History")

        events = get_squeeze_history(df)

        if events:
            events_df = pd.DataFrame(events)
            events_df = events_df[['start_date', 'end_date', 'duration', 'direction', 'price_move_pct']]
            events_df.columns = ['Start', 'End', 'Days', 'Direction', 'Move %']

            st.dataframe(events_df, hide_index=True, use_container_width=True)
        else:
            st.info("No squeeze events found in the period.")

    # Squeeze history chart
    st.divider()
    st.subheader("Squeeze Duration Analysis")

    events = get_squeeze_history(df)
    duration_fig = create_squeeze_duration_chart(events)
    st.plotly_chart(duration_fig, use_container_width=True)

    # Trading signals
    st.divider()
    st.subheader("Trading Signals")

    if latest['Squeeze_Fire']:
        st.warning("⚠️ **SQUEEZE JUST FIRED!** Potential breakout in progress.")

        # CRITICAL: Validate signal against 200 DMA position
        momentum = latest['Squeeze_Momentum']
        has_dma_200 = 'DMA_200' in latest and pd.notna(latest['DMA_200'])
        above_dma_200 = latest['Close'] > latest['DMA_200'] if has_dma_200 else None

        if momentum > 0 and above_dma_200 == True:
            st.success("📈 **Bullish Signal**: Momentum is positive AND price is above 200 DMA. Consider long positions with proper risk management.")
        elif momentum < 0 and above_dma_200 == False:
            st.error("📉 **Bearish Signal**: Momentum is negative AND price is below 200 DMA. Consider short positions or avoid longs.")
        elif has_dma_200:
            st.warning("⚠️ **Invalid Signal**: Momentum doesn't align with 200 DMA position. Use caution - this signal may be unreliable.")
            if momentum > 0:
                st.caption(f"Momentum is bullish but price (₹{latest['Close']:.2f}) is BELOW 200 DMA (₹{latest['DMA_200']:.2f})")
            else:
                st.caption(f"Momentum is bearish but price (₹{latest['Close']:.2f}) is ABOVE 200 DMA (₹{latest['DMA_200']:.2f})")
        else:
            # No 200 DMA data available
            if momentum > 0:
                st.success("📈 **Bullish Signal** (momentum-only): Consider long positions with proper risk management.")
            else:
                st.error("📉 **Bearish Signal** (momentum-only): Consider short positions or avoid longs.")

    elif latest['Squeeze_On']:
        st.info(f"🟢 **Squeeze Active** for {int(latest['Squeeze_Duration'])} days. Volatility is contracting.")
        st.caption("Wait for squeeze to fire (bands to expand) before entering a trade.")

        # Momentum preview with 200 DMA validation
        momentum = latest['Squeeze_Momentum']
        has_dma_200 = 'DMA_200' in latest and pd.notna(latest['DMA_200'])
        above_dma_200 = latest['Close'] > latest['DMA_200'] if has_dma_200 else None

        if momentum > 0 and above_dma_200 == True:
            st.caption("📈 Current momentum is bullish and price is above 200 DMA - potential valid upside breakout when squeeze fires.")
        elif momentum < 0 and above_dma_200 == False:
            st.caption("📉 Current momentum is bearish and price is below 200 DMA - potential valid downside breakout when squeeze fires.")
        elif has_dma_200:
            st.caption("⚠️ Momentum doesn't align with 200 DMA position - breakout may be unreliable.")
        else:
            # No 200 DMA data
            if momentum > 0:
                st.caption("📈 Current momentum is bullish - potential upside breakout when squeeze fires.")
            else:
                st.caption("📉 Current momentum is bearish - potential downside breakout when squeeze fires.")

    else:
        st.caption("⚪ No active squeeze. Watch for bands to contract inside Keltner Channels.")

    # Notes section for watchlist items
    if db.is_in_watchlist(symbol):
        st.divider()
        st.subheader("Notes")

        watchlist = db.get_watchlist()
        current_item = next((w for w in watchlist if w['symbol'] == symbol), None)

        col1, col2, col3 = st.columns(3)

        with col1:
            target_price = st.number_input(
                "Target Price (₹)",
                min_value=0.0,
                value=float(current_item.get('target_price') or 0),
                step=1.0
            )

        with col2:
            stop_loss = st.number_input(
                "Stop Loss (₹)",
                min_value=0.0,
                value=float(current_item.get('stop_loss') or 0),
                step=1.0
            )

        with col3:
            if st.button("Update", use_container_width=True):
                db.update_watchlist_item(
                    symbol,
                    target_price=target_price if target_price > 0 else None,
                    stop_loss=stop_loss if stop_loss > 0 else None
                )
                st.success("Updated!")
                st.rerun()

        notes = st.text_area(
            "Personal Notes",
            value=current_item.get('notes') or '',
            height=100
        )

        if st.button("Save Notes"):
            db.update_watchlist_item(symbol, notes=notes)
            st.success("Notes saved!")
