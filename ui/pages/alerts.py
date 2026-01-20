"""Alerts Page - Manage price and squeeze alerts"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager
from core.data_fetcher import get_cached_stock_list
from ui.components.tables import render_alerts_table


def render_alerts_page():
    """Render the alerts page"""

    st.title("🔔 Alerts")
    st.caption("Manage your price and squeeze alerts")

    db = DatabaseManager()

    # Create new alert section
    with st.expander("➕ Create New Alert", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            # Get stock list for dropdown
            stocks = get_cached_stock_list()
            if not stocks.empty:
                symbol_options = stocks['symbol'].tolist()
                selected_symbol = st.selectbox(
                    "Select Stock",
                    options=symbol_options,
                    format_func=lambda x: f"{x} - {stocks[stocks['symbol'] == x]['company_name'].values[0]}" if len(stocks[stocks['symbol'] == x]) > 0 else x
                )
            else:
                selected_symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE.NS)")

        with col2:
            alert_type = st.selectbox(
                "Alert Type",
                options=["PRICE_ABOVE", "PRICE_BELOW", "SQUEEZE_FIRE"],
                format_func=lambda x: {
                    "PRICE_ABOVE": "📈 Price Above",
                    "PRICE_BELOW": "📉 Price Below",
                    "SQUEEZE_FIRE": "💥 Squeeze Fire"
                }.get(x, x)
            )

        if alert_type in ["PRICE_ABOVE", "PRICE_BELOW"]:
            threshold = st.number_input(
                "Price Threshold (₹)",
                min_value=0.0,
                value=100.0,
                step=1.0
            )
        else:
            threshold = 0.0
            st.info("You'll be notified when the squeeze fires (bands expand outside Keltner Channels)")

        if st.button("Create Alert", use_container_width=True, type="primary"):
            if selected_symbol:
                company_name = ""
                if not stocks.empty and selected_symbol in stocks['symbol'].values:
                    company_name = stocks[stocks['symbol'] == selected_symbol]['company_name'].values[0]

                alert_id = db.create_alert(selected_symbol, alert_type, threshold, company_name)
                if alert_id > 0:
                    st.success(f"Alert created for {selected_symbol}!")
                    st.rerun()
                else:
                    st.error("Failed to create alert.")
            else:
                st.warning("Please select a stock.")

    st.divider()

    # Active alerts
    st.subheader("Active Alerts")

    active_alerts = db.get_active_alerts()

    if not active_alerts:
        st.info("No active alerts. Create one above!")
    else:
        for alert in active_alerts:
            with st.container():
                col1, col2, col3, col4 = st.columns([2.5, 2, 2, 1.5])

                with col1:
                    st.markdown(f"### {alert['symbol']}")
                    if alert.get('company_name'):
                        st.caption(alert['company_name'])

                with col2:
                    alert_type = alert['alert_type']
                    if alert_type == "PRICE_ABOVE":
                        st.markdown(f"📈 **Price Above** ₹{alert['threshold']:.2f}")
                    elif alert_type == "PRICE_BELOW":
                        st.markdown(f"📉 **Price Below** ₹{alert['threshold']:.2f}")
                    else:
                        st.markdown("💥 **Squeeze Fire**")

                with col3:
                    created = alert.get('created_date', '')[:10] if alert.get('created_date') else 'N/A'
                    st.caption(f"Created: {created}")

                with col4:
                    btn_col1, btn_col2 = st.columns(2)

                    with btn_col1:
                        if st.button("🔕", key=f"mute_{alert['id']}", help="Disable alert"):
                            db.toggle_alert(alert['id'])
                            st.rerun()

                    with btn_col2:
                        if st.button("🗑️", key=f"del_{alert['id']}", help="Delete alert"):
                            db.delete_alert(alert['id'])
                            st.rerun()

                st.divider()

    # Alert history (triggered alerts)
    st.subheader("Alert History")

    # Get all alerts including inactive ones
    all_alerts = []
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM alerts WHERE is_active = 0 ORDER BY triggered_date DESC LIMIT 20')
    rows = cursor.fetchall()
    conn.close()
    triggered_alerts = [dict(row) for row in rows]

    if not triggered_alerts:
        st.caption("No triggered alerts yet.")
    else:
        for alert in triggered_alerts:
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                st.markdown(f"**{alert['symbol']}**")

            with col2:
                alert_type = alert['alert_type']
                if alert_type == "PRICE_ABOVE":
                    st.caption(f"📈 Price Above ₹{alert['threshold']:.2f}")
                elif alert_type == "PRICE_BELOW":
                    st.caption(f"📉 Price Below ₹{alert['threshold']:.2f}")
                else:
                    st.caption("💥 Squeeze Fire")

            with col3:
                triggered = alert.get('triggered_date', '')[:10] if alert.get('triggered_date') else 'N/A'
                st.caption(f"Triggered: {triggered}")

    # Info section
    st.divider()

    with st.expander("ℹ️ About Alerts"):
        st.markdown("""
        ### Alert Types

        **📈 Price Above**
        - Triggers when the stock price goes above your specified threshold
        - Use for breakout alerts or profit targets

        **📉 Price Below**
        - Triggers when the stock price falls below your specified threshold
        - Use for stop-loss alerts or buying opportunities

        **💥 Squeeze Fire**
        - Triggers when a Bollinger Bands squeeze ends (bands expand outside Keltner Channels)
        - Indicates potential volatility breakout
        - No price threshold needed

        ### How Alerts Work
        - Alerts are checked when you refresh the Scanner or Watchlist
        - Triggered alerts are automatically disabled
        - Check the Alert History to see past triggers
        """)
