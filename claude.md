# NSE Squeeze Scanner - Project Documentation

## Project Overview
NSE stock scanner application that identifies trading opportunities using the TTM Squeeze indicator with Bollinger Bands and Keltner Channels. This tool helps traders identify potential breakout opportunities in Indian stocks listed on the National Stock Exchange (NSE).

## Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.x
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **Data Source**: Yahoo Finance (yfinance), NSE India
- **Database**: SQLite (local storage)
- **Deployment**: Streamlit Cloud, Local

## Project Structure
```
nse_squeeze_scanner/
├── app.py                      # Main application entry point
├── config.py                   # Configuration and constants
├── requirements.txt            # Python dependencies
├── filter_presets.json        # Saved filter configurations
├── .gitignore                 # Git ignore rules
├── README.md                  # User documentation
├── claude.md                  # AI context documentation (this file)
│
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── data_fetcher.py       # Stock data fetching from NSE/Yahoo Finance
│   ├── squeeze_detector.py   # TTM Squeeze algorithm implementation
│   ├── indicators.py         # Technical indicator calculations
│   ├── alerts.py             # Alert management system
│   └── data_cache.py         # Data caching mechanism
│
├── database/                  # Database operations
│   ├── __init__.py
│   └── db_manager.py         # SQLite database management
│
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── charts.py         # Chart generation (Plotly)
│   │   └── tables.py         # Table formatting
│   └── pages/
│       ├── __init__.py
│       ├── scanner.py        # Main scanner page
│       ├── stock_detail.py   # Individual stock analysis
│       ├── watchlist.py      # Watchlist management
│       └── alerts.py         # Alert configuration
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── export.py             # Data export (CSV, Excel)
│
└── tests/                     # Test suite
    ├── __init__.py
    └── test_app.py           # Application tests
```

## Core Features

### 1. Stock Scanning
- **Multi-index selection**:
  - Broad Market: Nifty 50, Nifty Next 50, Nifty Midcap 150, Nifty Smallcap 250, Nifty Microcap 250
  - Sectoral: Bank, IT, Pharma, Auto, FMCG, Metal, Realty, PSU Bank, Private Bank, Media, Energy
  - Thematic: Commodities, Consumption, Digital, Infrastructure, Manufacturing, Services, MNC
- Real-time data fetching from Yahoo Finance
- Intelligent caching to avoid redundant API calls
- Last scan timestamp tracking
- Session state management for persistent data

### 2. TTM Squeeze Algorithm

**Core Indicators:**
- **Bollinger Bands (BB)**: 20-period SMA with 2.0 standard deviations
- **Keltner Channels (KC)**: 20-period EMA with 1.5 ATR multiplier
- **Momentum Oscillator**: 12-period linear regression
- **Moving Averages**: 200 DMA and 50 DMA for trend validation

**Squeeze Detection Logic:**
- **Squeeze ON**: BB inside KC (both upper and lower bands)
  - Condition: `(bb_upper < kc_upper) AND (bb_lower > kc_lower)`
  - Indicates low volatility and potential energy buildup
- **Squeeze OFF**: BB outside KC
  - Condition: NOT squeeze_on
  - Normal volatility state
- **Squeeze FIRED**: Transition from ON to OFF
  - Condition: `squeeze_on[previous] AND squeeze_off[current]`
  - Signals potential breakout

**Breakout Classification:**
- **Bullish Breakout**:
  - Squeeze fires (ON → OFF transition)
  - Positive momentum
  - Price breaks above upper BB
  - Price above 200 DMA (trend validation)
- **Bearish Breakout**:
  - Squeeze fires (ON → OFF transition)
  - Negative momentum
  - Price breaks below lower BB
  - Price below 200 DMA (trend validation)

**Momentum States:**
- BULLISH_UP: Price above 200 DMA, momentum increasing (green)
- BULLISH_DOWN: Price above 200 DMA, momentum decreasing (lime)
- BEARISH_UP: Price below 200 DMA, momentum increasing (red)
- BEARISH_DOWN: Price below 200 DMA, momentum decreasing (maroon)

### 3. Advanced Filtering System

**Available Filters:**
1. **Valid Signals Only**: Only show stocks meeting 200 DMA validation rules
2. **Breakout Type**: Filter by Bullish/Bearish/Both
3. **Squeeze Status**: Filter by ON/OFF/FIRED states
4. **Minimum Squeeze Duration**: Require squeeze to be ON for X days minimum
5. **BB Width Range**: Filter by Bollinger Band width percentage (volatility)
6. **Momentum Direction**: Filter by momentum state (BULLISH_UP/DOWN, BEARISH_UP/DOWN)
7. **Distance from 200 DMA**:
   - Above 200 DMA: Filter stocks X% above their 200 DMA
   - Below 200 DMA: Filter stocks X% below their 200 DMA
8. **Watchlist Only**: Show only stocks in user's watchlist
9. **Low Float**: Filter for low float stocks (when available)

### 4. Filter Presets
- Save current filter configuration with custom name
- Load previously saved presets instantly
- Delete unwanted presets
- Presets stored in `filter_presets.json`
- Safe preset application using pending state mechanism

### 5. Interactive Visualizations
- **Price Chart**: Candlestick chart with volume
- **Bollinger Bands Overlay**: Upper, middle (SMA), and lower bands
- **Keltner Channels Overlay**: Upper, middle (EMA), and lower channels
- **Moving Averages**: 200 DMA and 50 DMA lines
- **Squeeze Indicators**: Visual markers for squeeze ON/OFF/FIRED states
- **Breakout Markers**:
  - Bullish: Green triangle pointing up
  - Bearish: Red triangle pointing down
- **Momentum Oscillator**: Histogram showing momentum direction and strength
- **Volume Analysis**: Volume bars with color coding

### 6. Stock Details Page
- Individual stock analysis with full history
- Detailed chart with all indicators
- Breakout history table
- Current squeeze status and statistics
- Historical performance metrics
- Navigation from results table

### 7. Watchlist Management
- Add/remove stocks from watchlist
- Persistent watchlist storage in database
- Quick access to favorite stocks
- Filter scan results by watchlist

### 8. Alert System
- Set price alerts for specific stocks
- Squeeze state change alerts
- Breakout notifications
- Configurable alert thresholds

## Key Algorithms

### Bollinger Bands Calculation
```python
# Middle band: 20-period Simple Moving Average
bb_middle = close.rolling(window=20, min_periods=20).mean()

# Standard deviation
bb_std = close.rolling(window=20, min_periods=20).std()

# Upper and lower bands
bb_upper = bb_middle + (2.0 * bb_std)
bb_lower = bb_middle - (2.0 * bb_std)

# BB width as percentage of middle band
bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
```

### Keltner Channels Calculation
```python
# Middle line: 20-period Exponential Moving Average
kc_middle = close.ewm(span=20, adjust=False).mean()

# True Range calculation
high_low = high - low
high_close = np.abs(high - close.shift())
low_close = np.abs(low - close.shift())
true_range = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)

# Average True Range (ATR): 20-period EMA of True Range
atr = true_range.ewm(span=20, adjust=False).mean()

# Upper and lower bands
kc_upper = kc_middle + (1.5 * atr)
kc_lower = kc_middle - (1.5 * atr)
```

### Squeeze Detection
```python
# Squeeze ON when BB is completely inside KC
squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)

# Squeeze OFF when BB is outside KC
squeeze_off = ~squeeze_on

# Squeeze FIRED when transitioning from ON to OFF
squeeze_fired = squeeze_on.shift(1) & squeeze_off

# Calculate squeeze duration
squeeze_duration = 0
for i in range(len(squeeze_on)):
    if squeeze_on[i]:
        squeeze_duration += 1
    else:
        squeeze_duration = 0
```

### Momentum Oscillator
```python
# Linear regression of price over 12 periods
def calculate_momentum(close, period=12):
    momentum = []
    for i in range(len(close)):
        if i < period:
            momentum.append(0)
        else:
            # Fit linear regression
            y = close[i-period:i].values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            # Momentum is the slope
            momentum.append(slope)
    return pd.Series(momentum, index=close.index)
```

### Moving Averages
```python
# 200-day Simple Moving Average (long-term trend)
dma_200 = close.rolling(window=200, min_periods=200).mean()

# 50-day Simple Moving Average (intermediate trend)
dma_50 = close.rolling(window=50, min_periods=50).mean()

# Distance from 200 DMA as percentage
dist_from_200dma = ((close - dma_200) / dma_200) * 100
```

## Data Flow

1. **User Configuration**:
   - Select indices to scan
   - Configure filters
   - Set analysis period

2. **Data Fetching**:
   - Fetch stock symbols for selected indices
   - Check cache for existing data
   - Fetch missing/updated data from Yahoo Finance
   - Store in session state and cache

3. **Analysis**:
   - Calculate technical indicators (BB, KC, ATR, DMA)
   - Detect squeeze states
   - Calculate momentum
   - Identify breakouts

4. **Filtering**:
   - Apply user-defined filters
   - Validate signals against 200 DMA
   - Sort and rank results

5. **Display**:
   - Show results in interactive table
   - Generate charts on demand
   - Export options (CSV, Excel)

6. **Detail View**:
   - Navigate to individual stock analysis
   - Show historical squeeze patterns
   - Display breakout history

## Database Schema

### Tables

**watchlist**
```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**alerts**
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    threshold REAL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
)
```

**scan_history**
```sql
CREATE TABLE scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indices_scanned TEXT,
    stocks_found INTEGER,
    filters_applied TEXT
)
```

## Configuration (config.py)

### Index Constants
```python
INDEX_NIFTY_50 = "NIFTY 50"
INDEX_NIFTY_NEXT_50 = "NIFTY NEXT 50"
INDEX_NIFTY_MIDCAP_150 = "NIFTY MIDCAP 150"
INDEX_NIFTY_SMALLCAP_250 = "NIFTY SMALLCAP 250"
INDEX_NIFTY_MICROCAP_250 = "NIFTY MICROCAP 250"

BROAD_MARKET_INDICES = [...]
SECTORAL_INDICES = [...]
THEMATIC_INDICES = [...]
```

### Display Names and Stock Counts
```python
INDEX_DISPLAY_NAMES = {
    "NIFTY 50": "Nifty 50",
    "NIFTY NEXT 50": "Nifty Next 50",
    # ...
}

INDEX_STOCK_COUNTS = {
    "NIFTY 50": 50,
    "NIFTY NEXT 50": 50,
    # ...
}
```

## Session State Management

### Key Session State Variables
```python
st.session_state.scan_results        # DataFrame of scan results
st.session_state.selected_indices    # List of indices being scanned
st.session_state.last_scan_time     # Timestamp of last scan
st.session_state.filter_*           # Various filter states
st.session_state.watchlist          # User's watchlist
st.session_state.pending_preset     # Preset to be applied
st.session_state.current_stock      # Currently viewing stock detail
```

## Known Issues and Fixes

### Fixed Issues
1. ✅ Text visibility problems - Enhanced CSS for high contrast
2. ✅ Session state errors with filter presets - Implemented pending preset mechanism
3. ✅ Stock details navigation with filter persistence - Safe state management
4. ✅ Pandas FutureWarnings - Updated to use infer_objects() and where()

### Current Limitations
- API rate limiting from Yahoo Finance for large scans
- Historical data limited by Yahoo Finance availability
- No real-time streaming data (data refreshed on demand)
- Export limited to CSV and Excel formats

## Recent Updates

### 2026-01-28
- Enhanced CSS for better text visibility and contrast
- Created comprehensive project documentation (claude.md)
- Added comprehensive test suite with pytest
- Planned: Post-breakout analysis page with CSV export

### Previous Updates
- Fixed pandas FutureWarning issues
- Added live demo link to README
- Deployed to Render with production settings
- Improved squeeze detection algorithm accuracy

## Future Enhancements

### Planned Features
1. **Backtesting Engine**: Test squeeze strategy on historical data
2. **Alert System Enhancement**: Email/SMS notifications
3. **Portfolio Tracking**: Track performance of selected stocks
4. **Performance Analytics**: Win rate, average gain/loss, etc.
5. **Mobile Responsive Design**: Improved mobile experience
6. **Real-time Data**: WebSocket integration for live updates
7. **Advanced Charting**: More technical indicators and drawing tools
8. **Social Features**: Share watchlists and analysis
9. **API Access**: Programmatic access to scan results

### Technical Improvements
- Implement async data fetching for better performance
- Add Redis caching for production deployment
- Implement comprehensive logging system
- Add unit tests for all core functions
- Set up CI/CD pipeline
- Add performance monitoring

## Dependencies

See `requirements.txt` for complete list:

### Core
- streamlit >= 1.30.0
- pandas >= 2.0.0
- numpy >= 1.24.0

### Data
- yfinance >= 0.2.33
- requests >= 2.31.0

### Visualization
- plotly >= 5.18.0
- kaleido >= 0.2.1

### Analysis
- scipy >= 1.11.0

### Export
- openpyxl >= 3.1.2

### Testing
- pytest >= 7.4.3
- pytest-cov >= 4.1.0

## Development Setup

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd nse-squeeze-scanner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test class
pytest tests/test_app.py::TestTTMSqueezeIndicators -v

# Watch mode (requires pytest-watch)
pytest-watch tests/
```

## API Usage

### Data Fetching
```python
from core.data_fetcher import fetch_stock_data, get_nifty50_symbols

# Get stock symbols
symbols = get_nifty50_symbols()

# Fetch data for a symbol
data = fetch_stock_data("RELIANCE.NS", period="6mo")
```

### Squeeze Detection
```python
from core.squeeze_detector import detect_squeeze, scan_single_stock

# Detect squeeze for a stock
result = scan_single_stock("TCS.NS", period="6mo")

# Access squeeze information
if result['squeeze_status'] == 'Squeeze Fired':
    print(f"Breakout detected: {result['breakout_type']}")
```

### Indicator Calculation
```python
from core.indicators import (
    calculate_bollinger_bands,
    calculate_keltner_channels,
    calculate_momentum
)

# Calculate indicators
bb = calculate_bollinger_bands(data['Close'])
kc = calculate_keltner_channels(data['High'], data['Low'], data['Close'])
momentum = calculate_momentum(data['Close'])
```

## Performance Considerations

### Caching Strategy
- Data cached in session state for duration of session
- Intelligent cache invalidation based on market hours
- Avoid redundant API calls for same stock/period

### Optimization Tips
- Scan smaller index groups for faster results
- Use appropriate historical period (6mo recommended)
- Apply filters to reduce result set size
- Close unused browser tabs to free memory

## Security Notes

- No user authentication required (public tool)
- No sensitive data stored
- All data fetched from public APIs
- Local SQLite database for personal use only
- No external data transmission except to Yahoo Finance

## Support and Troubleshooting

### Common Issues

**Issue**: Data not loading for certain stocks
**Solution**: Some stocks may not have data on Yahoo Finance. Try alternative symbols or verify symbol format (should end with .NS for NSE)

**Issue**: Slow scanning
**Solution**: Reduce number of indices scanned simultaneously. Yahoo Finance has rate limits.

**Issue**: Charts not displaying
**Solution**: Check internet connection. Plotly requires JavaScript enabled.

**Issue**: Filters not working
**Solution**: Clear browser cache and reload. Check that scan results exist before applying filters.

## Contributing Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all functions
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Commit Messages
- Use descriptive commit messages
- Format: `[Type] Brief description`
- Types: Feature, Fix, Refactor, Docs, Test, Style

### Pull Requests
- Create feature branch from main
- Include tests for new features
- Update documentation
- Ensure all tests pass
- Request review before merging

## Notes for AI Assistants

When working with this codebase:

1. **Preserve Functionality**: Always preserve existing functionality when making changes
2. **Test Thoroughly**: Test changes before committing
3. **Follow Patterns**: Follow existing code patterns and conventions
4. **Update Docs**: Update this file when adding new features
5. **Type Safety**: Use type hints and validate inputs
6. **Error Handling**: Implement proper error handling and user feedback
7. **Performance**: Consider performance impact of changes
8. **Dependencies**: Avoid adding unnecessary dependencies

### Testing Protocol
- Run pytest after every significant change
- Manually test UI changes in browser
- Verify all pages still work correctly
- Check console for warnings/errors
- Test with different filter combinations

### Deployment Checklist
- [ ] All tests passing
- [ ] No console errors
- [ ] Documentation updated
- [ ] Requirements.txt updated
- [ ] Version bumped (if applicable)
- [ ] Commit message descriptive
- [ ] Changes reviewed

---

**Last Updated**: 2026-01-28
**Version**: 2.0
**Maintainer**: Development Team
**Status**: Active Development
