"""
NSE Squeeze Scanner - Main Application
A beautiful Streamlit dashboard for scanning Indian stocks for Bollinger Bands squeeze patterns
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_fetcher import (
    get_cached_stock_list, fetch_stock_data, get_nifty50_symbols,
    get_nifty100_symbols, get_nifty200_symbols, get_combined_symbols, get_symbols_by_index
)
from core.squeeze_detector import scan_all_stocks, get_squeeze_summary, detect_squeeze, get_squeeze_history, scan_single_stock, detect_entry_signals, prepare_results_dataframe
from database.db_manager import DatabaseManager
from ui.components.charts import create_squeeze_chart, create_squeeze_duration_chart
from utils.export import export_to_csv, export_to_excel, format_scan_results_for_export, get_export_filename
from config import (
    AVAILABLE_INDICES, INDEX_DISPLAY_NAMES, INDEX_STOCK_COUNTS,
    INDEX_NIFTY_50, INDEX_NIFTY_NEXT_50, INDEX_NIFTY_MIDCAP_150,
    INDEX_NIFTY_SMALLCAP_250, INDEX_NIFTY_MICROCAP_250,
    BROAD_MARKET_INDICES, SECTORAL_INDICES, THEMATIC_INDICES, INDEX_CATEGORIES
)
import json
from pathlib import Path

# Preset storage location
PRESET_FILE = Path("filter_presets.json")

# Page configuration
st.set_page_config(
    page_title="NSE Squeeze Scanner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",  # Start collapsed for better mobile UX
    menu_items={
        'Get Help': 'https://github.com/ManojKathare/nse-squeeze-scanner',
        'Report a bug': 'https://github.com/ManojKathare/nse-squeeze-scanner/issues',
        'About': '# NSE Squeeze Scanner\nTTM Squeeze Strategy Scanner for Indian Stocks'
    }
)

# ========== MOBILE-RESPONSIVE CSS STYLING ==========
def apply_mobile_responsive_styling():
    """Apply comprehensive mobile-responsive CSS with dark theme"""
    st.markdown("""
    <style>
        /* ============================================
           CSS VARIABLES - DARK THEME
           ============================================ */
        :root {
            --primary-color: #1E90FF;
            --primary-hover: #4169E1;
            --secondary-color: #10B981;
            --danger-color: #EF4444;
            --warning-color: #F59E0B;
            --success-color: #00D26A;
            --text-primary: #FAFAFA;
            --text-secondary: #B8BCC4;
            --text-muted: #9CA3AF;
            --bg-primary: #0E1117;
            --bg-secondary: #1A1D24;
            --bg-card: #1E1E2E;
            --border-color: #3E3E4E;
        }

        /* ============================================
           BASE STYLES
           ============================================ */
        .stApp {
            background-color: var(--bg-primary);
            max-width: 100%;
            overflow-x: hidden;
        }

        /* Improve text readability */
        body, p, span, div, label, li, td, th {
            color: var(--text-primary) !important;
            line-height: 1.6 !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
        }

        /* ============================================
           MOBILE NAVIGATION (SIDEBAR)
           ============================================ */
        [data-testid="stSidebar"] {
            background-color: var(--bg-secondary);
            padding: 1rem 0.5rem;
        }

        [data-testid="stSidebar"] > div:first-child {
            background-color: var(--bg-secondary);
        }

        /* Improved sidebar text contrast */
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown li,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stRadio label,
        [data-testid="stSidebar"] .stCheckbox label {
            color: #E8EAED !important;
            font-weight: 400;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {
            color: #FFFFFF !important;
            font-weight: 600;
        }

        /* Navigation radio items styling */
        [data-testid="stSidebar"] .stRadio > div {
            gap: 0.5rem;
        }

        [data-testid="stSidebar"] .stRadio > div > label {
            background-color: var(--bg-card);
            padding: 12px 16px !important;
            border-radius: 8px;
            margin-bottom: 4px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            cursor: pointer;
            min-height: 44px;
            display: flex;
            align-items: center;
        }

        [data-testid="stSidebar"] .stRadio > div > label:hover {
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            transform: translateX(4px);
        }

        /* Mobile sidebar adjustments */
        @media (max-width: 768px) {
            [data-testid="stSidebar"] {
                min-width: 260px !important;
                max-width: 280px !important;
            }

            [data-testid="stSidebar"] .stRadio > div > label {
                padding: 14px 12px !important;
                font-size: 15px !important;
            }
        }

        /* ============================================
           MAIN CONTENT AREA
           ============================================ */
        .main .block-container {
            padding: 1rem !important;
            max-width: 100% !important;
        }

        @media (min-width: 768px) {
            .main .block-container {
                padding: 2rem 3rem !important;
            }
        }

        @media (min-width: 1024px) {
            .main .block-container {
                max-width: 1400px !important;
                margin: 0 auto !important;
            }
        }

        /* ============================================
           BUTTONS & INTERACTIVE ELEMENTS
           ============================================ */
        .stButton > button {
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
            font-size: 16px !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
            min-height: 44px;
            width: 100%;
        }

        .stButton > button:hover {
            background-color: var(--primary-hover) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 144, 255, 0.4) !important;
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Secondary button styling */
        .stButton > button[kind="secondary"] {
            background-color: #2D3748 !important;
            border: 1px solid #4A5568 !important;
        }

        /* Download button */
        .stDownloadButton button {
            background-color: var(--success-color) !important;
            min-height: 44px;
        }

        .stDownloadButton button:hover {
            background-color: #059669 !important;
        }

        /* ============================================
           FORMS & INPUTS
           ============================================ */
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox select,
        .stMultiSelect > div,
        .stTextArea textarea {
            border: 2px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 12px !important;
            font-size: 16px !important;
            color: var(--text-primary) !important;
            background-color: var(--bg-card) !important;
            min-height: 44px;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stSelectbox select:focus,
        .stTextArea textarea:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(30, 144, 255, 0.2) !important;
            outline: none !important;
        }

        /* Checkbox and Radio - Larger touch targets */
        .stCheckbox, .stRadio {
            min-height: 44px;
            display: flex;
            align-items: center;
        }

        [data-testid="stSidebar"] .stCheckbox {
            padding: 4px 0;
        }

        /* ============================================
           DATAFRAMES & TABLES
           ============================================ */
        [data-testid="stDataFrame"] {
            background-color: var(--bg-card);
            border-radius: 10px;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        .dataframe {
            width: 100% !important;
            overflow-x: auto !important;
        }

        .dataframe table {
            font-size: 14px !important;
            border-collapse: collapse !important;
        }

        .dataframe th {
            background-color: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            padding: 12px 8px !important;
            text-align: left !important;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .dataframe td {
            padding: 12px 8px !important;
            border-bottom: 1px solid var(--border-color) !important;
        }

        @media (max-width: 768px) {
            .dataframe table {
                font-size: 12px !important;
            }

            .dataframe th, .dataframe td {
                padding: 8px 6px !important;
            }
        }

        /* ============================================
           TABS
           ============================================ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            flex-wrap: nowrap;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #262730;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 20px;
            color: #E8EAED;
            font-weight: 500;
            white-space: nowrap;
            min-height: 44px;
        }

        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color) !important;
            color: white !important;
            border-color: var(--primary-color) !important;
        }

        @media (max-width: 768px) {
            .stTabs [data-baseweb="tab"] {
                padding: 10px 14px;
                font-size: 14px;
            }
        }

        /* ============================================
           METRICS & STATS
           ============================================ */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 14px !important;
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 14px !important;
        }

        @media (max-width: 768px) {
            [data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
            }

            [data-testid="stMetricLabel"] {
                font-size: 12px !important;
            }
        }

        /* ============================================
           ALERTS & NOTIFICATIONS
           ============================================ */
        .stAlert {
            padding: 16px !important;
            border-radius: 8px !important;
            margin-bottom: 1rem !important;
            background-color: #1E2530;
        }

        /* ============================================
           EXPANDERS
           ============================================ */
        .stExpander {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            margin-bottom: 1rem !important;
        }

        .streamlit-expanderHeader {
            background-color: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            padding: 16px !important;
            border-radius: 8px !important;
            min-height: 44px;
        }

        /* ============================================
           CHARTS & GRAPHS
           ============================================ */
        .js-plotly-plot, .plotly {
            width: 100% !important;
        }

        @media (max-width: 768px) {
            .js-plotly-plot .plotly {
                min-height: 300px !important;
            }
        }

        /* ============================================
           SLIDERS
           ============================================ */
        .stSlider {
            padding: 20px 0;
        }

        .stSlider > div > div > div {
            color: #E8EAED;
        }

        @media (max-width: 768px) {
            .stSlider [role="slider"] {
                width: 24px !important;
                height: 24px !important;
            }
        }

        /* ============================================
           COLUMNS & LAYOUT - RESPONSIVE
           ============================================ */
        @media (max-width: 768px) {
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }

            /* Stack columns vertically on mobile */
            .stHorizontalBlock {
                flex-wrap: wrap !important;
            }
        }

        /* ============================================
           STATUS BADGES
           ============================================ */
        .status-valid {
            background-color: rgba(0, 210, 106, 0.2);
            color: #00D26A;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 13px;
        }

        .status-invalid {
            background-color: rgba(255, 75, 75, 0.2);
            color: #FF4B4B;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 13px;
        }

        /* ============================================
           MISC ELEMENTS
           ============================================ */
        hr {
            border-color: var(--border-color);
        }

        .stCaption {
            color: var(--text-muted) !important;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* ============================================
           SCROLLBARS - DARK THEME
           ============================================ */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }

        /* ============================================
           MOBILE UTILITY CLASSES
           ============================================ */
        .mobile-hidden {
            display: block;
        }

        .mobile-only {
            display: none;
        }

        @media (max-width: 768px) {
            .mobile-hidden {
                display: none !important;
            }

            .mobile-only {
                display: block !important;
            }
        }

        /* ============================================
           ACCESSIBILITY
           ============================================ */
        *:focus-visible {
            outline: 2px solid var(--primary-color) !important;
            outline-offset: 2px !important;
        }

        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        /* ============================================
           MOBILE INFO BOX
           ============================================ */
        .mobile-tip-box {
            background-color: rgba(30, 144, 255, 0.15);
            border-left: 4px solid var(--primary-color);
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 16px;
        }

        .mobile-tip-box p {
            margin: 0;
            color: #E8EAED !important;
            font-size: 14px;
        }

        /* ============================================
           POST-BREAKOUT PAGE STYLING
           ============================================ */
        .post-breakout-header {
            background: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
        }

        .post-breakout-header h2 {
            color: white !important;
            margin: 0 0 0.5rem 0;
        }

        .post-breakout-header p {
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0;
            font-size: 16px;
        }

        /* Performance card styling */
        .perf-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .perf-card-positive {
            border-left: 4px solid var(--success-color);
        }

        .perf-card-negative {
            border-left: 4px solid var(--danger-color);
        }

    </style>
    """, unsafe_allow_html=True)

# Apply mobile-responsive styling
apply_mobile_responsive_styling()


# ========== MOBILE HELPER FUNCTIONS ==========
def add_mobile_hamburger_menu():
    """Add hamburger menu toggle for mobile devices"""
    st.markdown("""
    <style>
        /* Mobile hamburger menu button */
        .mobile-menu-toggle {
            display: none;
            position: fixed;
            top: 0.75rem;
            left: 0.75rem;
            z-index: 1001;
            background-color: #1E90FF;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 22px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(30, 144, 255, 0.4);
            width: 48px;
            height: 48px;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            line-height: 1;
        }

        .mobile-menu-toggle:hover {
            background-color: #4169E1;
            transform: scale(1.05);
        }

        .mobile-menu-toggle:active {
            transform: scale(0.95);
        }

        /* Show only on mobile */
        @media (max-width: 768px) {
            .mobile-menu-toggle {
                display: flex !important;
            }

            /* Add padding to main content to avoid overlap with hamburger */
            .main .block-container {
                padding-top: 4rem !important;
            }

            /* Style sidebar for mobile slide-in */
            [data-testid="stSidebar"] {
                transition: transform 0.3s ease !important;
            }

            [data-testid="stSidebar"][aria-expanded="false"] {
                transform: translateX(-100%) !important;
            }

            [data-testid="stSidebar"][aria-expanded="true"] {
                transform: translateX(0) !important;
                box-shadow: 4px 0 15px rgba(0, 0, 0, 0.3) !important;
            }
        }

        /* Hide hamburger on desktop */
        @media (min-width: 769px) {
            .mobile-menu-toggle {
                display: none !important;
            }
        }
    </style>

    <script>
        // Wait for DOM to be ready
        function initHamburgerMenu() {
            // Check if hamburger already exists
            if (document.querySelector('.mobile-menu-toggle')) return;

            // Create hamburger button
            const hamburger = document.createElement('button');
            hamburger.className = 'mobile-menu-toggle';
            hamburger.innerHTML = '☰';
            hamburger.setAttribute('aria-label', 'Toggle navigation menu');
            hamburger.setAttribute('id', 'mobile-hamburger');
            document.body.appendChild(hamburger);

            // Toggle sidebar function
            hamburger.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                const collapseBtn = document.querySelector('[data-testid="stSidebar"] button[kind="header"]');

                if (sidebar) {
                    const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';

                    if (isExpanded) {
                        // Close sidebar
                        if (collapseBtn) collapseBtn.click();
                        hamburger.innerHTML = '☰';
                    } else {
                        // Open sidebar
                        if (collapseBtn) collapseBtn.click();
                        hamburger.innerHTML = '✕';
                    }
                }
            });

            // Update hamburger icon based on sidebar state
            const observer = new MutationObserver(function(mutations) {
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
                    hamburger.innerHTML = isExpanded ? '✕' : '☰';
                }
            });

            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                observer.observe(sidebar, { attributes: true, attributeFilter: ['aria-expanded'] });
            }
        }

        // Initialize on load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initHamburgerMenu);
        } else {
            initHamburgerMenu();
        }

        // Re-initialize after Streamlit reruns
        window.addEventListener('load', function() {
            setTimeout(initHamburgerMenu, 100);
        });
    </script>
    """, unsafe_allow_html=True)


def add_mobile_navigation_hint():
    """Add a helpful navigation hint for mobile users - shown only once"""
    # Check if hint was already shown in this session
    if 'mobile_hint_shown' not in st.session_state:
        st.markdown("""
        <div class="mobile-only">
            <div class="mobile-tip-box">
                <p>📱 <strong>Tip:</strong> Tap the ☰ button in the top-left corner to navigate between pages</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.mobile_hint_shown = True


def add_mobile_page_header(page_title, show_hint=True):
    """Add mobile-friendly page header with optional navigation hint"""
    # Show navigation hint only on first visit
    if show_hint and 'shown_mobile_hint' not in st.session_state:
        st.markdown("""
        <div class="mobile-only">
            <div style="background-color: rgba(30, 144, 255, 0.15);
                        border-left: 4px solid #1E90FF;
                        padding: 12px 16px;
                        border-radius: 0 8px 8px 0;
                        margin-bottom: 16px;">
                <p style="margin: 0; color: #E8EAED; font-size: 14px;">
                    💡 <strong>Tip:</strong> Use the ☰ button to navigate between pages
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.shown_mobile_hint = True


def add_back_to_top_button():
    """Add a floating 'Back to Top' button for long pages"""
    st.markdown("""
    <style>
        #back-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
            background-color: #1E90FF;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(30, 144, 255, 0.4);
            display: none;
            transition: all 0.3s ease;
        }

        #back-to-top:hover {
            background-color: #4169E1;
            transform: scale(1.1);
        }

        @media (max-width: 768px) {
            #back-to-top {
                width: 44px;
                height: 44px;
                font-size: 20px;
                bottom: 16px;
                right: 16px;
            }
        }
    </style>

    <button id="back-to-top" onclick="window.scrollTo({top: 0, behavior: 'smooth'})" title="Back to top">
        ↑
    </button>

    <script>
        window.onscroll = function() {
            const btn = document.getElementById('back-to-top');
            if (btn) {
                if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
                    btn.style.display = 'block';
                } else {
                    btn.style.display = 'none';
                }
            }
        };
    </script>
    """, unsafe_allow_html=True)


def create_mobile_friendly_metrics(metrics_data):
    """
    Create responsive metrics that stack on mobile.
    metrics_data: list of tuples [(label, value, delta), ...]
    """
    # On mobile, show 2 columns max; on desktop show up to 4
    num_metrics = len(metrics_data)

    if num_metrics <= 2:
        cols = st.columns(num_metrics)
    elif num_metrics <= 4:
        cols = st.columns(min(num_metrics, 4))
    else:
        # For more than 4 metrics, create multiple rows
        cols = st.columns(4)

    for i, (label, value, delta) in enumerate(metrics_data):
        col_idx = i % len(cols)
        with cols[col_idx]:
            if delta:
                st.metric(label, value, delta)
            else:
                st.metric(label, value)


def render_responsive_table(df, key_columns=None, height=400):
    """
    Render a table that's optimized for both desktop and mobile.
    On mobile, shows fewer columns with option to expand.

    Args:
        df: DataFrame to display
        key_columns: List of essential columns to show on mobile (first 3-4)
        height: Table height in pixels
    """
    if df.empty:
        st.info("No data to display.")
        return

    # Show full table with horizontal scroll
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=height
    )

    # Mobile hint
    st.markdown("""
    <div class="mobile-only">
        <p style="color: #9CA3AF; font-size: 12px; text-align: center; margin-top: 8px;">
            ← Swipe table to see more columns →
        </p>
    </div>
    """, unsafe_allow_html=True)


# Period mapping
PERIOD_OPTIONS = {
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "Max": "max"
}


# ========== FILTER PRESET FUNCTIONS ==========
def load_presets():
    """Load saved filter presets from file"""
    if PRESET_FILE.exists():
        try:
            with open(PRESET_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_presets(presets):
    """Save filter presets to file"""
    with open(PRESET_FILE, 'w') as f:
        json.dump(presets, f, indent=2)


def get_current_filter_state():
    """Get current filter values from session state"""
    return {
        'filter_valid_signals': st.session_state.get('filter_valid_signals', False),
        'filter_breakout_type': list(st.session_state.get('filter_breakout_type', ['Bullish', 'Bearish'])),
        'filter_squeeze_status': list(st.session_state.get('filter_squeeze_status', ['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'])),
        'filter_min_duration': st.session_state.get('filter_min_duration', 0),
        'filter_bb_width_range': list(st.session_state.get('filter_bb_width_range', (0.0, 50.0))),
        'filter_momentum': list(st.session_state.get('filter_momentum', ['BULLISH_UP', 'BULLISH_DOWN', 'BEARISH_UP', 'BEARISH_DOWN'])),
        'filter_above_200dma': st.session_state.get('filter_above_200dma', False),
        'filter_above_200dma_range': list(st.session_state.get('filter_above_200dma_range', (0.0, 50.0))),
        'filter_below_200dma': st.session_state.get('filter_below_200dma', False),
        'filter_below_200dma_range': list(st.session_state.get('filter_below_200dma_range', (0.0, 50.0))),
        'filter_watchlist_only': st.session_state.get('filter_watchlist_only', False),
    }


def apply_preset_filters(preset_values):
    """
    DEPRECATED: Use queue_filter_preset() instead.
    This function is kept for backwards compatibility but now
    delegates to queue_filter_preset() which uses the safe pending preset approach.
    """
    queue_filter_preset(preset_values)


def apply_all_filters(df, watchlist_symbols=None):
    """Apply all filter criteria to the dataframe"""
    if df.empty:
        return df

    filtered = df.copy()

    # Valid signals filter
    if st.session_state.get('filter_valid_signals', False) and 'signal_valid' in filtered.columns:
        filtered = filtered[filtered['signal_valid'] == True]

    # Breakout type filter
    breakout_types = st.session_state.get('filter_breakout_type', ['Bullish', 'Bearish'])
    if breakout_types and 'Breakout' in filtered.columns:
        mask = filtered['Breakout'].apply(lambda x: any(bt.lower() in str(x).lower() for bt in breakout_types) if x != '-' else True)
        filtered = filtered[mask]

    # Squeeze status filter
    squeeze_statuses = st.session_state.get('filter_squeeze_status', ['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'])
    if squeeze_statuses and 'squeeze_status' in filtered.columns:
        filtered = filtered[filtered['squeeze_status'].isin(squeeze_statuses)]

    # Min squeeze duration filter
    min_duration = st.session_state.get('filter_min_duration', 0)
    if min_duration > 0 and 'squeeze_duration' in filtered.columns:
        filtered = filtered[filtered['squeeze_duration'] >= min_duration]

    # BB width filter
    bb_range = st.session_state.get('filter_bb_width_range', (0.0, 50.0))
    if 'bb_width' in filtered.columns:
        filtered = filtered[
            (filtered['bb_width'] >= bb_range[0]) &
            (filtered['bb_width'] <= bb_range[1])
        ]

    # Momentum direction filter
    momentum_dirs = st.session_state.get('filter_momentum', [])
    if momentum_dirs and 'momentum_direction' in filtered.columns:
        filtered = filtered[filtered['momentum_direction'].isin(momentum_dirs)]

    # Distance above 200 DMA filter
    if st.session_state.get('filter_above_200dma', False):
        above_range = st.session_state.get('filter_above_200dma_range', (0.0, 50.0))
        if 'current_price' in filtered.columns and 'dma_200' in filtered.columns:
            above_mask = (
                (filtered['current_price'] > filtered['dma_200']) &
                (filtered['dma_200'].notna())
            )
            if 'distance_from_200dma_pct' in filtered.columns:
                above_mask = above_mask & (
                    (filtered['distance_from_200dma_pct'] >= above_range[0]) &
                    (filtered['distance_from_200dma_pct'] <= above_range[1])
                )
            filtered = filtered[above_mask]

    # Distance below 200 DMA filter
    if st.session_state.get('filter_below_200dma', False):
        below_range = st.session_state.get('filter_below_200dma_range', (0.0, 50.0))
        if 'current_price' in filtered.columns and 'dma_200' in filtered.columns:
            below_mask = (
                (filtered['current_price'] < filtered['dma_200']) &
                (filtered['dma_200'].notna())
            )
            if 'distance_from_200dma_pct' in filtered.columns:
                below_mask = below_mask & (
                    (filtered['distance_from_200dma_pct'] >= below_range[0]) &
                    (filtered['distance_from_200dma_pct'] <= below_range[1])
                )
            filtered = filtered[below_mask]

    # Watchlist filter
    if st.session_state.get('filter_watchlist_only', False) and watchlist_symbols:
        filtered = filtered[filtered['symbol'].isin(watchlist_symbols)]

    return filtered


def init_session_state():
    """Initialize session state variables"""
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()
    if 'last_scan' not in st.session_state:
        st.session_state.last_scan = None
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Scanner"
    if 'selected_stocks_toggle' not in st.session_state:
        st.session_state.selected_stocks_toggle = []
    if 'selected_indices' not in st.session_state:
        # Load from database
        db = DatabaseManager()
        st.session_state.selected_indices = db.get_selected_indices()
    if 'show_filtered_only' not in st.session_state:
        st.session_state.show_filtered_only = True
    if 'bb_width_max' not in st.session_state:
        st.session_state.bb_width_max = 100.0

    # Pending preset system - for modifying filter state without Streamlit errors
    if 'apply_pending_preset' not in st.session_state:
        st.session_state.apply_pending_preset = False
    if 'pending_preset' not in st.session_state:
        st.session_state.pending_preset = {}

    # Filter session state variables (defaults)
    filter_defaults = {
        'filters_applied': False,
        'filter_valid_signals': False,
        'filter_breakout_type': ['Bullish', 'Bearish'],
        'filter_squeeze_status': ['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'],
        'filter_min_duration': 0,
        'filter_bb_width_range': (0.0, 50.0),
        'filter_momentum': ['BULLISH_UP', 'BULLISH_DOWN', 'BEARISH_UP', 'BEARISH_DOWN'],
        'filter_above_200dma': False,
        'filter_above_200dma_range': (0.0, 50.0),
        'filter_below_200dma': False,
        'filter_below_200dma_range': (0.0, 50.0),
        'filter_watchlist_only': False,
    }

    for key, default_value in filter_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def apply_pending_preset_if_needed():
    """
    Apply pending preset values BEFORE any widgets are created.
    This MUST be called at the very start of main(), right after init_session_state().

    CRITICAL: This function modifies session state for widget keys BEFORE
    those widgets are instantiated, which is the only time it's allowed.
    """
    if st.session_state.get('apply_pending_preset', False):
        preset_values = st.session_state.get('pending_preset', {})

        # Apply all pending values to session state
        for key, value in preset_values.items():
            if isinstance(value, list):
                st.session_state[key] = list(value)
            elif isinstance(value, tuple):
                st.session_state[key] = tuple(value)
            else:
                st.session_state[key] = value

        # Mark filters as applied
        st.session_state.filters_applied = True

        # Clear the pending flags
        st.session_state.apply_pending_preset = False
        st.session_state.pending_preset = {}


def queue_filter_preset(preset_values):
    """
    Queue preset values to be applied on next rerun.
    Does NOT directly modify widget-bound session state.
    """
    st.session_state.pending_preset = preset_values
    st.session_state.apply_pending_preset = True


def get_default_filter_values():
    """Get default filter values for reset"""
    return {
        'filter_valid_signals': False,
        'filter_breakout_type': ['Bullish', 'Bearish'],
        'filter_squeeze_status': ['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'],
        'filter_min_duration': 0,
        'filter_bb_width_range': (0.0, 50.0),
        'filter_momentum': ['BULLISH_UP', 'BULLISH_DOWN', 'BEARISH_UP', 'BEARISH_DOWN'],
        'filter_above_200dma': False,
        'filter_above_200dma_range': (0.0, 50.0),
        'filter_below_200dma': False,
        'filter_below_200dma_range': (0.0, 50.0),
        'filter_watchlist_only': False,
    }


def get_all_stock_options():
    """Get all available stock options for multi-select"""
    nifty50 = get_nifty50_symbols()
    nifty100 = get_nifty100_symbols()
    nifty200 = get_nifty200_symbols()
    return {
        'Nifty 50': nifty50,
        'Nifty 100': nifty100,
        'Nifty 200': nifty200
    }


def create_squeeze_history_chart(events: list, symbol: str) -> go.Figure:
    """Create detailed squeeze history chart"""
    if not events:
        fig = go.Figure()
        fig.add_annotation(text="No squeeze history", x=0.5, y=0.5, showarrow=False)
        return fig

    df = pd.DataFrame(events)
    df = df[df['end_date'] != 'Ongoing']  # Exclude ongoing

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No completed squeezes", x=0.5, y=0.5, showarrow=False)
        return fig

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Squeeze Duration (Days)', 'BB Width Before Breakout (%)',
                       'Price Move After Breakout (%)', 'Direction Distribution'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "pie"}]]
    )

    # Duration chart with human-readable labels
    colors = ['#00D26A' if d == 'BULLISH' else '#FF4B4B' for d in df['direction']]
    duration_labels = [f"{d} Days" for d in df['duration']]
    fig.add_trace(go.Bar(
        x=list(range(len(df))),
        y=df['duration'],
        marker_color=colors,
        name='Duration',
        text=duration_labels,
        textposition='outside',
        hovertemplate='Duration: %{text}<extra></extra>'
    ), row=1, col=1)

    # BB Width before breakout
    fig.add_trace(go.Bar(
        x=list(range(len(df))),
        y=df['bb_width_before'],
        marker_color='#1E90FF',
        name='BB Width',
        text=[f"{w:.1f}%" for w in df['bb_width_before']],
        textposition='outside',
        hovertemplate='BB Width: %{text}<extra></extra>'
    ), row=1, col=2)

    # Price moves
    avg_moves = [df['move_5d'].mean(), df['move_10d'].mean(), df['move_20d'].mean()]
    fig.add_trace(go.Bar(
        x=['5 Days', '10 Days', '20 Days'],
        y=avg_moves,
        marker_color=['#00D26A' if v > 0 else '#FF4B4B' for v in avg_moves],
        name='Avg Move',
        text=[f"{v:+.1f}%" for v in avg_moves],
        textposition='outside',
        hovertemplate='Avg Move: %{text}<extra></extra>'
    ), row=2, col=1)

    # Direction pie
    direction_counts = df['direction'].value_counts()
    fig.add_trace(go.Pie(
        labels=direction_counts.index,
        values=direction_counts.values,
        marker_colors=['#00D26A' if d == 'BULLISH' else '#FF4B4B' for d in direction_counts.index],
        hole=0.4,
        textinfo='label+percent',
        hovertemplate='%{label}: %{value} events<extra></extra>'
    ), row=2, col=2)

    fig.update_layout(
        title=f'{symbol} - Squeeze History Analysis',
        template='plotly_dark',
        height=600,
        showlegend=False,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117'
    )

    # Update axis titles for clarity
    fig.update_xaxes(title_text='Squeeze Event #', row=1, col=1)
    fig.update_yaxes(title_text='Duration (Days)', row=1, col=1)
    fig.update_xaxes(title_text='Squeeze Event #', row=1, col=2)
    fig.update_yaxes(title_text='BB Width (%)', row=1, col=2)
    fig.update_xaxes(title_text='Time Period', row=2, col=1)
    fig.update_yaxes(title_text='Avg Price Move (%)', row=2, col=1)

    return fig


def create_post_breakout_chart(events: list, breakout_type: str = 'BULLISH') -> go.Figure:
    """
    Create improved chart showing price movement after breakout with interactive markers.

    Features:
    - Scatter plot with markers for each breakout event
    - Hover tooltips showing date, BB width, price, and moves
    - Clear visual distinction between time periods
    - Summary statistics and average lines
    """
    if not events:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No {breakout_type.lower()} breakouts found",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='#9CA3AF')
        )
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=450)
        return fig

    df = pd.DataFrame(events)
    df = df[(df['end_date'] != 'Ongoing') & (df['direction'] == breakout_type)]

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No {breakout_type.lower()} breakouts found",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='#9CA3AF')
        )
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=450)
        return fig

    # Color scheme based on breakout type
    if breakout_type == 'BULLISH':
        primary_color = '#00D26A'
        secondary_color = '#90EE90'
        marker_fill = '#006400'
        marker_line = '#90EE90'
        title_emoji = '📈'
    else:
        primary_color = '#FF4B4B'
        secondary_color = '#FFB6C1'
        marker_fill = '#8B0000'
        marker_line = '#FFB6C1'
        title_emoji = '📉'

    fig = go.Figure()

    # Format dates for display
    df['date_str'] = pd.to_datetime(df['end_date']).dt.strftime('%b %d, %Y')

    # Create x-axis positions for each event
    x_positions = list(range(len(df)))

    # Define time periods with their colors
    periods = [
        ('move_5d', '5 Days', '#1E90FF', 'circle'),
        ('move_10d', '10 Days', '#00CED1', 'diamond'),
        ('move_20d', '20 Days', primary_color, 'star'),
    ]

    # Add scatter traces for each time period with markers
    for col, label, color, symbol in periods:
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=df[col],
            mode='markers+lines',
            name=label,
            marker=dict(
                size=12,
                color=color,
                symbol=symbol,
                line=dict(width=2, color='white')
            ),
            line=dict(width=2, color=color, dash='dot'),
            hovertemplate=(
                f'<b>{label} After Breakout</b><br>' +
                'Breakout Date: %{customdata[0]}<br>' +
                'Price at Breakout: ₹%{customdata[1]:.2f}<br>' +
                'BB Width: %{customdata[2]:.1f}%<br>' +
                'Price Change: <b>%{y:+.1f}%</b><br>' +
                '<extra></extra>'
            ),
            customdata=df[['date_str', 'price_at_breakout', 'bb_width_before']].values
        ))

    # Calculate and display averages
    avg_5d = df['move_5d'].mean()
    avg_10d = df['move_10d'].mean()
    avg_20d = df['move_20d'].mean()

    # Add average lines as annotations
    fig.add_hline(
        y=avg_5d,
        line_dash='dash',
        line_color='#1E90FF',
        line_width=1,
        annotation_text=f'5D Avg: {avg_5d:+.1f}%',
        annotation_position='right',
        annotation_font=dict(size=10, color='#1E90FF')
    )

    fig.add_hline(
        y=avg_20d,
        line_dash='dash',
        line_color=primary_color,
        line_width=1,
        annotation_text=f'20D Avg: {avg_20d:+.1f}%',
        annotation_position='right',
        annotation_font=dict(size=10, color=primary_color)
    )

    # Add zero line
    fig.add_hline(y=0, line_dash='solid', line_color='rgba(255,255,255,0.5)', line_width=2)

    # Update layout for better readability
    title = f"{title_emoji} {'Bullish' if breakout_type == 'BULLISH' else 'Bearish'} Breakout Performance"

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text='Breakout Event #', font=dict(size=14, color='#B8BCC4')),
            tickfont=dict(size=11, color='#E8EAED'),
            tickvals=x_positions,
            ticktext=[f"#{i+1}" for i in x_positions],
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text='Price Change (%)', font=dict(size=14, color='#B8BCC4')),
            tickfont=dict(size=11, color='#E8EAED'),
            ticksuffix='%',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=True,
            zerolinecolor='rgba(255,255,255,0.5)',
            zerolinewidth=2
        ),
        template='plotly_dark',
        height=450,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(size=12, color='white')
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#1A1D24',
            font_size=12,
            font_family='Arial',
            bordercolor='#3E3E4E'
        ),
        margin=dict(l=60, r=100, t=80, b=60)
    )

    return fig


def create_breakout_distribution_chart(events: list, breakout_type: str = 'BULLISH') -> go.Figure:
    """
    Create a distribution chart (box/violin plot) for breakout performance.
    Shows the statistical distribution of price moves after breakouts.
    """
    if not events:
        fig = go.Figure()
        fig.add_annotation(text=f"No {breakout_type.lower()} breakouts", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=300)
        return fig

    df = pd.DataFrame(events)
    df = df[(df['end_date'] != 'Ongoing') & (df['direction'] == breakout_type)]

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No {breakout_type.lower()} breakouts", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', height=300)
        return fig

    # Colors
    color = '#00D26A' if breakout_type == 'BULLISH' else '#FF4B4B'
    light_color = '#90EE90' if breakout_type == 'BULLISH' else '#FFB6C1'

    fig = go.Figure()

    # Add violin plots for each period
    for col, label, col_color in [
        ('move_5d', '5 Days', '#1E90FF'),
        ('move_10d', '10 Days', '#00CED1'),
        ('move_20d', '20 Days', color)
    ]:
        fig.add_trace(go.Violin(
            y=df[col],
            name=label,
            box_visible=True,
            meanline_visible=True,
            fillcolor=col_color,
            line_color='white',
            opacity=0.7,
            hovertemplate=f'{label}: %{{y:.1f}}%<extra></extra>'
        ))

    fig.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.4)')

    fig.update_layout(
        title=dict(
            text=f"Distribution of Price Moves ({len(df)} breakouts)",
            font=dict(size=14, color='#B8BCC4'),
            x=0.5
        ),
        yaxis=dict(
            title='Price Change (%)',
            ticksuffix='%',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        template='plotly_dark',
        height=300,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        showlegend=False,
        margin=dict(l=50, r=20, t=50, b=40)
    )

    return fig


def render_scanner():
    """Render the main scanner page"""
    st.title("🔍 NSE Squeeze Scanner")
    st.caption("Scan Indian stocks for Bollinger Bands squeeze patterns with 200 DMA validation")

    # Add hamburger menu for mobile
    add_mobile_hamburger_menu()

    # Mobile navigation hint (shows only once per session)
    add_mobile_page_header("🔍 Stock Scanner")

    # Add back to top button for long pages
    add_back_to_top_button()

    db = DatabaseManager()
    watchlist = db.get_watchlist()
    watchlist_symbols = [w['symbol'] for w in watchlist]

    # Sidebar - Stock Universe Selection (Filters moved to Advanced Filters)
    with st.sidebar:
        st.header("📊 Stock Universe")

        # Help button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("ℹ️", key="help_btn", help="View Help & Documentation"):
                st.session_state.current_page = "Help"
                st.rerun()

        # Index selection with categories
        st.markdown("**Select Indices:**")
        st.caption("Choose indices by category")

        selected_indices = []

        # Broad Market Indices
        with st.expander("📈 Broad Market", expanded=True):
            for index_key in BROAD_MARKET_INDICES:
                display_name = INDEX_DISPLAY_NAMES.get(index_key, index_key)
                stock_count = INDEX_STOCK_COUNTS.get(index_key, 0)
                checked = index_key in st.session_state.selected_indices

                if st.checkbox(
                    f"{display_name} ({stock_count})",
                    value=checked,
                    key=f"idx_{index_key}"
                ):
                    selected_indices.append(index_key)

        # Sectoral Indices
        with st.expander("🏭 Sectoral", expanded=False):
            for index_key in SECTORAL_INDICES:
                display_name = INDEX_DISPLAY_NAMES.get(index_key, index_key)
                stock_count = INDEX_STOCK_COUNTS.get(index_key, 0)
                checked = index_key in st.session_state.selected_indices

                if st.checkbox(
                    f"{display_name} ({stock_count})",
                    value=checked,
                    key=f"idx_{index_key}"
                ):
                    selected_indices.append(index_key)

        # Thematic Indices
        with st.expander("🎯 Thematic", expanded=False):
            for index_key in THEMATIC_INDICES:
                display_name = INDEX_DISPLAY_NAMES.get(index_key, index_key)
                stock_count = INDEX_STOCK_COUNTS.get(index_key, 0)
                checked = index_key in st.session_state.selected_indices

                if st.checkbox(
                    f"{display_name} ({stock_count})",
                    value=checked,
                    key=f"idx_{index_key}"
                ):
                    selected_indices.append(index_key)

        # Update session state and persist to database
        if selected_indices != st.session_state.selected_indices:
            st.session_state.selected_indices = selected_indices
            db.save_selected_indices(selected_indices)

        # Display selection summary
        if selected_indices:
            unique_symbols = get_combined_symbols(selected_indices)
            st.info(f"**{len(selected_indices)} indices** | **{len(unique_symbols)} unique stocks**")
        else:
            st.warning("Select at least one index")

        st.divider()

        # Last Scan Info
        st.header("📅 Scan Status")
        last_scan_meta = db.get_last_scan_metadata()
        if last_scan_meta:
            scan_time = datetime.fromisoformat(last_scan_meta['scan_time'])
            st.caption(f"**Last Scan:** {scan_time.strftime('%Y-%m-%d %H:%M')}")
            st.caption(f"**Stocks:** {last_scan_meta['total_stocks']}")
            st.caption(f"**Period:** {last_scan_meta['period']}")

            # Check if scan is from today
            if last_scan_meta['scan_date'] == date.today().isoformat():
                st.success("✓ Data is current")
            else:
                st.warning("⚠ Data may be outdated")
        else:
            st.caption("No scan data available")

        st.divider()

        # Data period
        st.header("⏱️ Data Period")
        data_period = st.selectbox(
            "Historical Data",
            list(PERIOD_OPTIONS.keys()),
            index=0,  # Default to 6 Months
            help="Amount of historical data to analyze"
        )

        st.divider()
        st.caption("💡 Use **Advanced Filters** in the main panel to filter results")

    # Main content area
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader("Scan Results")
    with col2:
        refresh_button = st.button("🔄 Refresh Data", type="secondary", use_container_width=True,
                                   help="Force refresh all data from API")
    with col3:
        scan_button = st.button("🔍 Scan Now", type="primary", use_container_width=True)

    # Run scan
    if scan_button or refresh_button:
        if not selected_indices:
            st.error("Please select at least one index to scan.")
            return

        period = PERIOD_OPTIONS[data_period]
        symbols = get_combined_symbols(selected_indices)

        # Check for cached data (unless refresh forced)
        symbols_to_scan = symbols
        if not refresh_button:
            symbols_to_scan = db.get_symbols_needing_scan(symbols)
            if len(symbols_to_scan) < len(symbols):
                # Load cached results
                cached_results = db.get_cached_scan_results(symbols=symbols)
                if cached_results:
                    st.info(f"Loading {len(symbols) - len(symbols_to_scan)} cached results, scanning {len(symbols_to_scan)} new stocks...")

                    # If ALL stocks are cached (no new scans needed), load cached data directly
                    if len(symbols_to_scan) == 0:
                        cached_df = pd.DataFrame(cached_results)
                        if not cached_df.empty:
                            # Add missing columns that are normally calculated during scan

                            # Add company_name if missing
                            if 'company_name' not in cached_df.columns:
                                cached_df['company_name'] = cached_df['symbol'].str.replace('.NS', '')

                            # Add signal_valid column (validates breakout with 200 DMA)
                            if 'signal_valid' not in cached_df.columns:
                                cached_df['signal_valid'] = False
                                if 'above_dma_200' in cached_df.columns and 'momentum' in cached_df.columns:
                                    # Bullish signals valid if above 200 DMA
                                    bullish_mask = cached_df['momentum'] > 0
                                    cached_df.loc[bullish_mask, 'signal_valid'] = cached_df.loc[bullish_mask, 'above_dma_200']
                                    # Bearish signals valid if below 200 DMA
                                    bearish_mask = cached_df['momentum'] < 0
                                    cached_df.loc[bearish_mask, 'signal_valid'] = ~cached_df.loc[bearish_mask, 'above_dma_200']

                            # Add Breakout column
                            if 'Breakout' not in cached_df.columns:
                                cached_df['Breakout'] = '-'
                                # For squeeze_fire stocks, determine breakout type
                                if 'squeeze_fire' in cached_df.columns and 'momentum' in cached_df.columns:
                                    fired_mask = cached_df['squeeze_fire'] == True
                                    bullish_fired = fired_mask & (cached_df['momentum'] > 0)
                                    bearish_fired = fired_mask & (cached_df['momentum'] < 0)
                                    cached_df.loc[bullish_fired, 'Breakout'] = 'Bullish'
                                    cached_df.loc[bearish_fired, 'Breakout'] = 'Bearish'

                            st.session_state.scan_results = cached_df
                            st.session_state.last_scan = datetime.now()
                            st.session_state.last_universe = f"{len(selected_indices)} indices ({len(symbols)} stocks)"
                            st.session_state.last_period = data_period
                            st.success(f"Loaded {len(cached_df)} stocks from cache.")

        if symbols_to_scan or refresh_button:
            stocks_df = pd.DataFrame({'symbol': symbols if refresh_button else symbols_to_scan,
                                     'company_name': symbols if refresh_button else symbols_to_scan})

            st.info(f"Scanning {len(stocks_df)} stocks with {data_period} data...")

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(completed, total):
                progress = completed / total
                progress_bar.progress(progress)
                status_text.text(f"Scanned {completed}/{total} stocks...")

            results = scan_all_stocks(stocks_df, period=period, progress_callback=update_progress)

            progress_bar.empty()
            status_text.empty()

            # Save results to cache
            if not results.empty:
                results_list = results.to_dict('records')
                db.save_scan_results_batch(results_list)
                db.save_scan_metadata(selected_indices, len(results), data_period)

            # Combine with cached if partial scan
            if not refresh_button and len(symbols_to_scan) < len(symbols):
                cached_df = pd.DataFrame(db.get_cached_scan_results(symbols=symbols))
                if not cached_df.empty and not results.empty:
                    results = pd.concat([results, cached_df]).drop_duplicates(subset=['symbol'])
                elif cached_df.empty:
                    pass
                else:
                    results = cached_df

            st.session_state.scan_results = results
            st.session_state.last_scan = datetime.now()
            st.session_state.last_universe = f"{len(selected_indices)} indices ({len(symbols)} stocks)"
            st.session_state.last_period = data_period
            st.success(f"Scan complete! Found {len(results)} stocks with data.")

    # Display results
    results = st.session_state.scan_results

    if results.empty:
        st.info("No scan results yet. Click 'Scan Now' to start scanning.")
        return

    if st.session_state.last_scan:
        universe = st.session_state.get('last_universe', 'All')
        period_used = st.session_state.get('last_period', '6 Months')
        st.caption(f"Last scan: {st.session_state.last_scan.strftime('%Y-%m-%d %H:%M:%S')} | Universe: **{universe}** | Period: **{period_used}**")

    # Prepare results with additional columns for filtering
    filtered_results = results.copy()

    if 'current_price' in filtered_results.columns and 'dma_200' in filtered_results.columns:
        # Calculate distance from 200 DMA
        valid_dma_mask = filtered_results['dma_200'].notna()
        filtered_results.loc[valid_dma_mask, 'distance_from_200dma_pct'] = np.where(
            filtered_results.loc[valid_dma_mask, 'current_price'] > filtered_results.loc[valid_dma_mask, 'dma_200'],
            ((filtered_results.loc[valid_dma_mask, 'current_price'] - filtered_results.loc[valid_dma_mask, 'dma_200']) / filtered_results.loc[valid_dma_mask, 'dma_200']) * 100,
            ((filtered_results.loc[valid_dma_mask, 'dma_200'] - filtered_results.loc[valid_dma_mask, 'current_price']) / filtered_results.loc[valid_dma_mask, 'dma_200']) * 100
        )
        filtered_results.loc[valid_dma_mask, 'position_vs_200dma'] = np.where(
            filtered_results.loc[valid_dma_mask, 'current_price'] > filtered_results.loc[valid_dma_mask, 'dma_200'],
            'Above', 'Below'
        )

    # Add squeeze_status column if not present
    if 'squeeze_status' not in filtered_results.columns:
        filtered_results['squeeze_status'] = 'Squeeze OFF'
        if 'squeeze_on' in filtered_results.columns:
            filtered_results.loc[filtered_results['squeeze_on'] == True, 'squeeze_status'] = 'Squeeze ON'
        if 'squeeze_fire' in filtered_results.columns:
            filtered_results.loc[filtered_results['squeeze_fire'] == True, 'squeeze_status'] = 'Squeeze Fired'

    # Add Breakout column for filtering
    # CRITICAL: Breakout type MUST validate against 200 DMA position
    def get_breakout_type_for_filter(row):
        if row.get('squeeze_fire', False) or row.get('squeeze_on', False):
            momentum = row.get('momentum', 0)
            above_dma_200 = row.get('above_dma_200', None)

            # CRITICAL: Bullish breakout ONLY if price > 200 DMA
            if momentum > 0 and above_dma_200 == True:
                return 'Bullish'
            # CRITICAL: Bearish breakout ONLY if price < 200 DMA
            elif momentum < 0 and above_dma_200 == False:
                return 'Bearish'
            # Invalid breakout - momentum doesn't align with 200 DMA
            elif above_dma_200 is not None:
                return 'Invalid'

        return 'None'

    filtered_results['Breakout'] = filtered_results.apply(get_breakout_type_for_filter, axis=1)

    # Store original count before filtering
    original_results_count = len(filtered_results)

    # Apply filters if filters have been applied
    if st.session_state.get('filters_applied', False):
        filtered_results = apply_all_filters(filtered_results, watchlist_symbols)
        st.session_state.filters_applied = False  # Reset flag after applying

    # Summary cards
    summary = get_squeeze_summary(filtered_results)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Stocks", summary['total_stocks'])
    with col2:
        st.metric("Active Squeezes", summary['active_squeezes'])
    with col3:
        st.metric("Fired Today", summary['fired_today'])
    with col4:
        bullish_pct = (summary['bullish_momentum'] / max(summary['active_squeezes'], 1)) * 100
        st.metric("Bullish %", f"{bullish_pct:.0f}%")
    with col5:
        # Count valid signals
        valid_count = len(filtered_results[filtered_results.get('signal_valid', True) == True]) if 'signal_valid' in filtered_results.columns else len(filtered_results)
        st.metric("Valid Signals", valid_count)

    st.divider()

    # Export buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        export_df = format_scan_results_for_export(filtered_results)
        csv_data = export_to_csv(export_df)
        st.download_button(
            "📥 CSV",
            data=csv_data,
            file_name=get_export_filename("squeeze_scan", "csv"),
            mime="text/csv"
        )
    with col3:
        excel_data = export_to_excel(export_df)
        st.download_button(
            "📥 Excel",
            data=excel_data,
            file_name=get_export_filename("squeeze_scan", "xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Results table header
    st.subheader(f"Results ({len(filtered_results)} stocks)")

    if filtered_results.empty:
        st.info("No stocks match the current filters.")
        return

    # ========== COMPREHENSIVE ADVANCED FILTERS SECTION ==========
    with st.expander("🔍 Advanced Filters", expanded=False):
        st.markdown("### Filter Options")
        st.markdown("Configure your filters below and click **'Apply Filters'** to update results.")

        # Row 1: Signal validation filters
        st.markdown("#### Signal Validation")
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox(
                "✅ Show Valid Signals Only",
                value=st.session_state.get('filter_valid_signals', False),
                key='filter_valid_signals',
                help="Valid signals meet 200 DMA criteria (Bullish above, Bearish below)"
            )
        with col2:
            st.multiselect(
                "Breakout Type",
                options=['Bullish', 'Bearish'],
                default=st.session_state.get('filter_breakout_type', ['Bullish', 'Bearish']),
                key='filter_breakout_type',
                help="Filter by breakout direction"
            )

        # Row 2: Squeeze-related filters
        st.markdown("---")
        st.markdown("#### Squeeze Parameters")
        col3, col4 = st.columns(2)
        with col3:
            st.multiselect(
                "Squeeze Status",
                options=['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'],
                default=st.session_state.get('filter_squeeze_status', ['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired']),
                key='filter_squeeze_status',
                help="ON = Consolidating | OFF = Normal | FIRED = Breaking out"
            )
        with col4:
            st.number_input(
                "Min Squeeze Duration (Days)",
                min_value=0,
                max_value=100,
                value=st.session_state.get('filter_min_duration', 0),
                key='filter_min_duration',
                help="Minimum days squeeze must be active"
            )

        # Row 3: BB Width and Momentum
        st.markdown("---")
        st.markdown("#### Technical Filters")
        col5, col6 = st.columns(2)
        with col5:
            st.slider(
                "Bollinger Band Width (%)",
                min_value=0.0,
                max_value=50.0,
                value=st.session_state.get('filter_bb_width_range', (0.0, 50.0)),
                step=0.5,
                key='filter_bb_width_range',
                help="Filter by BB width percentage (lower = tighter squeeze)"
            )
        with col6:
            st.multiselect(
                "Momentum Direction",
                options=['BULLISH_UP', 'BULLISH_DOWN', 'BEARISH_UP', 'BEARISH_DOWN'],
                default=st.session_state.get('filter_momentum', ['BULLISH_UP', 'BULLISH_DOWN', 'BEARISH_UP', 'BEARISH_DOWN']),
                key='filter_momentum',
                help="Filter by momentum direction"
            )

        # Row 4: 200 DMA distance filters
        st.markdown("---")
        st.markdown("#### 200 DMA Distance")
        col7, col8 = st.columns(2)
        with col7:
            st.checkbox(
                "📈 Filter Above 200 DMA Only",
                value=st.session_state.get('filter_above_200dma', False),
                key='filter_above_200dma'
            )
            if st.session_state.get('filter_above_200dma', False):
                st.slider(
                    "Distance Above Range (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=st.session_state.get('filter_above_200dma_range', (0.0, 50.0)),
                    step=0.5,
                    key='filter_above_200dma_range'
                )

        with col8:
            st.checkbox(
                "📉 Filter Below 200 DMA Only",
                value=st.session_state.get('filter_below_200dma', False),
                key='filter_below_200dma'
            )
            if st.session_state.get('filter_below_200dma', False):
                st.slider(
                    "Distance Below Range (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=st.session_state.get('filter_below_200dma_range', (0.0, 50.0)),
                    step=0.5,
                    key='filter_below_200dma_range'
                )

        # Row 5: Watchlist filter
        st.markdown("---")
        col_watch, col_empty = st.columns(2)
        with col_watch:
            st.checkbox(
                "⭐ Show Watchlist Only",
                value=st.session_state.get('filter_watchlist_only', False),
                key='filter_watchlist_only'
            )

        st.markdown("---")

        # Filter action buttons
        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])

        with col_btn1:
            if st.button("✅ Apply Filters", type="primary", use_container_width=True, help="Click to apply all filter changes"):
                st.session_state.filters_applied = True
                st.rerun()

        with col_btn2:
            if st.button("🔄 Reset Filters", use_container_width=True, help="Reset all filters to default"):
                # Use queue_filter_preset to safely reset all filters
                queue_filter_preset(get_default_filter_values())
                st.rerun()

        with col_btn3:
            # Quick presets buttons
            st.caption("Quick Presets:")
            preset_col1, preset_col2 = st.columns(2)
            with preset_col1:
                if st.button("🎯 Tight", use_container_width=True, help="BB Width < 5%"):
                    queue_filter_preset({'filter_bb_width_range': (0.0, 5.0)})
                    st.rerun()
                if st.button("📈 Bullish", use_container_width=True, help="Valid Bullish Only"):
                    queue_filter_preset({
                        'filter_valid_signals': True,
                        'filter_breakout_type': ['Bullish']
                    })
                    st.rerun()
            with preset_col2:
                if st.button("📉 Bearish", use_container_width=True, help="Valid Bearish Only"):
                    queue_filter_preset({
                        'filter_valid_signals': True,
                        'filter_breakout_type': ['Bearish']
                    })
                    st.rerun()
                if st.button("🔥 Fired", use_container_width=True, help="Breaking Out Now"):
                    queue_filter_preset({'filter_squeeze_status': ['Squeeze Fired']})
                    st.rerun()

        # ========== FILTER PRESETS SECTION ==========
        st.markdown("---")
        st.markdown("#### 💾 Filter Presets")

        presets = load_presets()

        col_preset1, col_preset2 = st.columns([3, 2])

        with col_preset1:
            preset_name = st.text_input(
                "Preset Name",
                placeholder="e.g., Tight Squeeze Bullish",
                help="Enter a name for this filter configuration"
            )

            if st.button("💾 Save Current Filters as Preset", use_container_width=True):
                if preset_name:
                    presets[preset_name] = get_current_filter_state()
                    save_presets(presets)
                    st.success(f"✅ Preset '{preset_name}' saved!")
                    st.rerun()
                else:
                    st.error("Please enter a preset name")

        with col_preset2:
            if presets:
                selected_preset = st.selectbox(
                    "Load Preset",
                    options=['-- Select Preset --'] + list(presets.keys()),
                    help="Select a saved filter preset to load"
                )

                col_load, col_delete = st.columns(2)

                with col_load:
                    if st.button("📂 Load", use_container_width=True):
                        if selected_preset != '-- Select Preset --':
                            # Use queue_filter_preset to safely apply preset
                            queue_filter_preset(presets[selected_preset])
                            st.success(f"✅ Loading: {selected_preset}")
                            st.rerun()

                with col_delete:
                    if st.button("🗑️ Delete", use_container_width=True):
                        if selected_preset != '-- Select Preset --':
                            del presets[selected_preset]
                            save_presets(presets)
                            st.success(f"🗑️ Deleted: {selected_preset}")
                            st.rerun()
            else:
                st.info("No saved presets yet")

        # Show filter status
        st.markdown("---")
        st.info(f"📊 Showing **{len(filtered_results)}** of **{original_results_count}** results")

    # ========== VALIDATION METRICS DASHBOARD ==========
    st.markdown("---")
    st.subheader("📊 Breakout Validation Metrics")

    # Calculate breakout statistics
    total_breakouts = 0
    valid_breakouts = 0
    invalid_breakouts = 0
    bullish_valid = 0
    bearish_valid = 0

    if 'squeeze_fire' in filtered_results.columns:
        total_breakouts = int(filtered_results['squeeze_fire'].sum())

    if 'signal_valid' in filtered_results.columns:
        fired_df = filtered_results[filtered_results.get('squeeze_fire', False) == True]
        if not fired_df.empty:
            valid_breakouts = int(fired_df['signal_valid'].sum())
            invalid_breakouts = total_breakouts - valid_breakouts

    if 'momentum' in filtered_results.columns and 'signal_valid' in filtered_results.columns:
        valid_fired = filtered_results[(filtered_results.get('squeeze_fire', False) == True) & (filtered_results['signal_valid'] == True)]
        if not valid_fired.empty:
            bullish_valid = int((valid_fired['momentum'] > 0).sum())
            bearish_valid = int((valid_fired['momentum'] < 0).sum())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Breakouts", total_breakouts)

    with col2:
        valid_pct = f"{(valid_breakouts/total_breakouts*100):.1f}%" if total_breakouts > 0 else "0%"
        st.metric("Valid Breakouts", valid_breakouts, delta=valid_pct)

    with col3:
        invalid_pct = f"{(invalid_breakouts/total_breakouts*100):.1f}%" if total_breakouts > 0 else "0%"
        st.metric("Invalid Breakouts", invalid_breakouts, delta=invalid_pct, delta_color="inverse")

    with col4:
        st.metric("Bullish/Bearish", f"{bullish_valid}/{bearish_valid}")

    # Show breakdown of invalid reasons if any
    if invalid_breakouts > 0 and 'signal_valid' in filtered_results.columns:
        with st.expander("⚠️ Invalid Breakouts Breakdown", expanded=False):
            invalid_df = filtered_results[(filtered_results.get('squeeze_fire', False) == True) & (filtered_results['signal_valid'] == False)]
            if not invalid_df.empty:
                # Group by above/below DMA
                if 'above_dma_200' in invalid_df.columns:
                    above_count = int((invalid_df['above_dma_200'] == True).sum())
                    below_count = int((invalid_df['above_dma_200'] == False).sum())
                    st.markdown(f"""
                    **Invalid Signal Reasons:**
                    - Bullish signals below 200 DMA: **{below_count}** (should be above)
                    - Bearish signals above 200 DMA: **{above_count}** (should be below)
                    """)
                st.dataframe(invalid_df[['symbol', 'company_name', 'current_price', 'momentum_direction', 'above_dma_200']].head(10), hide_index=True)

    # Format for display
    display_df = filtered_results.copy()
    display_df['Status'] = display_df.apply(
        lambda x: '🔴 FIRED!' if x['squeeze_fire'] else ('🟢 ON' if x['squeeze_on'] else '⚪ OFF'),
        axis=1
    )
    display_df['Direction'] = display_df['momentum_direction'].apply(
        lambda x: '📈' if 'BULLISH' in str(x).upper() else ('📉' if 'BEARISH' in str(x).upper() else '➡️')
    )
    display_df['★'] = display_df['symbol'].apply(lambda x: '⭐' if x in watchlist_symbols else '')

    # Add Breakout Type column for ON and FIRED squeezes
    def get_breakout_type(row):
        if row.get('squeeze_fire', False) or row.get('squeeze_on', False):
            momentum = row.get('momentum', 0)
            above_dma_200 = row.get('above_dma_200', None)

            # CRITICAL: Bullish breakout ONLY if price > 200 DMA
            if momentum > 0 and above_dma_200 == True:
                return '📈 Bullish'
            # CRITICAL: Bearish breakout ONLY if price < 200 DMA
            elif momentum < 0 and above_dma_200 == False:
                return '📉 Bearish'
            # Invalid breakout - momentum doesn't align with 200 DMA position
            elif above_dma_200 is not None:
                return '⚠️ Invalid'
            else:
                # Fallback when 200 DMA data not available (less reliable)
                if momentum > 0:
                    return '📈 Bullish'
                elif momentum < 0:
                    return '📉 Bearish'
        return '-'

    display_df['Breakout'] = display_df.apply(get_breakout_type, axis=1)

    # 200 DMA indicator - User-friendly display with distance
    has_dma_columns = 'above_dma_200' in display_df.columns or 'dma_200' in display_df.columns

    def format_200dma_status(row):
        """Format 200 DMA status for user-friendly display with distance percentage"""
        dma_200 = row.get('dma_200')
        price = row.get('current_price')

        if pd.isna(dma_200) or pd.isna(price):
            return "📊 N/A"

        if price > dma_200:
            distance_pct = ((price - dma_200) / dma_200) * 100
            return f"✅ +{distance_pct:.1f}%"
        elif price < dma_200:
            distance_pct = ((dma_200 - price) / dma_200) * 100
            return f"⚠️ -{distance_pct:.1f}%"
        else:
            return "➡️ At DMA"

    if has_dma_columns:
        display_df['DMA_Status'] = display_df.apply(format_200dma_status, axis=1)

        # Signal validity indicator
        display_df['Valid'] = display_df.apply(
            lambda x: '✅' if x.get('signal_valid', True) else '❌',
            axis=1
        )

    # Define column mapping: (source_col, display_name)
    column_mapping = [
        ('★', '★'),
        ('symbol', 'Symbol'),
        ('company_name', 'Company'),
        ('current_price', 'Price ₹'),
        ('price_change_pct', 'Change %'),
        ('Status', 'Squeeze'),
        ('Breakout', 'Breakout'),
        ('squeeze_duration', 'Days'),
        ('bb_width', 'BB Width'),
    ]

    # Add DMA columns if available
    if has_dma_columns:
        column_mapping.extend([
            ('DMA_Status', '200 DMA'),
            ('Valid', 'Valid'),
        ])

    # Filter to only include columns that exist in the DataFrame
    available_cols = []
    col_names = []
    for src_col, disp_name in column_mapping:
        if src_col in display_df.columns:
            available_cols.append(src_col)
            col_names.append(disp_name)

    # Select only available columns
    display_df = display_df[available_cols]

    # Validate column count before assignment
    if len(display_df.columns) != len(col_names):
        st.error(f"Column mismatch: DataFrame has {len(display_df.columns)} columns, expected {len(col_names)}")
        st.caption(f"DataFrame columns: {display_df.columns.tolist()}")
        st.caption(f"Expected names: {col_names}")
        return

    display_df.columns = col_names

    # Store symbol mapping for click handling
    symbol_list = filtered_results['symbol'].tolist()

    # Helper function to get company name safely (defined early for use below)
    def get_company_name(symbol):
        if 'company_name' in filtered_results.columns:
            matches = filtered_results[filtered_results['symbol'] == symbol]['company_name']
            if len(matches) > 0 and pd.notna(matches.values[0]):
                return matches.values[0]
        return symbol  # Fall back to symbol if company_name not available

    # Display clickable dataframe with selection
    st.caption("💡 Click on a row to select stock, then click 'View Details' or double-click the Symbol below")

    # Use dataframe with selection capability
    selection = st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Handle row selection
    selected_symbol = None
    if selection and hasattr(selection, 'selection') and selection.selection.rows:
        selected_idx = selection.selection.rows[0]
        if selected_idx < len(symbol_list):
            selected_symbol = symbol_list[selected_idx]
            st.session_state.selected_from_table = selected_symbol

    # Stock selector
    st.divider()

    # Quick action buttons for selected stock
    if selected_symbol:
        st.success(f"📌 Selected: **{selected_symbol}**")
        col_quick1, col_quick2, col_quick3 = st.columns(3)
        with col_quick1:
            if st.button("📊 Open Details", key="quick_details", use_container_width=True, type="primary"):
                st.session_state.selected_stock = selected_symbol
                st.session_state.current_page = "Stock Detail"
                st.rerun()
        with col_quick2:
            if selected_symbol in watchlist_symbols:
                if st.button("⭐ Remove from Watchlist", key="quick_remove", use_container_width=True):
                    db.remove_from_watchlist(selected_symbol)
                    st.rerun()
            else:
                if st.button("☆ Add to Watchlist", key="quick_add", use_container_width=True):
                    db.add_to_watchlist(selected_symbol, get_company_name(selected_symbol))
                    st.success(f"Added {selected_symbol}!")
                    st.rerun()
        with col_quick3:
            pass  # Space for future actions

    st.divider()

    col1, col2 = st.columns([3, 1])

    with col1:
        # Pre-select the symbol if one was clicked in the table
        default_idx = 0
        if selected_symbol and selected_symbol in symbol_list:
            default_idx = symbol_list.index(selected_symbol)

        selected = st.selectbox(
            "Or search/select stock for detailed analysis",
            options=symbol_list,
            index=default_idx,
            format_func=lambda x: f"{x} - {get_company_name(x)}"
        )

    with col2:
        if st.button("📊 View Details", use_container_width=True):
            st.session_state.selected_stock = selected
            st.session_state.current_page = "Stock Detail"
            st.rerun()

        if selected in watchlist_symbols:
            if st.button("⭐ Remove", use_container_width=True):
                db.remove_from_watchlist(selected)
                st.rerun()
        else:
            if st.button("☆ Add to Watchlist", use_container_width=True):
                company = get_company_name(selected)
                db.add_to_watchlist(selected, company)
                st.success(f"Added {selected}!")
                st.rerun()


def render_stock_detail():
    """Render stock detail page with 5-year history"""
    if st.button("← Back to Scanner"):
        st.session_state.current_page = "Scanner"
        st.rerun()

    if not st.session_state.selected_stock:
        st.warning("No stock selected. Go to Scanner to select a stock.")
        return

    symbol = st.session_state.selected_stock
    db = DatabaseManager()

    st.title(f"📊 {symbol}")

    # Period selector for detail view
    col1, col2 = st.columns([3, 1])
    with col2:
        detail_period = st.selectbox(
            "Data Period",
            list(PERIOD_OPTIONS.keys()),
            index=3,  # Default to 5 Years
            key="detail_period"
        )

    period = PERIOD_OPTIONS[detail_period]

    with st.spinner(f"Loading {detail_period} data for {symbol}..."):
        df = fetch_stock_data(symbol, period=period)

    if df is None or df.empty:
        st.error(f"Could not fetch data for {symbol}")
        return

    df = detect_squeeze(df)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

    # Metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Price", f"₹{latest['Close']:.2f}", f"{price_change:+.2f}%")
    with col2:
        st.metric("Squeeze", "🟢 ON" if latest['Squeeze_On'] else "🔴 OFF")
    with col3:
        st.metric("Duration", f"{int(latest['Squeeze_Duration'])} days")
    with col4:
        st.metric("BB Width", f"{latest['BB_Width']:.2f}%")
    with col5:
        direction = latest['Momentum_Direction']
        emoji = "📈" if "BULLISH" in str(direction) else "📉"
        st.metric("Momentum", f"{emoji}")
    with col6:
        if 'DMA_200' in latest and not pd.isna(latest['DMA_200']):
            dma_status = "✓ Above" if latest['Close'] > latest['DMA_200'] else "✗ Below"
            st.metric("200 DMA", dma_status)
        else:
            st.metric("200 DMA", "N/A")

    st.divider()

    # Watchlist button
    col1, col2 = st.columns([3, 1])
    with col2:
        if db.is_in_watchlist(symbol):
            st.info("⭐ In Watchlist")
        else:
            if st.button("☆ Add to Watchlist", use_container_width=True):
                db.add_to_watchlist(symbol)
                st.success("Added!")
                st.rerun()

    # Calculate 50 DMA if not present
    if 'DMA_50' not in df.columns:
        df['DMA_50'] = df['Close'].rolling(window=50).mean()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Chart", "📊 Squeeze History", "📉 Post-Breakout Analysis", "📋 Analysis"])

    with tab1:
        st.subheader("Price Chart with Squeeze Indicators")

        # Chart controls
        st.caption("📌 Chart Options - Toggle indicators on/off")
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)

        with ctrl_col1:
            show_200_dma = st.checkbox("Show 200 DMA", value=True, key=f"show_200dma_{symbol}",
                                       help="200-day Moving Average (blue dashed line)")
        with ctrl_col2:
            show_50_dma = st.checkbox("Show 50 DMA", value=True, key=f"show_50dma_{symbol}",
                                      help="50-day Moving Average (orange dotted line)")
        with ctrl_col3:
            show_breakouts = st.checkbox("Show Breakout Markers", value=True, key=f"show_breakouts_{symbol}",
                                         help="B = Bullish breakout, S = Bearish breakout")
        with ctrl_col4:
            pass  # Space for future options

        # DMA Status metrics
        if 'DMA_200' in df.columns or 'DMA_50' in df.columns:
            dma_col1, dma_col2, dma_col3 = st.columns(3)
            with dma_col1:
                st.metric("Current Price", f"₹{latest['Close']:.2f}")
            with dma_col2:
                if 'DMA_200' in latest and not pd.isna(latest['DMA_200']):
                    diff_200 = ((latest['Close'] - latest['DMA_200']) / latest['DMA_200']) * 100
                    st.metric("vs 200 DMA", f"{diff_200:+.1f}%",
                             delta=f"₹{latest['Close'] - latest['DMA_200']:.2f}")
                else:
                    st.metric("vs 200 DMA", "N/A")
            with dma_col3:
                if 'DMA_50' in latest and not pd.isna(latest['DMA_50']):
                    diff_50 = ((latest['Close'] - latest['DMA_50']) / latest['DMA_50']) * 100
                    st.metric("vs 50 DMA", f"{diff_50:+.1f}%",
                             delta=f"₹{latest['Close'] - latest['DMA_50']:.2f}")
                else:
                    st.metric("vs 50 DMA", "N/A")

        # Create chart with selected options
        fig = create_squeeze_chart(df, symbol,
                                   show_200_dma=show_200_dma,
                                   show_50_dma=show_50_dma,
                                   show_breakout_markers=show_breakouts)
        st.plotly_chart(fig, use_container_width=True)

        # Breakout markers legend
        if show_breakouts:
            with st.expander("📖 Breakout Markers Legend"):
                st.markdown("""
                | Marker | Meaning |
                |--------|---------|
                | **▲ B** (Green) | **Bullish Breakout** - Squeeze fired with positive momentum |
                | **▼ S** (Red) | **Bearish Breakout** - Squeeze fired with negative momentum |

                **Hover over markers** to see detailed information including:
                - Breakout date and price
                - BB Width at breakout
                - Volume
                - Position relative to 200 DMA and 50 DMA
                """)

    with tab2:
        st.subheader(f"All Squeeze Events ({detail_period})")

        events = get_squeeze_history(df)

        if events:
            # Get completed events for filtering
            completed_events = [e for e in events if e['end_date'] != 'Ongoing']

            # BB Width Slider - placed prominently at top
            if completed_events:
                bb_widths = [e['bb_width_before'] for e in completed_events if e['bb_width_before'] > 0]
                if bb_widths:
                    min_bb = min(bb_widths)
                    max_bb = max(bb_widths)

                    st.markdown("### 🎯 Filter by BB Width Before Breakout")
                    st.caption("Lower BB Width indicates tighter squeeze - often leads to stronger breakouts")

                    # Initialize session state for this stock's BB filter
                    bb_filter_key = f'bb_filter_{symbol}'
                    if bb_filter_key not in st.session_state:
                        st.session_state[bb_filter_key] = max_bb

                    col_slider, col_reset = st.columns([4, 1])
                    with col_slider:
                        bb_filter = st.slider(
                            "Max BB Width Before Breakout (%)",
                            min_value=float(min_bb),
                            max_value=float(max_bb),
                            value=float(st.session_state[bb_filter_key]),
                            step=0.1,
                            format="%.1f%%",
                            help="Filter breakouts by maximum BB width before breakout. Tighter squeezes (lower values) often produce larger moves.",
                            key=f"bb_slider_{symbol}"
                        )
                        st.session_state[bb_filter_key] = bb_filter

                    with col_reset:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Reset", key=f"reset_bb_{symbol}", help="Show all breakouts"):
                            st.session_state[bb_filter_key] = max_bb
                            st.rerun()

                    # Apply filter
                    filtered_events = [e for e in events if e['end_date'] == 'Ongoing' or e['bb_width_before'] <= bb_filter]
                    filtered_completed = [e for e in filtered_events if e['end_date'] != 'Ongoing']

                    # Show filter status
                    total_count = len(completed_events)
                    filtered_count = len(filtered_completed)
                    st.info(f"📊 Showing **{filtered_count}** of **{total_count}** breakouts (BB Width ≤ {bb_filter:.1f}%)")

                    st.divider()
                else:
                    filtered_events = events
                    filtered_completed = completed_events
            else:
                filtered_events = events
                filtered_completed = completed_events

            # Summary stats (using filtered data)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Squeezes", len(filtered_events))
            with col2:
                bullish = sum(1 for e in filtered_completed if e['direction'] == 'BULLISH')
                st.metric("Bullish Breakouts", bullish)
            with col3:
                bearish = sum(1 for e in filtered_completed if e['direction'] == 'BEARISH')
                st.metric("Bearish Breakouts", bearish)
            with col4:
                avg_duration = sum(e['duration'] for e in filtered_completed) / max(len(filtered_completed), 1)
                st.metric("Avg Duration", f"{avg_duration:.1f} days")

            st.divider()

            # Squeeze history chart (using filtered data)
            history_fig = create_squeeze_history_chart(filtered_events, symbol)
            st.plotly_chart(history_fig, use_container_width=True)

            st.divider()

            # Detailed table (using filtered data)
            st.subheader("Detailed Squeeze History")
            events_df = pd.DataFrame(filtered_events)

            # Format dates
            events_df['start_date'] = pd.to_datetime(events_df['start_date']).dt.strftime('%Y-%m-%d')
            events_df['end_date'] = events_df['end_date'].apply(
                lambda x: x if x == 'Ongoing' else pd.to_datetime(x).strftime('%Y-%m-%d')
            )

            # Format duration with human-readable labels
            events_df['duration_label'] = events_df['duration'].apply(lambda x: f"{x} Days")

            # Rename columns for display
            display_events = events_df[[
                'start_date', 'end_date', 'duration_label', 'direction',
                'bb_width_before', 'min_bb_width', 'move_5d', 'move_10d', 'move_20d'
            ]].copy()
            display_events.columns = [
                'Start', 'End', 'Duration', 'Direction',
                'BB Width Before', 'Min BB Width', '5D Move %', '10D Move %', '20D Move %'
            ]

            st.dataframe(display_events, use_container_width=True, hide_index=True)

            # Export squeeze history
            csv_data = display_events.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Squeeze History",
                data=csv_data,
                file_name=f"{symbol}_squeeze_history.csv",
                mime="text/csv"
            )
        else:
            st.info("No squeeze events found in this period.")

    with tab3:
        st.subheader("Post-Breakout Price Movement Analysis")
        st.caption("Analyze how prices moved after historical squeeze breakouts. Hover over markers for details.")

        events = get_squeeze_history(df)

        if events:
            # Count events by type
            bullish_events = [e for e in events if e['direction'] == 'BULLISH' and e['end_date'] != 'Ongoing']
            bearish_events = [e for e in events if e['direction'] == 'BEARISH' and e['end_date'] != 'Ongoing']

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Bullish Breakouts", len(bullish_events))
            with col2:
                st.metric("Bearish Breakouts", len(bearish_events))
            with col3:
                if bullish_events:
                    avg_bull_20d = sum(e['move_20d'] for e in bullish_events) / len(bullish_events)
                    st.metric("Avg Bullish 20D", f"{avg_bull_20d:+.1f}%")
                else:
                    st.metric("Avg Bullish 20D", "N/A")
            with col4:
                if bearish_events:
                    avg_bear_20d = sum(e['move_20d'] for e in bearish_events) / len(bearish_events)
                    st.metric("Avg Bearish 20D", f"{avg_bear_20d:+.1f}%")
                else:
                    st.metric("Avg Bearish 20D", "N/A")

            st.divider()

            # Bullish Breakouts Section
            st.markdown("### 📈 Bullish Breakout Performance")
            if bullish_events:
                # Main chart with markers
                bullish_fig = create_post_breakout_chart(events, 'BULLISH')
                st.plotly_chart(bullish_fig, use_container_width=True)

                # Statistics summary
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Distribution chart
                    bullish_dist_fig = create_breakout_distribution_chart(events, 'BULLISH')
                    st.plotly_chart(bullish_dist_fig, use_container_width=True)
                with col2:
                    st.markdown("#### Statistics")
                    avg_5d = sum(e['move_5d'] for e in bullish_events) / len(bullish_events)
                    avg_10d = sum(e['move_10d'] for e in bullish_events) / len(bullish_events)
                    avg_20d = sum(e['move_20d'] for e in bullish_events) / len(bullish_events)

                    # Win rates
                    win_5d = sum(1 for e in bullish_events if e['move_5d'] > 0) / len(bullish_events) * 100
                    win_10d = sum(1 for e in bullish_events if e['move_10d'] > 0) / len(bullish_events) * 100
                    win_20d = sum(1 for e in bullish_events if e['move_20d'] > 0) / len(bullish_events) * 100

                    st.markdown(f"""
                    | Period | Avg Move | Win Rate |
                    |--------|----------|----------|
                    | 5 Days | {avg_5d:+.1f}% | {win_5d:.0f}% |
                    | 10 Days | {avg_10d:+.1f}% | {win_10d:.0f}% |
                    | 20 Days | {avg_20d:+.1f}% | {win_20d:.0f}% |
                    """)
            else:
                st.info("No bullish breakouts found in this period.")

            st.divider()

            # Bearish Breakouts Section
            st.markdown("### 📉 Bearish Breakout Performance")
            if bearish_events:
                # Main chart with markers
                bearish_fig = create_post_breakout_chart(events, 'BEARISH')
                st.plotly_chart(bearish_fig, use_container_width=True)

                # Statistics summary
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Distribution chart
                    bearish_dist_fig = create_breakout_distribution_chart(events, 'BEARISH')
                    st.plotly_chart(bearish_dist_fig, use_container_width=True)
                with col2:
                    st.markdown("#### Statistics")
                    avg_5d = sum(e['move_5d'] for e in bearish_events) / len(bearish_events)
                    avg_10d = sum(e['move_10d'] for e in bearish_events) / len(bearish_events)
                    avg_20d = sum(e['move_20d'] for e in bearish_events) / len(bearish_events)

                    # "Win" rate for bearish (price goes down)
                    win_5d = sum(1 for e in bearish_events if e['move_5d'] < 0) / len(bearish_events) * 100
                    win_10d = sum(1 for e in bearish_events if e['move_10d'] < 0) / len(bearish_events) * 100
                    win_20d = sum(1 for e in bearish_events if e['move_20d'] < 0) / len(bearish_events) * 100

                    st.markdown(f"""
                    | Period | Avg Move | Success* |
                    |--------|----------|----------|
                    | 5 Days | {avg_5d:+.1f}% | {win_5d:.0f}% |
                    | 10 Days | {avg_10d:+.1f}% | {win_10d:.0f}% |
                    | 20 Days | {avg_20d:+.1f}% | {win_20d:.0f}% |

                    *Success = price moved down
                    """)
            else:
                st.info("No bearish breakouts found in this period.")

            st.divider()

            # Legend/Help
            with st.expander("📖 How to Read These Charts"):
                st.markdown("""
                **Interactive Markers:**
                - Hover over any marker to see detailed information
                - Each marker represents one historical breakout event
                - Different symbols represent different time periods (5D, 10D, 20D)

                **What the data shows:**
                - **5 Days**: Short-term price reaction after breakout
                - **10 Days**: Medium-term follow-through
                - **20 Days**: Longer-term trend development

                **Distribution Charts:**
                - Shows the statistical spread of price moves
                - Box shows median and quartiles
                - Wider distribution = less predictable outcomes

                **Using this data:**
                - Consistent positive averages suggest reliable bullish breakouts
                - High win rates indicate the signal works well for this stock
                - Use with 200 DMA validation for best results
                """)
        else:
            st.info("No breakout events found for analysis.")

    with tab4:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Current Indicators")
            analysis_data = {
                "Indicator": ["BB Upper", "BB Middle", "BB Lower", "KC Upper", "KC Middle", "KC Lower", "BB Width", "ATR", "Momentum", "200 DMA"],
                "Value": [
                    f"₹{latest['BB_Upper']:.2f}",
                    f"₹{latest['BB_Middle']:.2f}",
                    f"₹{latest['BB_Lower']:.2f}",
                    f"₹{latest['KC_Upper']:.2f}",
                    f"₹{latest['KC_Middle']:.2f}",
                    f"₹{latest['KC_Lower']:.2f}",
                    f"{latest['BB_Width']:.2f}%",
                    f"₹{latest['ATR']:.2f}",
                    f"{latest['Squeeze_Momentum']:.4f}" if not pd.isna(latest['Squeeze_Momentum']) else "N/A",
                    f"₹{latest['DMA_200']:.2f}" if 'DMA_200' in latest and not pd.isna(latest['DMA_200']) else "N/A"
                ]
            }
            st.dataframe(pd.DataFrame(analysis_data), hide_index=True, use_container_width=True)

        with col2:
            st.subheader("Trading Signals")

            # 200 DMA Status
            if 'DMA_200' in latest and not pd.isna(latest['DMA_200']):
                above_dma = latest['Close'] > latest['DMA_200']
                dma_dist = ((latest['Close'] - latest['DMA_200']) / latest['DMA_200']) * 100
                if above_dma:
                    st.success(f"📊 **Above 200 DMA** ({dma_dist:+.1f}% from DMA)")
                else:
                    st.error(f"📊 **Below 200 DMA** ({dma_dist:+.1f}% from DMA)")

            if latest['Squeeze_Fire']:
                st.warning("⚠️ **SQUEEZE JUST FIRED!** Potential breakout.")
                if latest['Squeeze_Momentum'] > 0:
                    if 'DMA_200' in latest and not pd.isna(latest['DMA_200']) and latest['Close'] > latest['DMA_200']:
                        st.success("📈 **Valid Bullish Signal**: Price above 200 DMA. Consider long positions.")
                    else:
                        st.warning("📈 **Bullish Signal (Caution)**: Price below 200 DMA. Higher risk.")
                else:
                    if 'DMA_200' in latest and not pd.isna(latest['DMA_200']) and latest['Close'] < latest['DMA_200']:
                        st.error("📉 **Valid Bearish Signal**: Price below 200 DMA. Consider short positions.")
                    else:
                        st.warning("📉 **Bearish Signal (Caution)**: Price above 200 DMA. Higher risk.")
            elif latest['Squeeze_On']:
                st.info(f"🟢 **Squeeze Active** for {int(latest['Squeeze_Duration'])} days.")
                st.caption(f"BB Width: {latest['BB_Width']:.2f}% - Wait for breakout.")

                # Show momentum direction hint
                if latest['Squeeze_Momentum'] > 0:
                    st.caption("📈 Current momentum is bullish - potential upside breakout.")
                else:
                    st.caption("📉 Current momentum is bearish - potential downside breakout.")
            else:
                st.caption("⚪ No active squeeze. Watch for bands to contract.")


def render_watchlist():
    """Render watchlist page"""
    st.title("⭐ Watchlist")
    st.caption("Your saved stocks")

    db = DatabaseManager()
    watchlist = db.get_watchlist()

    if not watchlist:
        st.info("Your watchlist is empty. Add stocks from the Scanner.")
        return

    col1, col2 = st.columns([3, 1])
    with col2:
        refresh = st.button("🔄 Refresh", use_container_width=True)

    if refresh or 'watchlist_data' not in st.session_state:
        with st.spinner("Fetching data..."):
            watchlist_data = []
            for item in watchlist:
                result = scan_single_stock(item['symbol'], item.get('company_name', ''))
                if result:
                    result['target_price'] = item.get('target_price')
                    result['stop_loss'] = item.get('stop_loss')
                    result['notes'] = item.get('notes', '')
                    watchlist_data.append(result)
            st.session_state.watchlist_data = watchlist_data

    watchlist_data = st.session_state.get('watchlist_data', [])

    if not watchlist_data:
        st.warning("Could not fetch watchlist data.")
        return

    # Summary
    active = sum(1 for w in watchlist_data if w.get('squeeze_on'))
    fired = sum(1 for w in watchlist_data if w.get('squeeze_fire'))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", len(watchlist_data))
    with col2:
        st.metric("Active Squeezes", active)
    with col3:
        st.metric("Fired Today", fired)

    st.divider()

    for item in watchlist_data:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2.5, 1.5, 1.5, 1.5, 1])

            with col1:
                st.markdown(f"### {item['symbol']}")
                st.caption(item.get('company_name', ''))

            with col2:
                st.metric("Price", f"₹{item['current_price']:.2f}", f"{item['price_change_pct']:+.2f}%")

            with col3:
                status = "🟢 ON" if item['squeeze_on'] else ("🔴 FIRED" if item['squeeze_fire'] else "⚪ OFF")
                st.metric("Squeeze", status)

            with col4:
                d = item.get('momentum_direction', '')
                emoji = "📈" if "BULLISH" in str(d) else "📉"
                st.markdown(f"**{emoji}**")
                st.caption(f"BB: {item.get('bb_width', 0):.1f}%")

            with col5:
                if st.button("📊", key=f"v_{item['symbol']}"):
                    st.session_state.selected_stock = item['symbol']
                    st.session_state.current_page = "Stock Detail"
                    st.rerun()
                if st.button("🗑️", key=f"r_{item['symbol']}"):
                    db.remove_from_watchlist(item['symbol'])
                    del st.session_state['watchlist_data']
                    st.rerun()

            if item.get('notes'):
                st.caption(f"📝 {item['notes']}")

            st.divider()


def render_alerts():
    """Render alerts page"""
    st.title("🔔 Alerts")
    st.caption("Manage price and squeeze alerts")

    db = DatabaseManager()

    # Create alert
    with st.expander("➕ Create New Alert"):
        col1, col2 = st.columns(2)

        with col1:
            stocks = get_cached_stock_list()
            if not stocks.empty:
                symbol = st.selectbox("Stock", stocks['symbol'].tolist())
            else:
                symbol = st.text_input("Stock Symbol")

        with col2:
            alert_type = st.selectbox(
                "Type",
                ["PRICE_ABOVE", "PRICE_BELOW", "SQUEEZE_FIRE"],
                format_func=lambda x: {"PRICE_ABOVE": "📈 Price Above", "PRICE_BELOW": "📉 Price Below", "SQUEEZE_FIRE": "💥 Squeeze Fire"}.get(x, x)
            )

        if alert_type in ["PRICE_ABOVE", "PRICE_BELOW"]:
            threshold = st.number_input("Price ₹", min_value=0.0, value=100.0)
        else:
            threshold = 0.0

        if st.button("Create Alert", type="primary"):
            if symbol:
                db.create_alert(symbol, alert_type, threshold)
                st.success("Alert created!")
                st.rerun()

    st.divider()

    # Active alerts
    st.subheader("Active Alerts")
    alerts = db.get_active_alerts()

    if not alerts:
        st.info("No active alerts.")
    else:
        for alert in alerts:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"**{alert['symbol']}**")

            with col2:
                t = alert['alert_type']
                if t == "PRICE_ABOVE":
                    st.caption(f"📈 Above ₹{alert['threshold']:.2f}")
                elif t == "PRICE_BELOW":
                    st.caption(f"📉 Below ₹{alert['threshold']:.2f}")
                else:
                    st.caption("💥 Squeeze Fire")

            with col3:
                if st.button("🗑️", key=f"del_{alert['id']}"):
                    db.delete_alert(alert['id'])
                    st.rerun()

            st.divider()


def generate_all_stocks_post_breakout_data(symbols: list, period: str = "6mo", progress_callback=None) -> pd.DataFrame:
    """
    Generate post-breakout historical data for all scanned stocks.

    This creates a comprehensive CSV with historical squeeze events and their
    performance metrics (5d, 10d, 20d moves) for ALL stocks, not just fired ones.

    Args:
        symbols: List of stock symbols to analyze
        period: Historical data period
        progress_callback: Optional callback for progress updates

    Returns:
        DataFrame with all historical breakout data
    """
    from core.squeeze_detector import get_squeeze_history, detect_squeeze

    all_events = []

    for i, symbol in enumerate(symbols):
        if progress_callback:
            progress_callback(i + 1, len(symbols), symbol)

        try:
            # Fetch stock data
            df = fetch_stock_data(symbol, period=period)

            if df is None or df.empty:
                continue

            # Detect squeeze and get history
            df = detect_squeeze(df)
            events = get_squeeze_history(df)

            # Add symbol to each event and append to all_events
            for event in events:
                event['symbol'] = symbol
                # Get current stock info from scan results if available
                if 'scan_results' in st.session_state and not st.session_state.scan_results.empty:
                    stock_info = st.session_state.scan_results[
                        st.session_state.scan_results['symbol'] == symbol
                    ]
                    if not stock_info.empty:
                        event['current_squeeze_status'] = stock_info.iloc[0].get('squeeze_status', 'Unknown')
                        event['current_price'] = stock_info.iloc[0].get('current_price', 0)
                all_events.append(event)

        except Exception as e:
            # Skip stocks that fail to load
            continue

    if not all_events:
        return pd.DataFrame()

    # Create DataFrame
    events_df = pd.DataFrame(all_events)

    # Reorder columns for better readability
    preferred_order = [
        'symbol', 'direction', 'start_date', 'end_date', 'duration',
        'bb_width_before_breakout', 'min_bb_width',
        'move_5d', 'move_10d', 'move_20d',
        'price_at_breakout', 'breakout_close',
        'current_squeeze_status', 'current_price'
    ]

    # Only include columns that exist
    final_cols = [col for col in preferred_order if col in events_df.columns]
    # Add any remaining columns
    remaining_cols = [col for col in events_df.columns if col not in final_cols]
    final_cols.extend(remaining_cols)

    events_df = events_df[final_cols]

    # Rename columns for clarity
    rename_map = {
        'symbol': 'Symbol',
        'direction': 'Breakout_Direction',
        'start_date': 'Squeeze_Start',
        'end_date': 'Squeeze_End',
        'duration': 'Squeeze_Duration_Days',
        'bb_width_before_breakout': 'BB_Width_Before_Breakout',
        'min_bb_width': 'Min_BB_Width_During_Squeeze',
        'move_5d': 'Price_Move_5D_%',
        'move_10d': 'Price_Move_10D_%',
        'move_20d': 'Price_Move_20D_%',
        'price_at_breakout': 'Price_At_Breakout',
        'breakout_close': 'Breakout_Close',
        'current_squeeze_status': 'Current_Squeeze_Status',
        'current_price': 'Current_Price'
    }

    events_df = events_df.rename(columns={k: v for k, v in rename_map.items() if k in events_df.columns})

    return events_df


def render_post_breakout():
    """Render post-breakout analysis page"""
    st.title("📈 Post-Breakout Analysis")
    st.caption("Track performance of stocks after squeeze breakouts")

    # Mobile tip
    st.markdown("""
    <div class="mobile-only">
        <div class="mobile-tip-box">
            <p>📱 <strong>Tip:</strong> Swipe tables horizontally to see all data</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Header section with gradient
    st.markdown("""
    <div class="post-breakout-header">
        <h2>📊 Breakout Performance Tracker</h2>
        <p>Analyze how stocks perform after squeeze breakout signals are triggered</p>
    </div>
    """, unsafe_allow_html=True)

    # Check if scan results exist
    if 'scan_results' not in st.session_state or st.session_state.scan_results.empty:
        st.warning("⚠️ No scan results available. Please run a scan first to see post-breakout analysis.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Go to Scanner", use_container_width=True):
                st.session_state.current_page = "Scanner"
                st.rerun()
        with col2:
            if st.button("📖 View Help", use_container_width=True):
                st.session_state.current_page = "Help"
                st.rerun()
        return

    results_df = st.session_state.scan_results

    # Filter for fired squeezes
    fired_df = results_df[results_df['squeeze_status'] == 'Squeeze Fired'].copy() if 'squeeze_status' in results_df.columns else pd.DataFrame()

    # Summary metrics
    st.subheader("📊 Breakout Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_scanned = len(results_df)
        st.metric("Total Scanned", total_scanned)

    with col2:
        total_fired = len(fired_df)
        st.metric("Squeezes Fired", total_fired)

    with col3:
        if not fired_df.empty and 'Breakout' in fired_df.columns:
            bullish_count = len(fired_df[fired_df['Breakout'].str.contains('Bullish', case=False, na=False)])
            st.metric("Bullish Breakouts", bullish_count, delta=f"{bullish_count/total_fired*100:.0f}%" if total_fired > 0 else "0%")
        else:
            st.metric("Bullish Breakouts", 0)

    with col4:
        if not fired_df.empty and 'Breakout' in fired_df.columns:
            bearish_count = len(fired_df[fired_df['Breakout'].str.contains('Bearish', case=False, na=False)])
            st.metric("Bearish Breakouts", bearish_count, delta=f"{bearish_count/total_fired*100:.0f}%" if total_fired > 0 else "0%")
        else:
            st.metric("Bearish Breakouts", 0)

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Fired Squeezes", "📊 Performance Analysis", "📋 All Results", "📥 Historical Export"])

    with tab1:
        st.subheader("🔥 Recently Fired Squeezes")

        if fired_df.empty:
            st.info("No squeeze-fired signals found in the current scan results.")
        else:
            # Display columns to show
            display_cols = ['symbol', 'current_price', 'Breakout', 'signal_valid', 'bb_width', 'momentum_direction', 'squeeze_duration']
            available_cols = [col for col in display_cols if col in fired_df.columns]

            if available_cols:
                display_df = fired_df[available_cols].copy()

                # Rename columns for better readability
                rename_map = {
                    'symbol': 'Symbol',
                    'current_price': 'Price',
                    'Breakout': 'Breakout Type',
                    'signal_valid': 'Valid Signal',
                    'bb_width': 'BB Width %',
                    'momentum_direction': 'Momentum',
                    'squeeze_duration': 'Duration (Days)'
                }
                display_df = display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns})

                st.dataframe(display_df, use_container_width=True, hide_index=True)

                # Stock selection for detailed view
                st.divider()
                st.subheader("📈 View Stock Details")

                selected_symbol = st.selectbox(
                    "Select a stock to view details:",
                    options=fired_df['symbol'].tolist() if 'symbol' in fired_df.columns else [],
                    format_func=lambda x: f"{x} - {'Bullish' if 'Bullish' in str(fired_df[fired_df['symbol']==x]['Breakout'].values[0]) else 'Bearish'}" if 'symbol' in fired_df.columns and 'Breakout' in fired_df.columns else x
                )

                if selected_symbol:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📊 View Full Details", use_container_width=True):
                            st.session_state.selected_stock = selected_symbol
                            st.session_state.current_page = "Stock Detail"
                            st.rerun()
                    with col2:
                        if st.button("⭐ Add to Watchlist", use_container_width=True):
                            db = DatabaseManager()
                            stock_data = fired_df[fired_df['symbol'] == selected_symbol].iloc[0] if 'symbol' in fired_df.columns else {}
                            db.add_to_watchlist(
                                selected_symbol,
                                stock_data.get('current_price', 0),
                                notes=f"Added from Post-Breakout - {stock_data.get('Breakout', 'Unknown')} breakout"
                            )
                            st.success(f"✅ {selected_symbol} added to watchlist!")
            else:
                st.info("No display columns available in the data.")

    with tab2:
        st.subheader("📊 Breakout Performance Analysis")

        if fired_df.empty:
            st.info("No fired squeezes available for performance analysis.")
        else:
            # Performance by breakout type
            st.markdown("#### Performance by Breakout Type")

            if 'Breakout' in fired_df.columns:
                # Bullish breakouts analysis
                bullish_df = fired_df[fired_df['Breakout'].str.contains('Bullish', case=False, na=False)]
                bearish_df = fired_df[fired_df['Breakout'].str.contains('Bearish', case=False, na=False)]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("""
                    <div class="perf-card perf-card-positive">
                        <h4 style="color: #00D26A !important; margin: 0 0 0.5rem 0;">📈 Bullish Breakouts</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    if not bullish_df.empty:
                        st.metric("Count", len(bullish_df))
                        if 'signal_valid' in bullish_df.columns:
                            valid_count = bullish_df['signal_valid'].sum()
                            st.metric("Valid Signals", f"{valid_count} ({valid_count/len(bullish_df)*100:.0f}%)")
                        if 'bb_width' in bullish_df.columns:
                            st.metric("Avg BB Width", f"{bullish_df['bb_width'].mean():.2f}%")
                        if 'squeeze_duration' in bullish_df.columns:
                            st.metric("Avg Squeeze Duration", f"{bullish_df['squeeze_duration'].mean():.1f} days")
                    else:
                        st.info("No bullish breakouts")

                with col2:
                    st.markdown("""
                    <div class="perf-card perf-card-negative">
                        <h4 style="color: #EF4444 !important; margin: 0 0 0.5rem 0;">📉 Bearish Breakouts</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    if not bearish_df.empty:
                        st.metric("Count", len(bearish_df))
                        if 'signal_valid' in bearish_df.columns:
                            valid_count = bearish_df['signal_valid'].sum()
                            st.metric("Valid Signals", f"{valid_count} ({valid_count/len(bearish_df)*100:.0f}%)")
                        if 'bb_width' in bearish_df.columns:
                            st.metric("Avg BB Width", f"{bearish_df['bb_width'].mean():.2f}%")
                        if 'squeeze_duration' in bearish_df.columns:
                            st.metric("Avg Squeeze Duration", f"{bearish_df['squeeze_duration'].mean():.1f} days")
                    else:
                        st.info("No bearish breakouts")

            # BB Width distribution chart
            st.divider()
            st.markdown("#### BB Width Distribution")

            if 'bb_width' in fired_df.columns and not fired_df['bb_width'].isna().all():
                fig = go.Figure()

                fig.add_trace(go.Histogram(
                    x=fired_df['bb_width'],
                    nbinsx=20,
                    marker_color='#1E90FF',
                    opacity=0.8,
                    name='BB Width Distribution'
                ))

                fig.update_layout(
                    title="BB Width % Distribution of Fired Squeezes",
                    xaxis_title="BB Width %",
                    yaxis_title="Count",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("BB Width data not available for chart.")

            # Squeeze duration distribution
            if 'squeeze_duration' in fired_df.columns and not fired_df['squeeze_duration'].isna().all():
                st.markdown("#### Squeeze Duration Distribution")

                fig2 = go.Figure()

                fig2.add_trace(go.Histogram(
                    x=fired_df['squeeze_duration'],
                    nbinsx=15,
                    marker_color='#10B981',
                    opacity=0.8,
                    name='Duration Distribution'
                ))

                fig2.update_layout(
                    title="Squeeze Duration Distribution (Days)",
                    xaxis_title="Duration (Days)",
                    yaxis_title="Count",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400
                )

                st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("📋 All Scan Results")

        if results_df.empty:
            st.info("No scan results available.")
        else:
            # Filter options
            col1, col2, col3 = st.columns(3)

            with col1:
                status_filter = st.multiselect(
                    "Squeeze Status",
                    options=['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'],
                    default=['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired'],
                    key="post_breakout_status_filter"
                )

            with col2:
                if 'Breakout' in results_df.columns:
                    breakout_filter = st.multiselect(
                        "Breakout Type",
                        options=['Bullish', 'Bearish', '-'],
                        default=['Bullish', 'Bearish', '-'],
                        key="post_breakout_type_filter"
                    )
                else:
                    breakout_filter = None

            with col3:
                valid_only = st.checkbox("Valid Signals Only", value=False, key="post_breakout_valid_filter")

            # Apply filters
            filtered_df = results_df.copy()

            if 'squeeze_status' in filtered_df.columns and status_filter:
                filtered_df = filtered_df[filtered_df['squeeze_status'].isin(status_filter)]

            if breakout_filter and 'Breakout' in filtered_df.columns:
                mask = filtered_df['Breakout'].apply(lambda x: any(bt in str(x) for bt in breakout_filter))
                filtered_df = filtered_df[mask]

            if valid_only and 'signal_valid' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['signal_valid'] == True]

            # Display filtered results
            st.write(f"Showing {len(filtered_df)} of {len(results_df)} stocks")

            # Select columns to display
            display_cols = ['symbol', 'current_price', 'squeeze_status', 'Breakout', 'signal_valid', 'bb_width', 'momentum_direction']
            available_cols = [col for col in display_cols if col in filtered_df.columns]

            if available_cols:
                st.dataframe(filtered_df[available_cols], use_container_width=True, hide_index=True, height=500)

                # Export option
                st.divider()
                col1, col2 = st.columns(2)

                with col1:
                    csv_data = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_data,
                        file_name=f"post_breakout_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                with col2:
                    if st.button("🔄 Refresh Scan", use_container_width=True):
                        st.session_state.current_page = "Scanner"
                        st.rerun()

    with tab4:
        st.subheader("📥 Historical Post-Breakout Data Export")
        st.markdown("""
        Generate comprehensive historical squeeze data for **ALL scanned stocks** -
        not just fired squeezes. This includes price movements after each historical
        breakout (5-day, 10-day, 20-day returns).
        """)

        # Show info about what will be exported
        st.info("""
        **What's included in the export:**
        - All historical squeeze events for each scanned stock
        - Breakout direction (Bullish/Bearish/Invalid)
        - Squeeze duration and BB width metrics
        - Price moves: 5-day, 10-day, and 20-day % returns after each breakout
        - Current squeeze status and price
        """)

        # Get list of symbols from scan results
        if 'symbol' in results_df.columns:
            symbols = results_df['symbol'].tolist()
            st.write(f"**{len(symbols)} stocks** available for historical analysis")

            # Period selection for historical data
            col1, col2 = st.columns([2, 1])
            with col1:
                export_period = st.selectbox(
                    "Historical Data Period",
                    options=["6 Months", "1 Year", "2 Years"],
                    index=0,
                    help="Select how much historical data to analyze",
                    key="export_period_select"
                )
            with col2:
                period_map = {"6 Months": "6mo", "1 Year": "1y", "2 Years": "2y"}
                selected_period = period_map[export_period]

            st.divider()

            # Generate button
            if st.button("🔄 Generate Historical Data", type="primary", use_container_width=True):
                with st.spinner(f"Analyzing historical data for {len(symbols)} stocks..."):
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    def update_progress(current, total, symbol):
                        progress_bar.progress(current / total)
                        status_text.text(f"Processing {current}/{total}: {symbol}")

                    # Generate the data
                    historical_df = generate_all_stocks_post_breakout_data(
                        symbols,
                        period=selected_period,
                        progress_callback=update_progress
                    )

                    progress_bar.empty()
                    status_text.empty()

                    if not historical_df.empty:
                        # Store in session state for download
                        st.session_state.historical_export_df = historical_df

                        st.success(f"✅ Generated {len(historical_df)} historical breakout events!")

                        # Show summary stats
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Events", len(historical_df))
                        with col2:
                            if 'Breakout_Direction' in historical_df.columns:
                                bullish = len(historical_df[historical_df['Breakout_Direction'] == 'BULLISH'])
                                st.metric("Bullish", bullish)
                        with col3:
                            if 'Breakout_Direction' in historical_df.columns:
                                bearish = len(historical_df[historical_df['Breakout_Direction'] == 'BEARISH'])
                                st.metric("Bearish", bearish)
                        with col4:
                            unique_stocks = historical_df['Symbol'].nunique() if 'Symbol' in historical_df.columns else 0
                            st.metric("Stocks with Data", unique_stocks)
                    else:
                        st.warning("No historical breakout data found for the selected stocks.")

            # Show preview and download if data exists
            if 'historical_export_df' in st.session_state and not st.session_state.historical_export_df.empty:
                st.divider()
                st.subheader("📋 Data Preview")

                historical_df = st.session_state.historical_export_df

                # Show preview (first 100 rows)
                st.dataframe(
                    historical_df.head(100),
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )

                if len(historical_df) > 100:
                    st.caption(f"Showing first 100 of {len(historical_df)} rows")

                # Download button
                st.divider()
                csv_data = historical_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Complete Historical Data (CSV)",
                    data=csv_data,
                    file_name=f"all_stocks_historical_breakouts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )

                # Show column descriptions
                with st.expander("📖 Column Descriptions"):
                    st.markdown("""
                    | Column | Description |
                    |--------|-------------|
                    | **Symbol** | Stock ticker symbol |
                    | **Breakout_Direction** | BULLISH, BEARISH, or INVALID |
                    | **Squeeze_Start** | Date squeeze began |
                    | **Squeeze_End** | Date squeeze ended (breakout) |
                    | **Squeeze_Duration_Days** | Number of days in squeeze |
                    | **BB_Width_Before_Breakout** | Bollinger Band width % just before breakout |
                    | **Min_BB_Width_During_Squeeze** | Tightest BB width during squeeze |
                    | **Price_Move_5D_%** | % price change 5 days after breakout |
                    | **Price_Move_10D_%** | % price change 10 days after breakout |
                    | **Price_Move_20D_%** | % price change 20 days after breakout |
                    | **Price_At_Breakout** | Stock price when squeeze fired |
                    | **Current_Squeeze_Status** | Current status (if available) |
                    | **Current_Price** | Current stock price (if available) |

                    **Note:** INVALID direction means the breakout didn't align with 200 DMA position.
                    """)
        else:
            st.warning("No symbol data available in scan results.")

    # Back to scanner button
    st.divider()
    if st.button("← Back to Scanner", use_container_width=True):
        st.session_state.current_page = "Scanner"
        st.rerun()


def render_help():
    """Render comprehensive help page with mobile-friendly tabs"""
    st.title("ℹ️ Help & Documentation")
    st.caption("Learn how to use the NSE Squeeze Scanner effectively")

    # Mobile tip
    st.markdown("""
    <div class="mobile-only">
        <div class="mobile-tip-box">
            <p>📱 <strong>Tip:</strong> Swipe tabs horizontally to see all sections</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mobile-friendly tabs for main sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Getting Started",
        "📊 Indicators",
        "🎯 Strategy",
        "❓ FAQ"
    ])

    with tab1:
        st.markdown("""
        ## 🚀 Getting Started

        Welcome to NSE Squeeze Scanner! This tool helps you identify potential breakout opportunities in Indian stocks using the TTM Squeeze indicator.

        ### How to Use This App

        #### 1️⃣ Select Indices
        - Navigate to the **Scanner** page
        - Choose from Nifty 50, Midcap, Smallcap, or Sectoral indices
        - You can select multiple indices at once
        - Click **"Scan Stocks"** to start analysis

        #### 2️⃣ Review Results
        - View all stocks with potential breakouts in the results table
        - Use filters to narrow down results by squeeze status, breakout type, etc.
        - Sort by any column to find the best setups

        #### 3️⃣ Analyze Individual Stocks
        - Click on any stock row or select from dropdown to see detailed analysis
        - View price charts with squeeze indicators
        - Check historical squeeze performance

        #### 4️⃣ Track Breakouts
        - Visit the **Post-Breakout** page to see all fired squeezes
        - Analyze performance metrics and patterns
        - Download results for further analysis

        ### 📱 Mobile Tips
        - Use the **sidebar menu** (tap ☰ or swipe from left) to navigate between pages
        - Tables scroll horizontally - **swipe left/right** to see all columns
        - Rotate device to **landscape mode** for better chart viewing
        - Tap on expandable sections to reveal more details

        ---

        ### Quick Start Checklist
        - [ ] Go to Scanner page
        - [ ] Select at least one index (e.g., Nifty 50)
        - [ ] Click "Scan Stocks"
        - [ ] Review stocks with "Squeeze Fired" status
        - [ ] Check if signals are "Valid" (aligned with 200 DMA)
        - [ ] Add interesting stocks to Watchlist
        """)

        st.info("💡 **Pro Tip:** Start with Nifty 50 for the most liquid stocks, then expand to Midcap and Smallcap for more opportunities.")

    with tab2:
        st.markdown("""
        ## 📊 Technical Indicators Explained

        ### Bollinger Bands (BB)

        Bollinger Bands are volatility bands placed above and below a moving average.

        | Component | Calculation |
        |-----------|-------------|
        | **Middle Band** | 20-period Simple Moving Average (SMA) |
        | **Upper Band** | Middle Band + (2 × Standard Deviation) |
        | **Lower Band** | Middle Band - (2 × Standard Deviation) |

        **BB Width Formula:**
        ```
        BB Width % = ((Upper - Lower) / Middle) × 100
        ```
        - Lower BB Width = Tighter squeeze = Bigger potential breakout
        - Use the BB Width slider to filter stocks with tighter squeezes

        ---

        ### Keltner Channels (KC)

        Keltner Channels use Average True Range (ATR) to define volatility.

        | Component | Calculation |
        |-----------|-------------|
        | **Middle Line** | 20-period EMA |
        | **Upper Channel** | EMA + (1.5 × ATR) |
        | **Lower Channel** | EMA - (1.5 × ATR) |

        - More stable than Bollinger Bands due to ATR smoothing
        - Used in conjunction with BB to detect squeeze conditions

        ---

        ### TTM Squeeze Indicator

        The squeeze occurs when Bollinger Bands move **inside** Keltner Channels, indicating low volatility.

        | Status | Meaning | Visual |
        |--------|---------|--------|
        | **Squeeze ON** 🟢 | BB inside KC - volatility contracting | Green dots |
        | **Squeeze OFF** ⚪ | BB outside KC - normal volatility | Gray dots |
        | **Squeeze FIRED** 🔴 | Just transitioned from ON to OFF | Red signal |

        ---

        ### Momentum Oscillator

        The momentum indicator shows both direction and strength of price movement.

        | State | Direction | Strength | Signal |
        |-------|-----------|----------|--------|
        | **BULLISH_UP** 📈 | Positive | Increasing | Strongest buy |
        | **BULLISH_DOWN** | Positive | Decreasing | Weakening buy |
        | **BEARISH_DOWN** 📉 | Negative | Increasing | Strongest sell |
        | **BEARISH_UP** | Negative | Decreasing | Weakening sell |

        **Histogram Colors:**
        - 🟢 Lime Green: Bullish momentum increasing
        - 🟢 Dark Green: Bullish momentum decreasing
        - 🔴 Red: Bearish momentum increasing
        - 🔴 Dark Red: Bearish momentum decreasing

        ---

        ### 200-Day Moving Average (200 DMA)

        The 200 DMA is a long-term trend indicator used to validate breakout signals.

        **Signal Validation Rules:**
        - **Bullish signals** are valid only when price is **ABOVE** the 200 DMA
        - **Bearish signals** are valid only when price is **BELOW** the 200 DMA

        | Price vs 200 DMA | Bullish Signal | Bearish Signal |
        |-----------------|----------------|----------------|
        | Above 200 DMA | ✅ Valid | ⚠️ Invalid |
        | Below 200 DMA | ⚠️ Invalid | ✅ Valid |
        """)

    with tab3:
        st.markdown("""
        ## 🎯 Trading Strategy

        ### The TTM Squeeze Strategy

        #### Step 1: Identify Squeeze
        Markets alternate between periods of low volatility (consolidation) and high volatility (trending). The Squeeze indicator finds these consolidation periods.

        #### Step 2: Wait for Squeeze Fire
        When Bollinger Bands break out of Keltner Channels, it signals the end of consolidation and the potential beginning of a new trend.

        #### Step 3: Determine Direction
        Use the momentum oscillator to determine the breakout direction:

        **📈 Bullish Setup:**
        - Squeeze fires (transitions from ON to OFF)
        - Momentum turns positive (green histogram)
        - Price closes above upper Bollinger Band
        - **CRITICAL:** Price must be above 200 DMA ✅

        **📉 Bearish Setup:**
        - Squeeze fires (transitions from ON to OFF)
        - Momentum turns negative (red histogram)
        - Price closes below lower Bollinger Band
        - **CRITICAL:** Price must be below 200 DMA ✅

        ---

        ### ⚠️ Important Rules

        #### Signal Validation
        | Signal Type | 200 DMA Requirement | Result |
        |-------------|---------------------|--------|
        | Bullish | Price ABOVE 200 DMA | ✅ Valid |
        | Bullish | Price BELOW 200 DMA | ❌ Invalid |
        | Bearish | Price BELOW 200 DMA | ✅ Valid |
        | Bearish | Price ABOVE 200 DMA | ❌ Invalid |

        #### Entry Points
        - **Aggressive:** Enter immediately on squeeze fire
        - **Conservative:** Wait for next candle confirmation

        #### Risk Management
        - **Stop Loss:** Recent swing low (bullish) or swing high (bearish)
        - **Take Profit:** When momentum starts weakening
        - **Position Size:** Never risk more than 1-2% per trade

        ---

        ### 📈 Success Tips

        1. **Always check 200 DMA position** - This is non-negotiable
        2. **Look for tight squeezes** - Lower BB Width = bigger potential move
        3. **Confirm with volume** - Volume should expand on breakout
        4. **Use proper risk management** - Define stop loss before entry
        5. **Don't fight the trend** - Trade with the larger trend direction
        6. **Be patient** - Wait for the right setup, don't force trades
        7. **Track your trades** - Use the Post-Breakout page to analyze results
        """)

        st.warning("⚠️ **Disclaimer:** This tool is for educational and informational purposes only. Always do your own research and consult with a financial advisor before making trading decisions.")

    with tab4:
        st.markdown("""
        ## ❓ Frequently Asked Questions

        ### General Questions

        **Q: How often is data updated?**
        A: Data is fetched from NSE in real-time when you run a scan. Historical data is cached to improve performance and reduce API load.

        **Q: Can I use this for intraday trading?**
        A: This scanner is designed for **daily timeframe** analysis. For intraday trading, you would need real-time tick data which is not currently supported.

        **Q: How accurate are the signals?**
        A: No trading signal is 100% accurate. The squeeze indicator identifies potential opportunities, but you should always use proper risk management and combine with your own analysis.

        ---

        ### Technical Questions

        **Q: What is a "valid" signal?**
        A: A valid signal meets the 200 DMA criteria:
        - Bullish signals: Price must be ABOVE 200 DMA
        - Bearish signals: Price must be BELOW 200 DMA

        **Q: Why do some signals show as invalid?**
        A: Invalid signals don't meet the 200 DMA requirement. Trading against the long-term trend carries higher risk. These signals are still shown but should be treated with caution.

        **Q: How is BB Width calculated?**
        A: `BB Width % = ((Upper Band - Lower Band) / Middle Band) × 100`

        **Q: What squeeze duration should I look for?**
        A: Longer squeezes (7+ days) often lead to bigger breakouts, but there's no magic number. Use the duration filter to experiment.

        ---

        ### Mobile Usage

        **Q: How do I navigate on mobile?**
        A: Tap the **hamburger menu (☰)** in the top-left corner or swipe from the left edge to open the navigation sidebar.

        **Q: Why can't I see all table columns?**
        A: Tables scroll horizontally on mobile. Swipe left/right to see all columns.

        **Q: Charts are hard to read on mobile**
        A: Try rotating your device to **landscape mode** for better chart viewing.

        ---

        ### Data & Privacy

        **Q: Is my data stored?**
        A: No personal data is collected. Scan results are stored only in your browser session and cleared when you close the app.

        **Q: Can I export my results?**
        A: Yes! Use the **"Download CSV"** button on the Scanner and Post-Breakout pages.

        ---

        ### Troubleshooting

        **Q: The app is loading slowly**
        A: This can happen during market hours when NSE servers are busy. Try:
        - Reducing the number of indices selected
        - Waiting a few minutes and trying again
        - Checking your internet connection

        **Q: I see an error message**
        A: Common causes and solutions:
        - **NSE website down:** Wait and try again
        - **Too many requests:** Wait 1-2 minutes before retrying
        - **Network error:** Check your internet connection

        **Q: Navigation menu not working**
        A: Try refreshing the page (F5 or pull down to refresh on mobile).
        """)

        # Quick links
        st.divider()
        st.markdown("### 📧 Need More Help?")
        st.markdown("""
        If you have questions not covered here:
        - Check our [GitHub Repository](https://github.com/ManojKathare/nse-squeeze-scanner)
        - Report issues or request features via GitHub Issues
        """)

    st.divider()

    # Quick Reference Section
    st.subheader("📌 Quick Reference")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Status Icons:**
        - 🟢 Squeeze ON (consolidation)
        - ⚪ Squeeze OFF (normal)
        - 🔴 Squeeze FIRED (breakout!)
        - 📈 Bullish momentum
        - 📉 Bearish momentum
        - ⭐ In watchlist
        - ✅ Valid signal
        - ⚠️ Invalid (against trend)
        """)

    with col2:
        st.markdown("""
        **Best Practices:**
        1. Use 5Y data for accurate 200 DMA
        2. Focus on valid signals only
        3. Look for tight squeezes (low BB Width)
        4. Confirm breakouts with volume
        5. Always use stop losses
        6. Track performance via Post-Breakout
        """)

    # Navigation quick links
    st.divider()
    st.markdown("### 🔗 Quick Navigation")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Go to Scanner", use_container_width=True):
            st.session_state.current_page = "Scanner"
            st.rerun()

    with col2:
        if st.button("📈 Post-Breakout", use_container_width=True):
            st.session_state.current_page = "Post-Breakout"
            st.rerun()

    with col3:
        if st.button("⭐ Watchlist", use_container_width=True):
            st.session_state.current_page = "Watchlist"
            st.rerun()


def main():
    """Main application"""
    init_session_state()

    # ========== APPLY PENDING PRESET BEFORE ANY WIDGETS ==========
    # This is the ONLY place where filter session state can be safely modified
    apply_pending_preset_if_needed()

    # Page configuration for navigation
    pages = [
        {"icon": "🔍", "name": "Scanner", "key": "Scanner"},
        {"icon": "📊", "name": "Stock Detail", "key": "Stock Detail"},
        {"icon": "📈", "name": "Post-Breakout", "key": "Post-Breakout", "badge": "NEW"},
        {"icon": "⭐", "name": "Watchlist", "key": "Watchlist"},
        {"icon": "🔔", "name": "Alerts", "key": "Alerts"},
        {"icon": "ℹ️", "name": "Help", "key": "Help"}
    ]

    # Ensure current_page is valid
    valid_keys = [p["key"] for p in pages]
    if st.session_state.current_page not in valid_keys:
        st.session_state.current_page = "Scanner"

    # Sidebar navigation with button-based menu (better for mobile)
    with st.sidebar:
        st.markdown("## 📊 NSE Squeeze Scanner")
        st.caption("Bollinger Bands Squeeze Detector")
        st.divider()

        # Navigation label
        st.markdown("**📱 Navigation**")

        # Button-based navigation (more clickable on mobile than radio)
        for page in pages:
            is_active = st.session_state.current_page == page["key"]

            # Create button label with badge if applicable
            label = f"{page['icon']} {page['name']}"
            if page.get('badge'):
                label += f" 🆕"

            # Use primary type for active page, secondary for others
            if st.button(
                label,
                key=f"nav_btn_{page['key']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_page = page["key"]
                st.rerun()

        st.divider()

        st.markdown("### 📘 Quick Info")
        st.markdown("""
**Squeeze Status:**
- 🟢 ON = Bands contracting
- 🔴 FIRED = Just ended
- ⚪ OFF = No squeeze

**200 DMA Validation:**
- ✓ Valid = With trend
- ⚠️ Caution = Against trend

**Momentum:**
- 📈 Bullish
- 📉 Bearish
        """)

        st.divider()

        # Quick actions for mobile
        st.markdown("### ⚡ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄", key="refresh_btn", help="Refresh page"):
                st.rerun()
        with col2:
            if st.button("🏠", key="home_btn", help="Go to Scanner"):
                st.session_state.current_page = "Scanner"
                st.rerun()

        st.divider()
        st.caption("Made with ❤️ for Indian Traders")
        st.caption(f"v2.1 • {datetime.now().strftime('%b %Y')}")

    # Render page based on current selection
    if st.session_state.current_page == "Scanner":
        render_scanner()
    elif st.session_state.current_page == "Stock Detail":
        render_stock_detail()
    elif st.session_state.current_page == "Post-Breakout":
        render_post_breakout()
    elif st.session_state.current_page == "Watchlist":
        render_watchlist()
    elif st.session_state.current_page == "Alerts":
        render_alerts()
    elif st.session_state.current_page == "Help":
        render_help()
    else:
        # Default to scanner
        render_scanner()


if __name__ == "__main__":
    main()
