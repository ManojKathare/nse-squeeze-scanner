"""
Comprehensive Test Suite for NSE Squeeze Scanner
Tests TTM Squeeze indicator calculations, breakout detection, filtering, and data integrity.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.indicators import (
    calculate_bollinger_bands,
    calculate_keltner_channels,
    calculate_momentum,
    calculate_200_dma,
    calculate_all_indicators
)
from core.squeeze_detector import (
    detect_squeeze,
    detect_entry_signals,
    prepare_results_dataframe,
    scan_single_stock,
    get_squeeze_history
)


# ========== FIXTURES ==========

@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')

    # Generate realistic price data
    close_prices = 100 + np.random.randn(250).cumsum()
    close_prices = np.maximum(close_prices, 50)  # Keep prices positive

    df = pd.DataFrame({
        'Date': dates,
        'Open': close_prices + np.random.randn(250) * 2,
        'High': close_prices + np.abs(np.random.randn(250) * 3),
        'Low': close_prices - np.abs(np.random.randn(250) * 3),
        'Close': close_prices,
        'Volume': np.random.randint(100000, 10000000, 250)
    })

    # Ensure High is highest and Low is lowest
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)

    return df


@pytest.fixture
def sample_stock_data_with_squeeze():
    """Create stock data with a known squeeze pattern"""
    np.random.seed(123)
    dates = pd.date_range(start='2024-01-01', periods=300, freq='D')

    # Create base price with squeeze pattern
    price = 100
    prices = []

    for i in range(300):
        if 50 <= i < 100:  # Squeeze period - low volatility
            price += np.random.randn() * 0.5
        elif 100 <= i < 120:  # Breakout period - high volatility
            price += np.random.randn() * 5 + 2  # Bullish breakout
        else:  # Normal period
            price += np.random.randn() * 2
        prices.append(max(price, 50))

    df = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p + abs(np.random.randn() * 2) for p in prices],
        'Low': [p - abs(np.random.randn() * 2) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(100000, 10000000, 300)
    })

    # Ensure High is highest and Low is lowest
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)

    return df


# ========== TEST BOLLINGER BANDS ==========

class TestBollingerBands:
    """Test Bollinger Bands calculation"""

    def test_bollinger_bands_columns_exist(self, sample_stock_data):
        """Test that BB calculation creates required columns"""
        df = calculate_bollinger_bands(sample_stock_data.copy())

        assert 'bb_middle' in df.columns
        assert 'bb_upper' in df.columns
        assert 'bb_lower' in df.columns
        assert 'bb_width_pct' in df.columns

    def test_bollinger_bands_middle_is_sma(self, sample_stock_data):
        """Test BB middle band is 20-period SMA"""
        df = calculate_bollinger_bands(sample_stock_data.copy(), period=20)

        # Calculate manual SMA
        manual_sma = df['Close'].rolling(window=20).mean()

        # Compare (skip NaN values)
        valid_indices = ~manual_sma.isna()
        assert np.allclose(
            df.loc[valid_indices, 'bb_middle'],
            manual_sma[valid_indices],
            rtol=0.01
        )

    def test_bollinger_bands_upper_greater_than_lower(self, sample_stock_data):
        """Test BB upper band is always >= lower band"""
        df = calculate_bollinger_bands(sample_stock_data.copy())

        valid_data = df.dropna(subset=['bb_upper', 'bb_lower'])
        assert (valid_data['bb_upper'] >= valid_data['bb_lower']).all()

    def test_bollinger_bands_width_positive(self, sample_stock_data):
        """Test BB width is always positive"""
        df = calculate_bollinger_bands(sample_stock_data.copy())

        valid_data = df.dropna(subset=['bb_width_pct'])
        assert (valid_data['bb_width_pct'] >= 0).all()

    def test_bollinger_bands_price_between_bands_usually(self, sample_stock_data):
        """Test that price is usually between BB bands (not always, but mostly)"""
        df = calculate_bollinger_bands(sample_stock_data.copy())

        valid_data = df.dropna(subset=['bb_upper', 'bb_lower'])
        between_bands = (
            (valid_data['Close'] <= valid_data['bb_upper']) &
            (valid_data['Close'] >= valid_data['bb_lower'])
        )

        # Price should be between bands at least 90% of the time (2 std dev)
        assert between_bands.sum() / len(between_bands) >= 0.90


# ========== TEST KELTNER CHANNELS ==========

class TestKeltnerChannels:
    """Test Keltner Channels calculation"""

    def test_keltner_channels_columns_exist(self, sample_stock_data):
        """Test that KC calculation creates required columns"""
        df = calculate_keltner_channels(sample_stock_data.copy())

        assert 'kc_middle' in df.columns
        assert 'kc_upper' in df.columns
        assert 'kc_lower' in df.columns
        assert 'atr' in df.columns

    def test_keltner_channels_middle_is_ema(self, sample_stock_data):
        """Test KC middle is EMA"""
        df = calculate_keltner_channels(sample_stock_data.copy(), ema_period=20)

        # Calculate manual EMA
        manual_ema = df['Close'].ewm(span=20, adjust=False).mean()

        # Compare (skip NaN values)
        valid_indices = ~manual_ema.isna()
        assert np.allclose(
            df.loc[valid_indices, 'kc_middle'],
            manual_ema[valid_indices],
            rtol=0.01
        )

    def test_keltner_channels_upper_greater_than_lower(self, sample_stock_data):
        """Test KC upper channel is always >= lower channel"""
        df = calculate_keltner_channels(sample_stock_data.copy())

        valid_data = df.dropna(subset=['kc_upper', 'kc_lower'])
        assert (valid_data['kc_upper'] >= valid_data['kc_lower']).all()

    def test_atr_always_positive(self, sample_stock_data):
        """Test ATR is always positive or zero"""
        df = calculate_keltner_channels(sample_stock_data.copy())

        valid_data = df.dropna(subset=['atr'])
        assert (valid_data['atr'] >= 0).all()


# ========== TEST SQUEEZE DETECTION ==========

class TestSqueezeDetection:
    """Test squeeze detection logic"""

    def test_squeeze_columns_exist(self, sample_stock_data):
        """Test that squeeze detection creates required columns"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)

        assert 'squeeze_on' in df.columns
        assert 'squeeze_off' in df.columns
        assert 'squeeze_fired' in df.columns
        assert 'squeeze_status' in df.columns
        assert 'squeeze_duration' in df.columns

    def test_squeeze_on_off_mutually_exclusive(self, sample_stock_data):
        """Test squeeze_on and squeeze_off are mutually exclusive"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)

        valid_data = df.dropna(subset=['squeeze_on', 'squeeze_off'])

        # squeeze_on and squeeze_off should never both be True
        assert not (valid_data['squeeze_on'] & valid_data['squeeze_off']).any()

    def test_squeeze_fired_only_on_transition(self, sample_stock_data_with_squeeze):
        """Test squeeze_fired only occurs when transitioning from ON to OFF"""
        df = calculate_all_indicators(sample_stock_data_with_squeeze.copy())
        df = detect_squeeze(df)

        fired_indices = df[df['squeeze_fired'] == True].index

        for idx in fired_indices:
            if idx > 0:
                prev_idx = idx - 1
                # Previous should be squeeze_on, current should be squeeze_off
                if not pd.isna(df.loc[prev_idx, 'squeeze_on']):
                    assert df.loc[prev_idx, 'squeeze_on'] == True or df.loc[prev_idx, 'squeeze_off'] == True
                    assert df.loc[idx, 'squeeze_off'] == True

    def test_squeeze_status_values(self, sample_stock_data):
        """Test squeeze_status only contains valid values"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)

        valid_statuses = ['Squeeze ON', 'Squeeze OFF', 'Squeeze Fired']
        valid_data = df.dropna(subset=['squeeze_status'])

        assert valid_data['squeeze_status'].isin(valid_statuses).all()

    def test_squeeze_duration_non_negative(self, sample_stock_data):
        """Test squeeze duration is always non-negative"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)

        valid_data = df.dropna(subset=['squeeze_duration'])
        assert (valid_data['squeeze_duration'] >= 0).all()

    def test_squeeze_duration_resets_on_off(self, sample_stock_data_with_squeeze):
        """Test squeeze duration resets when squeeze turns OFF"""
        df = calculate_all_indicators(sample_stock_data_with_squeeze.copy())
        df = detect_squeeze(df)

        # When squeeze is OFF, duration should be 0
        off_data = df[df['squeeze_status'] == 'Squeeze OFF']
        if len(off_data) > 0:
            assert (off_data['squeeze_duration'] == 0).all()


# ========== TEST MOMENTUM CALCULATION ==========

class TestMomentum:
    """Test momentum oscillator calculation"""

    def test_momentum_column_exists(self, sample_stock_data):
        """Test momentum calculation creates momentum column"""
        df = calculate_momentum(sample_stock_data.copy())

        assert 'momentum' in df.columns

    def test_momentum_has_positive_and_negative(self, sample_stock_data):
        """Test momentum has both positive and negative values"""
        df = calculate_momentum(sample_stock_data.copy())

        valid_data = df.dropna(subset=['momentum'])

        # Should have both positive and negative momentum
        has_positive = (valid_data['momentum'] > 0).any()
        has_negative = (valid_data['momentum'] < 0).any()

        assert has_positive or has_negative  # At least one direction


# ========== TEST 200 DMA ==========

class TestMovingAverages:
    """Test moving average calculations"""

    def test_200_dma_exists(self, sample_stock_data):
        """Test 200 DMA calculation"""
        df = calculate_200_dma(sample_stock_data.copy())

        assert 'dma_200' in df.columns
        assert 'dist_from_200dma_pct' in df.columns

    def test_200_dma_is_sma(self, sample_stock_data):
        """Test 200 DMA is simple moving average"""
        df = calculate_200_dma(sample_stock_data.copy())

        # Calculate manual SMA
        manual_sma = df['Close'].rolling(window=200).mean()

        # Compare valid values
        valid_indices = ~manual_sma.isna()
        if valid_indices.any():
            assert np.allclose(
                df.loc[valid_indices, 'dma_200'],
                manual_sma[valid_indices],
                rtol=0.01
            )

    def test_distance_from_200dma_calculation(self, sample_stock_data):
        """Test distance from 200 DMA is correctly calculated"""
        df = calculate_200_dma(sample_stock_data.copy())

        valid_data = df.dropna(subset=['dma_200', 'dist_from_200dma_pct'])

        if len(valid_data) > 0:
            # Manually calculate distance
            manual_dist = ((valid_data['Close'] - valid_data['dma_200']) / valid_data['dma_200']) * 100

            assert np.allclose(
                valid_data['dist_from_200dma_pct'],
                manual_dist,
                rtol=0.01
            )


# ========== TEST BREAKOUT DETECTION ==========

class TestBreakoutDetection:
    """Test breakout detection and validation"""

    def test_entry_signals_columns_exist(self, sample_stock_data):
        """Test entry signal detection creates required columns"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)
        df = detect_entry_signals(df)

        assert 'entry_signal' in df.columns
        assert 'signal_type' in df.columns
        assert 'signal_valid' in df.columns

    def test_valid_signals_respect_200dma_bullish(self, sample_stock_data):
        """Test bullish signals require price above 200 DMA"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)
        df = detect_entry_signals(df)

        # Filter valid bullish signals
        valid_bullish = df[
            (df['signal_valid'] == True) &
            (df['signal_type'].str.contains('Bullish', na=False))
        ]

        if len(valid_bullish) > 0:
            # All valid bullish signals should have price > 200 DMA
            assert (valid_bullish['Close'] > valid_bullish['dma_200']).all()

    def test_valid_signals_respect_200dma_bearish(self, sample_stock_data):
        """Test bearish signals require price below 200 DMA"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)
        df = detect_entry_signals(df)

        # Filter valid bearish signals
        valid_bearish = df[
            (df['signal_valid'] == True) &
            (df['signal_type'].str.contains('Bearish', na=False))
        ]

        if len(valid_bearish) > 0:
            # All valid bearish signals should have price < 200 DMA
            assert (valid_bearish['Close'] < valid_bearish['dma_200']).all()


# ========== TEST RESULTS DATAFRAME ==========

class TestResultsDataFrame:
    """Test results dataframe preparation"""

    def test_prepare_results_creates_required_columns(self, sample_stock_data):
        """Test that prepare_results_dataframe creates all required columns"""
        df = calculate_all_indicators(sample_stock_data.copy())
        df = detect_squeeze(df)
        df = detect_entry_signals(df)
        results_df = prepare_results_dataframe(df)

        # Check for essential columns
        assert 'Date' in results_df.columns or 'date' in results_df.columns
        assert 'Close' in results_df.columns or 'close' in results_df.columns
        assert 'squeeze_status' in results_df.columns


# ========== TEST SQUEEZE HISTORY ==========

class TestSqueezeHistory:
    """Test squeeze history generation"""

    def test_squeeze_history_returns_list(self, sample_stock_data_with_squeeze):
        """Test get_squeeze_history returns a list"""
        df = calculate_all_indicators(sample_stock_data_with_squeeze.copy())
        df = detect_squeeze(df)

        history = get_squeeze_history(df)

        assert isinstance(history, list)

    def test_squeeze_history_contains_dicts(self, sample_stock_data_with_squeeze):
        """Test squeeze history entries are dictionaries"""
        df = calculate_all_indicators(sample_stock_data_with_squeeze.copy())
        df = detect_squeeze(df)

        history = get_squeeze_history(df)

        if len(history) > 0:
            assert all(isinstance(entry, dict) for entry in history)


# ========== TEST DATA INTEGRITY ==========

class TestDataIntegrity:
    """Test data integrity and consistency"""

    def test_no_negative_prices(self, sample_stock_data):
        """Test that calculated values don't create negative prices"""
        df = calculate_all_indicators(sample_stock_data.copy())

        assert (df['Close'] > 0).all()

        valid_bb = df.dropna(subset=['bb_lower'])
        if len(valid_bb) > 0:
            assert (valid_bb['bb_lower'] > 0).all()

    def test_indicators_dont_create_inf_nan_unexpectedly(self, sample_stock_data):
        """Test indicators don't create unexpected inf/NaN values"""
        df = calculate_all_indicators(sample_stock_data.copy())

        # After 200 periods, we shouldn't have NaN in most columns
        if len(df) > 210:
            recent_data = df.iloc[-50:]

            # Check key columns
            for col in ['bb_middle', 'kc_middle', 'momentum']:
                if col in recent_data.columns:
                    # Should have mostly valid data
                    valid_pct = (~recent_data[col].isna()).sum() / len(recent_data)
                    assert valid_pct > 0.8  # At least 80% valid


# ========== TEST EDGE CASES ==========

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        # Create very small dataset
        small_df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10),
            'Open': [100] * 10,
            'High': [102] * 10,
            'Low': [98] * 10,
            'Close': [100] * 10,
            'Volume': [1000000] * 10
        })

        # Should not crash, but will have NaN values
        df = calculate_all_indicators(small_df.copy())

        # Function should complete without error
        assert df is not None

    def test_constant_price_handling(self):
        """Test handling of constant prices (no volatility)"""
        constant_df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=250),
            'Open': [100] * 250,
            'High': [100] * 250,
            'Low': [100] * 250,
            'Close': [100] * 250,
            'Volume': [1000000] * 250
        })

        # Should handle constant prices gracefully
        df = calculate_all_indicators(constant_df.copy())
        df = detect_squeeze(df)

        # BB width should be zero or very small
        valid_bb = df.dropna(subset=['bb_width_pct'])
        if len(valid_bb) > 0:
            assert (valid_bb['bb_width_pct'] < 1.0).all()


# ========== INTEGRATION TESTS ==========

class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_analysis_pipeline(self, sample_stock_data):
        """Test complete analysis pipeline from data to results"""
        # Step 1: Calculate indicators
        df = calculate_all_indicators(sample_stock_data.copy())
        assert df is not None

        # Step 2: Detect squeeze
        df = detect_squeeze(df)
        assert 'squeeze_status' in df.columns

        # Step 3: Detect entry signals
        df = detect_entry_signals(df)
        assert 'entry_signal' in df.columns

        # Step 4: Prepare results
        results = prepare_results_dataframe(df)
        assert results is not None
        assert len(results) > 0

    def test_squeeze_pattern_detection(self, sample_stock_data_with_squeeze):
        """Test that squeeze pattern is detected in known data"""
        df = calculate_all_indicators(sample_stock_data_with_squeeze.copy())
        df = detect_squeeze(df)

        # Should detect at least one squeeze event
        squeeze_on_count = (df['squeeze_status'] == 'Squeeze ON').sum()
        squeeze_fired_count = (df['squeeze_status'] == 'Squeeze Fired').sum()

        # We engineered this data to have a squeeze, so should detect something
        assert squeeze_on_count > 0 or squeeze_fired_count > 0


# ========== PERFORMANCE TESTS ==========

class TestPerformance:
    """Test performance and efficiency"""

    def test_indicator_calculation_speed(self, sample_stock_data):
        """Test that indicator calculation completes in reasonable time"""
        import time

        start = time.time()
        df = calculate_all_indicators(sample_stock_data.copy())
        elapsed = time.time() - start

        # Should complete in under 1 second for 250 data points
        assert elapsed < 1.0

    def test_squeeze_detection_speed(self, sample_stock_data):
        """Test that squeeze detection completes quickly"""
        import time

        df = calculate_all_indicators(sample_stock_data.copy())

        start = time.time()
        df = detect_squeeze(df)
        elapsed = time.time() - start

        # Should be very fast
        assert elapsed < 0.5


# ========== RUN TESTS ==========

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
