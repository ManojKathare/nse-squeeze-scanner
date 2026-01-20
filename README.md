# NSE TTM Squeeze Scanner

A comprehensive stock screening application for NSE (National Stock Exchange of India) that implements the TTM Squeeze strategy with 200 DMA validation for higher probability trades.

**🚀 [Live Demo](https://nse-squeeze-scanner.onrender.com/)** - Try it now!

## Features

- **Multi-Index Scanning**: Scan Nifty 50, Next 50, Midcap 150, Smallcap 250, and Microcap 250
- **TTM Squeeze Detection**: Identifies low volatility periods using Bollinger Bands inside Keltner Channels
- **200 DMA Validation**: Validates breakout signals based on price position relative to 200-day Moving Average
- **Five Advanced Filters**:
  - Valid Signal Filter (200 DMA aligned)
  - Distance from 200 DMA (Above/Below)
  - Squeeze Status Filter
  - Bollinger Band Width Filter
  - Quick Presets
- **Interactive Charts**: Candlestick charts with breakout markers and DMA overlays
- **Post-Breakout Analysis**: Historical performance tracking of squeeze breakouts
- **Data Caching**: Intelligent caching for faster subsequent scans
- **Export Options**: Download results as CSV or Excel

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ManojKathare/nse-squeeze-scanner.git
cd nse-squeeze-scanner
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

## Usage

### Basic Workflow

1. **Select Indices**: Choose one or more NSE indices to scan from the sidebar
2. **Set Data Period**: Select historical data period (6 months to 5 years)
3. **Click "Scan Now"**: Start scanning for squeeze patterns
4. **Apply Filters**: Use advanced filters to narrow down results
5. **Analyze Stocks**: Click on any stock for detailed analysis
6. **Export Results**: Download filtered results as CSV/Excel

### Understanding Squeeze Signals

| Status | Meaning |
|--------|---------|
| Squeeze ON (Green) | Bollinger Bands inside Keltner Channels - volatility contracting |
| Squeeze OFF (White) | Normal volatility - no squeeze |
| Squeeze FIRED (Red) | Squeeze just ended - potential breakout signal |

### Signal Validation

The scanner validates breakout signals using the 200 DMA rule:

- **Valid Bullish**: Squeeze fired with positive momentum AND price above 200 DMA
- **Valid Bearish**: Squeeze fired with negative momentum AND price below 200 DMA
- **Invalid**: Breakout signal that doesn't align with the long-term trend

## TTM Squeeze Strategy

The TTM Squeeze identifies periods of low volatility (consolidation) that often precede significant price moves.

### Indicators Used

| Indicator | Parameters |
|-----------|------------|
| Bollinger Bands | 20-period SMA, 2.0 standard deviations |
| Keltner Channels | 20-period EMA, 1.5 ATR (20-period) |
| Momentum | 12-period Linear Regression |
| 200 DMA | 200-period Simple Moving Average |

### Entry Rules

**Bullish Setup**:
1. Squeeze fires (transitions from ON to OFF)
2. Momentum oscillator is positive
3. Price closes above upper Bollinger Band
4. **Price is above 200 DMA** (validation)

**Bearish Setup**:
1. Squeeze fires (transitions from ON to OFF)
2. Momentum oscillator is negative
3. Price closes below lower Bollinger Band
4. **Price is below 200 DMA** (validation)

## Project Structure

```
nse_squeeze_scanner/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration constants
├── requirements.txt       # Python dependencies
├── core/
│   ├── data_fetcher.py    # Stock data fetching
│   ├── indicators.py      # Technical indicators (BB, KC, Momentum)
│   └── squeeze_detector.py # Squeeze detection logic
├── database/
│   └── db_manager.py      # SQLite database management
├── ui/
│   └── components/
│       └── charts.py      # Plotly chart components
├── utils/
│   └── export.py          # CSV/Excel export utilities
└── docs/
    ├── STRATEGY.md        # Detailed strategy documentation
    └── CHANGELOG.md       # Version history
```

## Advanced Filters

### 1. Valid Signal Filter
Shows only breakouts that align with the 200 DMA trend direction.

### 2. Distance from 200 DMA
- **Above DMA**: Filter stocks by percentage above the 200 DMA
- **Below DMA**: Filter stocks by percentage below the 200 DMA

### 3. Squeeze Status Filter
Filter by current squeeze state (ON, OFF, or FIRED).

### 4. BB Width Filter
Filter by Bollinger Band Width percentage. Lower values indicate tighter squeezes with potentially larger breakouts.

### 5. Quick Presets
- **Tight Squeezes Only**: BB Width < 5%
- **Valid Signals Only**: 200 DMA validated signals
- **Breaking Out Now**: Only stocks with fired squeezes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Disclaimer

This application is for **educational and informational purposes only**. It is not intended as financial advice.

- Past performance does not guarantee future results
- Always do your own research before making trading decisions
- The developers are not responsible for any financial losses

**Trade at your own risk.**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- TTM Squeeze indicator concept by John Carter
- Stock data provided by Yahoo Finance via yfinance
- Built with Streamlit, Pandas, and Plotly
