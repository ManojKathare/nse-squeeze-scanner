"""Main Scanner Page - Scan all NSE stocks for squeeze patterns"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.data_fetcher import get_cached_stock_list
from core.squeeze_detector import scan_all_stocks, get_squeeze_summary
from database.db_manager import DatabaseManager
from ui.components.tables import render_scanner_table
from utils.export import export_to_csv, export_to_excel, format_scan_results_for_export, get_export_filename


def render_scanner_page():
    """Render the main scanner page"""

    st.title("🔍 NSE Squeeze Scanner")
    st.caption("Scan Indian stocks for Bollinger Bands squeeze patterns")

    # Initialize database
    db = DatabaseManager()
    watchlist = db.get_watchlist()
    watchlist_symbols = [w['symbol'] for w in watchlist]

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        filter_squeeze = st.radio(
            "Squeeze Status",
            ["All", "Squeeze ON", "Squeeze OFF", "Fired Today"],
            index=0
        )

        min_duration = st.slider(
            "Min Squeeze Duration (Days)",
            min_value=0,
            max_value=30,
            value=0
        )

        momentum_filter = st.multiselect(
            "Momentum Direction",
            ["BULLISH_UP", "BULLISH_DOWN", "BEARISH_UP", "BEARISH_DOWN"],
            default=[]
        )

        st.divider()

        show_watchlist_only = st.checkbox("Show Watchlist Only", value=False)

    # Main content
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Scan Results")

    with col2:
        scan_button = st.button("🔄 Scan Now", type="primary", use_container_width=True)

    # Check for cached results
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()
        st.session_state.last_scan = None

    # Run scan
    if scan_button:
        with st.spinner("Fetching stock list..."):
            stocks_df = get_cached_stock_list()

        if stocks_df.empty:
            st.error("Could not fetch stock list. Please try again.")
            return

        st.info(f"Scanning {len(stocks_df)} stocks... This may take a few minutes.")

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(completed, total):
            progress = completed / total
            progress_bar.progress(progress)
            status_text.text(f"Scanned {completed}/{total} stocks...")

        results = scan_all_stocks(stocks_df, progress_callback=update_progress)

        progress_bar.empty()
        status_text.empty()

        st.session_state.scan_results = results
        st.session_state.last_scan = datetime.now()

        st.success(f"Scan complete! Found {len(results)} stocks with data.")

    # Display results
    results = st.session_state.scan_results

    if results.empty:
        st.info("No scan results yet. Click 'Scan Now' to start scanning.")
        return

    # Show last scan time
    if st.session_state.last_scan:
        st.caption(f"Last scan: {st.session_state.last_scan.strftime('%Y-%m-%d %H:%M:%S')}")

    # Apply filters
    filtered_results = results.copy()

    if filter_squeeze == "Squeeze ON":
        filtered_results = filtered_results[filtered_results['squeeze_on'] == True]
    elif filter_squeeze == "Squeeze OFF":
        filtered_results = filtered_results[filtered_results['squeeze_off'] == True]
    elif filter_squeeze == "Fired Today":
        filtered_results = filtered_results[filtered_results['squeeze_fire'] == True]

    if min_duration > 0:
        filtered_results = filtered_results[filtered_results['squeeze_duration'] >= min_duration]

    if momentum_filter:
        filtered_results = filtered_results[filtered_results['momentum_direction'].isin(momentum_filter)]

    if show_watchlist_only:
        filtered_results = filtered_results[filtered_results['symbol'].isin(watchlist_symbols)]

    # Summary cards
    summary = get_squeeze_summary(filtered_results)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Stocks", summary['total_stocks'])

    with col2:
        st.metric("Active Squeezes", summary['active_squeezes'],
                 delta=None if summary['active_squeezes'] == 0 else "🟢")

    with col3:
        st.metric("Fired Today", summary['fired_today'],
                 delta=None if summary['fired_today'] == 0 else "🔴")

    with col4:
        bullish_pct = (summary['bullish_momentum'] / max(summary['active_squeezes'], 1)) * 100
        st.metric("Bullish %", f"{bullish_pct:.0f}%")

    st.divider()

    # Export buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        export_df = format_scan_results_for_export(filtered_results)
        csv_data = export_to_csv(export_df)
        st.download_button(
            "📥 Export CSV",
            data=csv_data,
            file_name=get_export_filename("squeeze_scan", "csv"),
            mime="text/csv"
        )

    with col3:
        excel_data = export_to_excel(export_df)
        st.download_button(
            "📥 Export Excel",
            data=excel_data,
            file_name=get_export_filename("squeeze_scan", "xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Results table
    st.subheader(f"Results ({len(filtered_results)} stocks)")

    render_scanner_table(filtered_results, watchlist_symbols=watchlist_symbols)

    # Stock selection for detail view
    st.divider()

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_symbol = st.selectbox(
            "Select stock for detailed analysis",
            options=filtered_results['symbol'].tolist() if not filtered_results.empty else [],
            format_func=lambda x: f"{x} - {filtered_results[filtered_results['symbol'] == x]['company_name'].values[0]}" if not filtered_results.empty else x
        )

    with col2:
        if selected_symbol:
            if st.button("📊 View Details", use_container_width=True):
                st.session_state.selected_stock = selected_symbol
                st.switch_page("ui/pages/stock_detail.py")

            # Add to watchlist button
            if selected_symbol in watchlist_symbols:
                if st.button("⭐ Remove from Watchlist", use_container_width=True):
                    db.remove_from_watchlist(selected_symbol)
                    st.rerun()
            else:
                if st.button("☆ Add to Watchlist", use_container_width=True):
                    company = filtered_results[filtered_results['symbol'] == selected_symbol]['company_name'].values[0]
                    db.add_to_watchlist(selected_symbol, company)
                    st.success(f"Added {selected_symbol} to watchlist!")
                    st.rerun()
