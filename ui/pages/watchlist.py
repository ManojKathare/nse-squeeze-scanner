"""Watchlist Page - Manage saved stocks"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager
from core.data_fetcher import fetch_stock_data
from core.squeeze_detector import scan_single_stock


def render_watchlist_page():
    """Render the watchlist page"""

    st.title("⭐ Watchlist")
    st.caption("Your saved stocks for quick access")

    db = DatabaseManager()
    watchlist = db.get_watchlist()

    if not watchlist:
        st.info("Your watchlist is empty. Add stocks from the Scanner page.")
        if st.button("Go to Scanner"):
            st.switch_page("ui/pages/scanner.py")
        return

    # Refresh button
    col1, col2 = st.columns([3, 1])

    with col2:
        refresh = st.button("🔄 Refresh Prices", use_container_width=True)

    # Scan watchlist stocks if refresh clicked
    if refresh or 'watchlist_data' not in st.session_state:
        with st.spinner("Fetching latest data..."):
            watchlist_data = []

            for item in watchlist:
                result = scan_single_stock(item['symbol'], item.get('company_name', ''))
                if result:
                    result['notes'] = item.get('notes', '')
                    result['target_price'] = item.get('target_price')
                    result['stop_loss'] = item.get('stop_loss')
                    result['added_date'] = item.get('added_date', '')
                    watchlist_data.append(result)

            st.session_state.watchlist_data = watchlist_data

    watchlist_data = st.session_state.get('watchlist_data', [])

    if not watchlist_data:
        st.warning("Could not fetch data for watchlist stocks.")
        return

    # Summary
    active_squeezes = sum(1 for w in watchlist_data if w.get('squeeze_on'))
    fired_today = sum(1 for w in watchlist_data if w.get('squeeze_fire'))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Stocks", len(watchlist_data))

    with col2:
        st.metric("Active Squeezes", active_squeezes)

    with col3:
        st.metric("Fired Today", fired_today, delta="🔴" if fired_today > 0 else None)

    st.divider()

    # Display watchlist items
    for item in watchlist_data:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2.5, 1.5, 1.5, 1.5, 1])

            with col1:
                st.markdown(f"### {item['symbol']}")
                st.caption(item.get('company_name', ''))

            with col2:
                price_delta = f"{item['price_change_pct']:+.2f}%"
                st.metric("Price", f"₹{item['current_price']:.2f}", price_delta)

            with col3:
                status = "🟢 ON" if item['squeeze_on'] else ("🔴 FIRED!" if item['squeeze_fire'] else "⚪ OFF")
                st.metric("Squeeze", status)
                if item['squeeze_on']:
                    st.caption(f"{item['squeeze_duration']} days")

            with col4:
                direction = item.get('momentum_direction', 'N/A')
                emoji = "📈" if "BULLISH" in str(direction) else "📉" if "BEARISH" in str(direction) else ""
                st.metric("Momentum", f"{emoji}")
                st.caption(direction)

            with col5:
                if st.button("📊", key=f"view_{item['symbol']}", help="View Details"):
                    st.session_state.selected_stock = item['symbol']
                    st.switch_page("ui/pages/stock_detail.py")

                if st.button("🗑️", key=f"remove_{item['symbol']}", help="Remove"):
                    db.remove_from_watchlist(item['symbol'])
                    if 'watchlist_data' in st.session_state:
                        del st.session_state['watchlist_data']
                    st.rerun()

            # Target/Stop Loss indicators
            if item.get('target_price') or item.get('stop_loss'):
                target_col, sl_col, _ = st.columns([1, 1, 2])

                with target_col:
                    if item.get('target_price'):
                        target_diff = ((item['target_price'] - item['current_price']) / item['current_price']) * 100
                        color = "green" if target_diff > 0 else "red"
                        st.markdown(f"🎯 Target: ₹{item['target_price']:.2f} (:{color}[{target_diff:+.1f}%])")

                with sl_col:
                    if item.get('stop_loss'):
                        sl_diff = ((item['stop_loss'] - item['current_price']) / item['current_price']) * 100
                        color = "red" if sl_diff < 0 else "green"
                        st.markdown(f"🛑 SL: ₹{item['stop_loss']:.2f} (:{color}[{sl_diff:+.1f}%])")

            # Notes
            if item.get('notes'):
                st.caption(f"📝 {item['notes']}")

            st.divider()

    # Bulk actions
    st.subheader("Bulk Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export Watchlist to CSV", use_container_width=True):
            df = pd.DataFrame(watchlist_data)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name="watchlist.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("Clear All", use_container_width=True, type="secondary"):
            if st.checkbox("Confirm clear all"):
                for item in watchlist:
                    db.remove_from_watchlist(item['symbol'])
                if 'watchlist_data' in st.session_state:
                    del st.session_state['watchlist_data']
                st.rerun()
