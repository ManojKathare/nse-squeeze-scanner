"""Technical indicators module - Bollinger Bands and Keltner Channels"""

import pandas as pd
import numpy as np
from scipy import stats
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BB_PERIOD, BB_STD_DEV, KC_EMA_PERIOD, KC_ATR_PERIOD, KC_ATR_MULTIPLIER, MOMENTUM_LENGTH, DMA_PERIOD


def calculate_bollinger_bands(df: pd.DataFrame, period: int = BB_PERIOD,
                              std_dev: float = BB_STD_DEV) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.

    Args:
        df: DataFrame with 'Close' column
        period: SMA period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)

    Returns:
        DataFrame with BB_Middle, BB_Upper, BB_Lower, BB_Width columns added
    """
    df = df.copy()

    # Middle Band = 20-period SMA
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()

    # Standard Deviation
    rolling_std = df['Close'].rolling(window=period).std()

    # Upper and Lower Bands
    df['BB_Upper'] = df['BB_Middle'] + (std_dev * rolling_std)
    df['BB_Lower'] = df['BB_Middle'] - (std_dev * rolling_std)

    # Band Width (percentage)
    df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100

    return df


def calculate_keltner_channels(df: pd.DataFrame, ema_period: int = KC_EMA_PERIOD,
                               atr_period: int = KC_ATR_PERIOD,
                               atr_multiplier: float = KC_ATR_MULTIPLIER) -> pd.DataFrame:
    """
    Calculate Keltner Channels.

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns
        ema_period: EMA period (default 20)
        atr_period: ATR period (default 10)
        atr_multiplier: ATR multiplier (default 1.5)

    Returns:
        DataFrame with KC_Middle, KC_Upper, KC_Lower, ATR columns added
    """
    df = df.copy()

    # Middle Line = EMA
    df['KC_Middle'] = df['Close'].ewm(span=ema_period, adjust=False).mean()

    # True Range
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.maximum(
            np.abs(df['High'] - df['Close'].shift(1)),
            np.abs(df['Low'] - df['Close'].shift(1))
        )
    )

    # Average True Range
    df['ATR'] = df['TR'].rolling(window=atr_period).mean()

    # Upper and Lower Channels
    df['KC_Upper'] = df['KC_Middle'] + (atr_multiplier * df['ATR'])
    df['KC_Lower'] = df['KC_Middle'] - (atr_multiplier * df['ATR'])

    return df


def calculate_momentum(df: pd.DataFrame, length: int = MOMENTUM_LENGTH) -> pd.DataFrame:
    """
    Calculate Squeeze Momentum using Linear Regression.
    This determines the breakout direction.

    Args:
        df: DataFrame with KC_Upper, KC_Lower, Close columns
        length: Linear regression period

    Returns:
        DataFrame with Squeeze_Momentum and Momentum_Direction columns added
    """
    df = df.copy()

    # Momentum source = Close - KC Midline
    df['Momentum_Source'] = df['Close'] - ((df['KC_Upper'] + df['KC_Lower']) / 2)

    # Linear regression value
    def linreg(series):
        if len(series) < length or series.isna().any():
            return np.nan
        x = np.arange(len(series))
        try:
            slope, intercept, _, _, _ = stats.linregress(x, series.values)
            return intercept + slope * (len(series) - 1)
        except:
            return np.nan

    df['Squeeze_Momentum'] = df['Momentum_Source'].rolling(window=length).apply(linreg, raw=False)

    # Momentum direction with increasing/decreasing
    momentum_prev = df['Squeeze_Momentum'].shift(1)

    conditions = [
        (df['Squeeze_Momentum'] > 0) & (df['Squeeze_Momentum'] > momentum_prev),
        (df['Squeeze_Momentum'] > 0) & (df['Squeeze_Momentum'] <= momentum_prev),
        (df['Squeeze_Momentum'] < 0) & (df['Squeeze_Momentum'] < momentum_prev),
        (df['Squeeze_Momentum'] < 0) & (df['Squeeze_Momentum'] >= momentum_prev),
    ]
    choices = ['BULLISH_UP', 'BULLISH_DOWN', 'BEARISH_DOWN', 'BEARISH_UP']

    df['Momentum_Direction'] = np.select(conditions, choices, default='NEUTRAL')

    return df


def calculate_200_dma(df: pd.DataFrame, period: int = DMA_PERIOD) -> pd.DataFrame:
    """
    Calculate 200-day Moving Average for signal validation.

    Args:
        df: DataFrame with 'Close' column
        period: DMA period (default 200)

    Returns:
        DataFrame with DMA_200 and Above_DMA_200 columns added
    """
    df = df.copy()

    # Calculate 200-day Simple Moving Average
    df['DMA_200'] = df['Close'].rolling(window=period).mean()

    # Determine if price is above or below 200 DMA
    df['Above_DMA_200'] = df['Close'] > df['DMA_200']

    # Calculate distance from 200 DMA (percentage)
    df['DMA_200_Distance'] = ((df['Close'] - df['DMA_200']) / df['DMA_200']) * 100

    return df


def calculate_all_indicators(df: pd.DataFrame, include_dma: bool = True) -> pd.DataFrame:
    """
    Calculate all indicators (BB, KC, Momentum, 200 DMA) on a DataFrame.

    Args:
        df: DataFrame with OHLCV data
        include_dma: Whether to include 200 DMA calculation (requires more data)

    Returns:
        DataFrame with all indicator columns added
    """
    df = calculate_bollinger_bands(df)
    df = calculate_keltner_channels(df)
    df = calculate_momentum(df)
    if include_dma:
        df = calculate_200_dma(df)
    return df
