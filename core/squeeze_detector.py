"""Squeeze detection module - Core algorithm for BB/KC squeeze pattern"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MIN_DATA_POINTS, MAX_WORKERS, DEFAULT_PERIOD
from core.indicators import calculate_all_indicators
from core.data_fetcher import fetch_stock_data


def detect_squeeze(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect Bollinger Bands Squeeze Pattern.

    SQUEEZE ON: Bollinger Bands are INSIDE Keltner Channels
                BB_Lower > KC_Lower AND BB_Upper < KC_Upper

    SQUEEZE OFF: Bollinger Bands are OUTSIDE Keltner Channels

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with squeeze indicator columns added
    """
    df = df.copy()

    # Calculate all indicators
    df = calculate_all_indicators(df)

    # Squeeze Detection
    df['Squeeze_On'] = (df['BB_Lower'] > df['KC_Lower']) & (df['BB_Upper'] < df['KC_Upper'])
    df['Squeeze_Off'] = ~df['Squeeze_On']

    # Detect squeeze "fire" (transition from ON to OFF)
    squeeze_on_shifted = df['Squeeze_On'].shift(1)
    squeeze_on_shifted = squeeze_on_shifted.where(squeeze_on_shifted.notna(), False)
    df['Squeeze_Fire'] = squeeze_on_shifted & df['Squeeze_Off']

    # Calculate squeeze duration
    squeeze_duration = []
    count = 0
    for squeeze_on in df['Squeeze_On']:
        if squeeze_on:
            count += 1
        else:
            count = 0
        squeeze_duration.append(count)

    df['Squeeze_Duration'] = squeeze_duration

    return df


def detect_entry_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect entry signals with 200 DMA validation.

    CRITICAL: Breakout is TRUE only if:
    - BULLISH: Price ABOVE 200 DMA
    - BEARISH: Price BELOW 200 DMA

    Args:
        df: DataFrame with squeeze detection columns

    Returns:
        DataFrame with entry signal columns added
    """
    df = df.copy()

    # Ensure squeeze detection is done
    if 'Squeeze_Fire' not in df.columns:
        df = detect_squeeze(df)

    # Initialize signal columns
    df['long_signal'] = False
    df['short_signal'] = False
    df['breakout_detected'] = False
    df['is_valid_breakout'] = False
    df['invalid_reason'] = ''

    for i in range(1, len(df)):
        if df['Squeeze_Fire'].iloc[i]:
            # Get current values
            momentum = df['Squeeze_Momentum'].iloc[i] if not pd.isna(df['Squeeze_Momentum'].iloc[i]) else 0
            close = df['Close'].iloc[i]
            bb_upper = df['BB_Upper'].iloc[i]
            bb_lower = df['BB_Lower'].iloc[i]
            dma_200 = df['DMA_200'].iloc[i] if 'DMA_200' in df.columns and not pd.isna(df['DMA_200'].iloc[i]) else None

            # BULLISH BREAKOUT
            if momentum > 0 and close > bb_upper:
                df.loc[df.index[i], 'breakout_detected'] = True

                # VALIDATE: Must be above 200 DMA
                if dma_200 is not None and close > dma_200:
                    df.loc[df.index[i], 'long_signal'] = True
                    df.loc[df.index[i], 'is_valid_breakout'] = True
                else:
                    df.loc[df.index[i], 'invalid_reason'] = 'Price below 200 DMA (bullish invalid)'

            # BEARISH BREAKOUT
            elif momentum < 0 and close < bb_lower:
                df.loc[df.index[i], 'breakout_detected'] = True

                # VALIDATE: Must be below 200 DMA
                if dma_200 is not None and close < dma_200:
                    df.loc[df.index[i], 'short_signal'] = True
                    df.loc[df.index[i], 'is_valid_breakout'] = True
                else:
                    df.loc[df.index[i], 'invalid_reason'] = 'Price above 200 DMA (bearish invalid)'

    # Add signal type column
    df['signal_type'] = 'None'
    df.loc[df['long_signal'], 'signal_type'] = 'Bullish Breakout (Valid)'
    df.loc[df['short_signal'], 'signal_type'] = 'Bearish Breakout (Valid)'
    df.loc[(df['breakout_detected']) & (~df['is_valid_breakout']), 'signal_type'] = 'Invalid Breakout'

    return df


def prepare_results_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare results DataFrame with all necessary columns for filtering.

    Args:
        df: DataFrame with scan results

    Returns:
        DataFrame with additional filter columns
    """
    df = df.copy()

    # Calculate distance from 200 DMA (absolute percentage)
    if 'close' in df.columns and '200_dma' in df.columns:
        df['distance_from_200dma_pct'] = np.where(
            df['close'] > df['200_dma'],
            ((df['close'] - df['200_dma']) / df['200_dma']) * 100,
            ((df['200_dma'] - df['close']) / df['200_dma']) * 100
        )

        # Add position relative to 200 DMA
        df['position_vs_200dma'] = np.where(df['close'] > df['200_dma'], 'Above', 'Below')

    # Handle column name variations (lowercase vs capitalized)
    close_col = 'close' if 'close' in df.columns else ('Close' if 'Close' in df.columns else None)
    dma_col = '200_dma' if '200_dma' in df.columns else ('dma_200' if 'dma_200' in df.columns else ('DMA_200' if 'DMA_200' in df.columns else None))

    if close_col and dma_col:
        df['distance_from_200dma_pct'] = np.where(
            df[close_col] > df[dma_col],
            ((df[close_col] - df[dma_col]) / df[dma_col]) * 100,
            ((df[dma_col] - df[close_col]) / df[dma_col]) * 100
        )
        df['position_vs_200dma'] = np.where(df[close_col] > df[dma_col], 'Above', 'Below')

    # Ensure BB width percentage exists
    if 'bb_width_pct' not in df.columns:
        bb_upper = 'bb_upper' if 'bb_upper' in df.columns else ('BB_Upper' if 'BB_Upper' in df.columns else None)
        bb_lower = 'bb_lower' if 'bb_lower' in df.columns else ('BB_Lower' if 'BB_Lower' in df.columns else None)
        bb_middle = 'bb_middle' if 'bb_middle' in df.columns else ('BB_Middle' if 'BB_Middle' in df.columns else None)

        if bb_upper and bb_lower and bb_middle:
            df['bb_width_pct'] = ((df[bb_upper] - df[bb_lower]) / df[bb_middle]) * 100

    # Ensure squeeze status exists
    if 'squeeze_status' not in df.columns:
        squeeze_on = 'squeeze_on' if 'squeeze_on' in df.columns else ('Squeeze_On' if 'Squeeze_On' in df.columns else None)
        squeeze_fire = 'squeeze_fire' if 'squeeze_fire' in df.columns else ('Squeeze_Fire' if 'Squeeze_Fire' in df.columns else None)

        if squeeze_on and squeeze_fire:
            df['squeeze_status'] = 'Squeeze OFF'
            df.loc[df[squeeze_on] == True, 'squeeze_status'] = 'Squeeze ON'
            df.loc[df[squeeze_fire] == True, 'squeeze_status'] = 'Squeeze Fired'

    return df


def scan_single_stock(symbol: str, company_name: str = '',
                      period: str = DEFAULT_PERIOD) -> Optional[Dict]:
    """
    Scan a single stock for squeeze condition.

    Args:
        symbol: Stock symbol
        company_name: Company name
        period: Data period

    Returns:
        Dictionary with scan results or None if failed
    """
    try:
        df = fetch_stock_data(symbol, period)

        if df is None or df.empty or len(df) < MIN_DATA_POINTS:
            return None

        # Detect squeeze
        df = detect_squeeze(df)

        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # Calculate price change
        price_change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

        # Get 200 DMA values if available
        dma_200 = round(float(latest['DMA_200']), 2) if 'DMA_200' in latest and not pd.isna(latest['DMA_200']) else None
        above_dma_200 = bool(latest['Above_DMA_200']) if 'Above_DMA_200' in latest and not pd.isna(latest['Above_DMA_200']) else None
        dma_200_distance = round(float(latest['DMA_200_Distance']), 2) if 'DMA_200_Distance' in latest and not pd.isna(latest['DMA_200_Distance']) else None

        # Determine if signal is valid based on 200 DMA
        # Bullish signals are valid only if price > 200 DMA
        # Bearish signals are valid only if price < 200 DMA
        momentum = round(float(latest['Squeeze_Momentum']), 4) if not pd.isna(latest['Squeeze_Momentum']) else 0
        signal_valid = True
        if above_dma_200 is not None:
            if momentum > 0:  # Bullish signal
                signal_valid = above_dma_200
            else:  # Bearish signal
                signal_valid = not above_dma_200

        return {
            'symbol': symbol,
            'company_name': company_name,
            'current_price': round(float(latest['Close']), 2),
            'price_change_pct': round(float(price_change_pct), 2),
            'squeeze_on': bool(latest['Squeeze_On']),
            'squeeze_off': bool(latest['Squeeze_Off']),
            'squeeze_fire': bool(latest['Squeeze_Fire']),
            'squeeze_duration': int(latest['Squeeze_Duration']),
            'momentum': momentum,
            'momentum_direction': str(latest['Momentum_Direction']),
            'bb_width': round(float(latest['BB_Width']), 2) if not pd.isna(latest['BB_Width']) else 0,
            'volume': int(latest['Volume']) if not pd.isna(latest['Volume']) else 0,
            'dma_200': dma_200,
            'above_dma_200': above_dma_200,
            'dma_200_distance': dma_200_distance,
            'signal_valid': signal_valid
        }
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None


def scan_all_stocks(stocks_df: pd.DataFrame, period: str = DEFAULT_PERIOD,
                   progress_callback=None) -> pd.DataFrame:
    """
    Scan all stocks for squeeze patterns.

    Args:
        stocks_df: DataFrame with 'symbol' and 'company_name' columns
        period: Data period
        progress_callback: Optional callback for progress updates

    Returns:
        DataFrame with scan results
    """
    results = []
    total = len(stocks_df)
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for _, row in stocks_df.iterrows():
            future = executor.submit(
                scan_single_stock,
                row['symbol'],
                row.get('company_name', ''),
                period
            )
            futures[future] = row['symbol']

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    # Sort by squeeze status and duration
    df = df.sort_values(
        by=['squeeze_on', 'squeeze_fire', 'squeeze_duration', 'momentum'],
        ascending=[False, False, False, False]
    )

    return df.reset_index(drop=True)


def get_squeeze_history(df: pd.DataFrame) -> List[Dict]:
    """
    Extract historical squeeze events from stock data.

    Args:
        df: DataFrame with squeeze detection columns

    Returns:
        List of squeeze events with start, end, duration, direction, bb_width_before_breakout
    """
    if 'Squeeze_On' not in df.columns:
        df = detect_squeeze(df)

    # Reset index if needed to ensure proper iteration
    df = df.reset_index(drop=True)

    events = []
    in_squeeze = False
    start_idx = None
    min_bb_width = None  # Track minimum BB width during squeeze

    for i in range(len(df)):
        row = df.iloc[i]

        if row['Squeeze_On'] and not in_squeeze:
            # Squeeze started
            in_squeeze = True
            start_idx = i
            min_bb_width = row['BB_Width'] if not pd.isna(row['BB_Width']) else 999

        elif row['Squeeze_On'] and in_squeeze:
            # During squeeze - track minimum BB width (tightest squeeze)
            if not pd.isna(row['BB_Width']) and row['BB_Width'] < min_bb_width:
                min_bb_width = row['BB_Width']

        elif not row['Squeeze_On'] and in_squeeze:
            # Squeeze ended (fired)
            in_squeeze = False

            start_row = df.iloc[start_idx]
            end_row = row

            # BB Width just before breakout (previous day)
            prev_row = df.iloc[i - 1] if i > 0 else row
            bb_width_before = prev_row['BB_Width'] if not pd.isna(prev_row['BB_Width']) else 0

            # Determine breakout direction based on momentum AND 200 DMA position
            # CRITICAL: Bullish breakout ONLY if price > 200 DMA
            # CRITICAL: Bearish breakout ONLY if price < 200 DMA
            momentum = row['Squeeze_Momentum']
            price = row['Close']
            dma_200 = row['DMA_200'] if 'DMA_200' in df.columns and not pd.isna(row['DMA_200']) else None

            direction = None
            if dma_200 is not None:
                if momentum > 0 and price > dma_200:
                    direction = 'BULLISH'
                elif momentum < 0 and price < dma_200:
                    direction = 'BEARISH'
                else:
                    # Invalid breakout - momentum doesn't align with 200 DMA position
                    direction = 'INVALID'
            else:
                # No 200 DMA data available, fallback to momentum only (less reliable)
                direction = 'BULLISH' if momentum > 0 else 'BEARISH'

            # Calculate price move after breakout (5, 10, 20 days)
            price_at_breakout = row['Close']
            price_5d = df.iloc[min(i + 5, len(df) - 1)]['Close'] if i + 5 < len(df) else row['Close']
            price_10d = df.iloc[min(i + 10, len(df) - 1)]['Close'] if i + 10 < len(df) else row['Close']
            price_20d = df.iloc[min(i + 20, len(df) - 1)]['Close'] if i + 20 < len(df) else row['Close']

            move_5d = ((price_5d - price_at_breakout) / price_at_breakout) * 100
            move_10d = ((price_10d - price_at_breakout) / price_at_breakout) * 100
            move_20d = ((price_20d - price_at_breakout) / price_at_breakout) * 100

            events.append({
                'start_date': start_row['Date'] if 'Date' in df.columns else start_idx,
                'end_date': end_row['Date'] if 'Date' in df.columns else i,
                'duration': i - start_idx,
                'direction': direction,
                'bb_width_before': round(float(bb_width_before), 2),
                'min_bb_width': round(float(min_bb_width), 2) if min_bb_width else 0,
                'price_at_breakout': round(float(price_at_breakout), 2),
                'move_5d': round(float(move_5d), 2),
                'move_10d': round(float(move_10d), 2),
                'move_20d': round(float(move_20d), 2),
                'momentum': round(float(row['Squeeze_Momentum']), 4) if not pd.isna(row['Squeeze_Momentum']) else 0
            })

            min_bb_width = None

    # If currently in squeeze, add as ongoing
    if in_squeeze and start_idx is not None:
        latest = df.iloc[-1]
        start_row = df.iloc[start_idx]
        events.append({
            'start_date': start_row['Date'] if 'Date' in df.columns else start_idx,
            'end_date': 'Ongoing',
            'duration': len(df) - start_idx,
            'direction': 'PENDING',
            'bb_width_before': round(float(latest['BB_Width']), 2) if not pd.isna(latest['BB_Width']) else 0,
            'min_bb_width': round(float(min_bb_width), 2) if min_bb_width else 0,
            'price_at_breakout': 0,
            'move_5d': 0,
            'move_10d': 0,
            'move_20d': 0,
            'momentum': round(float(latest['Squeeze_Momentum']), 4) if not pd.isna(latest['Squeeze_Momentum']) else 0
        })

    return events


def get_squeeze_summary(scan_results: pd.DataFrame) -> Dict:
    """
    Get summary statistics from scan results.

    Args:
        scan_results: DataFrame from scan_all_stocks

    Returns:
        Dictionary with summary stats
    """
    if scan_results.empty:
        return {
            'total_stocks': 0,
            'active_squeezes': 0,
            'fired_today': 0,
            'bullish_momentum': 0,
            'bearish_momentum': 0
        }

    return {
        'total_stocks': len(scan_results),
        'active_squeezes': int(scan_results['squeeze_on'].sum()),
        'fired_today': int(scan_results['squeeze_fire'].sum()),
        'bullish_momentum': int(scan_results[scan_results['momentum'] > 0]['squeeze_on'].sum()),
        'bearish_momentum': int(scan_results[scan_results['momentum'] < 0]['squeeze_on'].sum())
    }
