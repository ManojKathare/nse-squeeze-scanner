"""Table components for displaying scan results"""

import streamlit as st
import pandas as pd
from typing import Callable, Optional


def style_squeeze_status(val):
    """Style squeeze status column"""
    if val == True or val == 'Yes':
        return 'background-color: rgba(0, 210, 106, 0.3); color: #00D26A; font-weight: bold'
    return ''


def style_price_change(val):
    """Style price change column"""
    try:
        if float(val) > 0:
            return 'color: #00D26A'
        elif float(val) < 0:
            return 'color: #FF4B4B'
    except:
        pass
    return ''


def style_momentum_direction(val):
    """Style momentum direction column"""
    if 'BULLISH' in str(val).upper():
        return 'color: #00D26A'
    elif 'BEARISH' in str(val).upper():
        return 'color: #FF4B4B'
    return ''


def format_volume(val):
    """Format volume with K/M/B suffixes"""
    try:
        val = float(val)
        if val >= 1_000_000_000:
            return f'{val/1_000_000_000:.2f}B'
        elif val >= 1_000_000:
            return f'{val/1_000_000:.2f}M'
        elif val >= 1_000:
            return f'{val/1_000:.1f}K'
        return str(int(val))
    except:
        return str(val)


def render_scanner_table(df: pd.DataFrame, on_select: Optional[Callable] = None,
                        watchlist_symbols: list = None):
    """
    Render the main scanner results table.

    Args:
        df: Scan results DataFrame
        on_select: Callback when row is selected
        watchlist_symbols: List of symbols in watchlist
    """
    if df.empty:
        st.info("No stocks found matching the criteria.")
        return

    watchlist_symbols = watchlist_symbols or []

    # Create display DataFrame
    display_df = df.copy()

    # Format columns
    display_df['Volume'] = display_df['volume'].apply(format_volume)

    # Add status emoji
    display_df['Status'] = display_df.apply(
        lambda x: '🔴 FIRED!' if x['squeeze_fire'] else ('🟢 ON' if x['squeeze_on'] else '⚪ OFF'),
        axis=1
    )

    # Add direction emoji
    display_df['Direction'] = display_df['momentum_direction'].apply(
        lambda x: '📈 ' + x if 'BULLISH' in str(x).upper() else ('📉 ' + x if 'BEARISH' in str(x).upper() else x)
    )

    # Add watchlist indicator
    display_df['★'] = display_df['symbol'].apply(
        lambda x: '⭐' if x in watchlist_symbols else ''
    )

    # Select columns for display
    columns_to_show = [
        '★', 'symbol', 'company_name', 'current_price', 'price_change_pct',
        'Status', 'squeeze_duration', 'Direction', 'bb_width', 'Volume'
    ]

    display_df = display_df[[c for c in columns_to_show if c in display_df.columns]]

    # Rename columns
    display_df.columns = [
        '★', 'Symbol', 'Company', 'Price (₹)', 'Change %',
        'Squeeze', 'Days', 'Momentum', 'BB Width %', 'Volume'
    ]

    # Display with styling
    styled_df = display_df.style.applymap(
        style_price_change,
        subset=['Change %']
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )


def render_watchlist_table(df: pd.DataFrame, on_remove: Optional[Callable] = None):
    """
    Render the watchlist table with action buttons.

    Args:
        df: Watchlist DataFrame
        on_remove: Callback when remove button clicked
    """
    if df.empty:
        st.info("Your watchlist is empty. Add stocks from the Scanner page.")
        return

    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{row['symbol']}**")
            if row.get('company_name'):
                st.caption(row['company_name'])

        with col2:
            if row.get('target_price'):
                st.metric("Target", f"₹{row['target_price']}")

        with col3:
            if row.get('stop_loss'):
                st.metric("Stop Loss", f"₹{row['stop_loss']}")

        with col4:
            if st.button("🗑️", key=f"remove_{row['symbol']}", help="Remove from watchlist"):
                if on_remove:
                    on_remove(row['symbol'])
                st.rerun()

        if row.get('notes'):
            st.caption(f"📝 {row['notes']}")

        st.divider()


def render_alerts_table(alerts: list, on_delete: Optional[Callable] = None,
                       on_toggle: Optional[Callable] = None):
    """
    Render the alerts table with action buttons.

    Args:
        alerts: List of alert dictionaries
        on_delete: Callback when delete button clicked
        on_toggle: Callback when toggle button clicked
    """
    if not alerts:
        st.info("No alerts set. Create alerts from the Stock Detail page.")
        return

    for alert in alerts:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            status = "🔔" if alert.get('is_active') else "🔕"
            st.markdown(f"{status} **{alert['symbol']}**")
            if alert.get('company_name'):
                st.caption(alert['company_name'])

        with col2:
            alert_type = alert.get('alert_type', '')
            if alert_type == 'PRICE_ABOVE':
                st.write(f"📈 Price above ₹{alert.get('threshold', 0):.2f}")
            elif alert_type == 'PRICE_BELOW':
                st.write(f"📉 Price below ₹{alert.get('threshold', 0):.2f}")
            elif alert_type == 'SQUEEZE_FIRE':
                st.write("💥 Squeeze Fire")

        with col3:
            if alert.get('triggered_date'):
                st.caption(f"Triggered: {alert['triggered_date'][:10]}")
            else:
                st.caption(f"Created: {alert.get('created_date', '')[:10]}")

        with col4:
            col_a, col_b = st.columns(2)
            with col_a:
                toggle_label = "🔕" if alert.get('is_active') else "🔔"
                if st.button(toggle_label, key=f"toggle_{alert['id']}", help="Toggle alert"):
                    if on_toggle:
                        on_toggle(alert['id'])
                    st.rerun()
            with col_b:
                if st.button("🗑️", key=f"delete_{alert['id']}", help="Delete alert"):
                    if on_delete:
                        on_delete(alert['id'])
                    st.rerun()

        st.divider()
