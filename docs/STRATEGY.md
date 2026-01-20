# TTM Squeeze Strategy Documentation

## Overview

The TTM Squeeze is a volatility-based trading strategy that identifies periods of low volatility (consolidation) that often precede significant price moves. This scanner implements the strategy with an additional 200 DMA validation filter to improve signal quality.

## The Science Behind It

Markets alternate between periods of low and high volatility. When volatility contracts (squeeze), it's like a coiled spring - energy builds up and eventually releases in the form of a strong directional move. The TTM Squeeze captures this phenomenon by:

1. Identifying when Bollinger Bands contract inside Keltner Channels
2. Using momentum to predict breakout direction
3. Validating signals with the 200-day trend

## Indicator Parameters

### Bollinger Bands
- **Period**: 20 (SMA)
- **Standard Deviation**: 2.0
- **Purpose**: Measure price volatility relative to recent average

```
Middle Band = 20-period SMA of Close
Upper Band = Middle Band + (2.0 × 20-period Std Dev)
Lower Band = Middle Band - (2.0 × 20-period Std Dev)
BB Width = ((Upper - Lower) / Middle) × 100
```

### Keltner Channels
- **EMA Period**: 20
- **ATR Period**: 20
- **ATR Multiplier**: 1.5
- **Purpose**: Provide a more stable volatility envelope

```
Middle Line = 20-period EMA of Close
True Range = MAX(High-Low, ABS(High-PrevClose), ABS(Low-PrevClose))
ATR = 20-period EMA of True Range
Upper Channel = Middle Line + (1.5 × ATR)
Lower Channel = Middle Line - (1.5 × ATR)
```

### Squeeze Momentum
- **Length**: 12 periods
- **Method**: Linear Regression
- **Purpose**: Determine breakout direction and strength

```
Momentum Source = Close - KC Midline
Squeeze Momentum = Linear Regression Value of Momentum Source (12 periods)
```

### 200-Day Moving Average
- **Period**: 200 (SMA)
- **Purpose**: Identify long-term trend for signal validation

```
200 DMA = 200-period SMA of Close
```

## Squeeze Detection

### Squeeze ON (Consolidation)
A squeeze is "ON" when Bollinger Bands are completely inside Keltner Channels:

```
Squeeze ON = (BB_Lower > KC_Lower) AND (BB_Upper < KC_Upper)
```

This indicates:
- Volatility has contracted significantly
- Price is consolidating
- A potential breakout is building

### Squeeze OFF (Normal)
```
Squeeze OFF = NOT Squeeze ON
```

### Squeeze FIRED (Breakout)
A squeeze "fires" when it transitions from ON to OFF:

```
Squeeze FIRED = Previous bar Squeeze ON AND Current bar Squeeze OFF
```

This is the primary signal - volatility is expanding and a directional move is beginning.

## Entry Rules

### Bullish Entry (Long)
All conditions must be met:

1. **Squeeze just fired** (transition from ON to OFF)
2. **Positive momentum** (Squeeze Momentum > 0)
3. **Price above upper BB** (Close > BB Upper) - confirms strength
4. **Price above 200 DMA** (Close > 200 DMA) - trend validation

```python
BULLISH_BREAKOUT = (
    Squeeze_Fire == True AND
    Momentum > 0 AND
    Close > BB_Upper AND
    Close > DMA_200
)
```

### Bearish Entry (Short)
All conditions must be met:

1. **Squeeze just fired** (transition from ON to OFF)
2. **Negative momentum** (Squeeze Momentum < 0)
3. **Price below lower BB** (Close < BB Lower) - confirms weakness
4. **Price below 200 DMA** (Close < 200 DMA) - trend validation

```python
BEARISH_BREAKOUT = (
    Squeeze_Fire == True AND
    Momentum < 0 AND
    Close < BB_Lower AND
    Close < DMA_200
)
```

## Why 200 DMA Validation?

Adding the 200 DMA filter significantly improves signal quality:

### Benefits
1. **Filters Counter-Trend Signals**: Bullish signals below 200 DMA often fail
2. **Higher Probability Trades**: Trading with the trend increases success rate
3. **Reduces False Breakouts**: Many squeezes fire but don't follow through
4. **Aligns with Institutional Flow**: Large players often use 200 DMA

### Invalid Signals
- **Bullish below 200 DMA**: The long-term trend is bearish; bullish breakouts often fail
- **Bearish above 200 DMA**: The long-term trend is bullish; bearish breakouts often fail

These are marked as "Invalid" in the scanner - they can still be traded but carry higher risk.

## Momentum Direction States

The scanner tracks four momentum states:

| State | Condition | Interpretation |
|-------|-----------|----------------|
| BULLISH_UP | Momentum > 0 AND increasing | Strongest buy signal |
| BULLISH_DOWN | Momentum > 0 AND decreasing | Weakening buy |
| BEARISH_DOWN | Momentum < 0 AND decreasing | Strongest sell signal |
| BEARISH_UP | Momentum < 0 AND increasing | Weakening sell |

## BB Width Interpretation

Bollinger Band Width indicates squeeze intensity:

| BB Width | Interpretation |
|----------|----------------|
| < 5% | Very tight squeeze - high potential |
| 5-10% | Moderate squeeze |
| > 10% | Wide bands - no squeeze |

**Key Insight**: Tighter squeezes (lower BB Width) often produce larger breakout moves.

## Exit Rules (Suggested)

The scanner focuses on entry signals. Here are common exit approaches:

### Take Profit
- Target 1: 1.5x ATR from entry
- Target 2: Previous swing high/low
- Target 3: Trail with 20 EMA

### Stop Loss
- Below/above the squeeze's low/high
- 1-2 ATR from entry
- Below/above the 200 DMA

### Time-Based
- Exit if no significant move within 5-10 bars
- Exit on squeeze re-entry (new squeeze forms)

## Post-Breakout Analysis

The scanner tracks historical breakout performance:

- **5-Day Move**: Short-term reaction
- **10-Day Move**: Medium-term follow-through
- **20-Day Move**: Trend development

Use this data to understand how well squeezes work for specific stocks.

## Best Practices

1. **Use 5-Year Data**: Ensures accurate 200 DMA calculation
2. **Focus on Valid Signals**: Filter for 200 DMA validated breakouts
3. **Check BB Width**: Prioritize tighter squeezes (< 5%)
4. **Confirm with Volume**: Higher volume on breakout day is better
5. **Wait for Close**: Don't enter until the day closes above/below BB
6. **Manage Risk**: Never risk more than 1-2% per trade

## Limitations

- **Lagging Indicator**: Squeeze fires after the fact
- **False Breakouts**: Not all squeezes lead to significant moves
- **Requires Context**: Works better in trending markets
- **Not for Scalping**: Designed for swing trading (days to weeks)

## References

- John Carter - Original TTM Squeeze concept
- Bollinger, John - Bollinger on Bollinger Bands
- Keltner, Chester - Original Keltner Channel concept
