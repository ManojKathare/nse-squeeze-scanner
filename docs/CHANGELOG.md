# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-01-XX

### Added
- **Five Advanced Filters** in results section:
  - Valid Signal Filter (200 DMA validation)
  - Distance from 200 DMA (Above) with range slider
  - Distance from 200 DMA (Below) with range slider
  - Squeeze Status multiselect filter
  - Bollinger Band Width percentage filter
- **Quick Presets** for common filter combinations
- **Validation Metrics Dashboard** showing:
  - Total breakouts detected
  - Valid vs invalid breakout counts
  - Bullish/Bearish breakdown
  - Invalid breakout reasons
- **Entry Signal Detection** with 200 DMA validation (`detect_entry_signals` function)
- **Results DataFrame Preparation** helper function (`prepare_results_dataframe`)
- Complete **GitHub documentation**:
  - README.md with installation and usage instructions
  - STRATEGY.md with detailed strategy documentation
  - CHANGELOG.md (this file)
  - LICENSE (MIT)
  - .gitignore for Python/Streamlit projects

### Changed
- **Keltner Channel ATR Period** updated from 10 to 20 (standard TTM Squeeze)
- Improved filter organization in expandable panel
- Enhanced signal validation logic

### Fixed
- TTM Squeeze algorithm now uses correct 20-period ATR for Keltner Channels

## [1.0.0] - 2024-01-XX

### Added
- Initial release
- **Multi-Index Scanning**:
  - Nifty 50
  - Nifty Next 50
  - Nifty Midcap 150
  - Nifty Smallcap 250
  - Nifty Microcap 250
- **TTM Squeeze Detection**:
  - Bollinger Bands (20 SMA, 2.0 std dev)
  - Keltner Channels (20 EMA, 1.5 ATR)
  - Linear Regression Momentum (12 period)
- **200 DMA Integration**:
  - Automatic calculation for all stocks
  - Visual indicator (Above/Below)
  - Signal validation based on DMA position
- **Interactive Features**:
  - Clickable results table
  - Stock detail pages with charts
  - Watchlist management
  - Price alerts
- **Visualization**:
  - Candlestick charts with Plotly
  - Breakout markers on charts
  - 50 DMA and 200 DMA overlays
  - Squeeze history charts
  - Post-breakout analysis charts
- **Data Management**:
  - SQLite database for caching
  - Smart refresh (only fetch new data)
  - Configurable data periods
- **Export Options**:
  - CSV export
  - Excel export
  - Filtered data export
- **Dark Theme UI**:
  - Custom CSS styling
  - High contrast for readability
  - Mobile-responsive layout

### Technical Details
- Built with Streamlit 1.30+
- Python 3.9+ compatible
- Uses yfinance for data fetching
- SQLite for local storage
- Plotly for interactive charts

---

## Planned Features

### [1.2.0] - Future
- [ ] Real-time scanning with auto-refresh
- [ ] Email/SMS alerts for squeeze fires
- [ ] Portfolio tracking integration
- [ ] Custom indicator parameters
- [ ] Backtesting module
- [ ] Machine learning signal enhancement

### [1.3.0] - Future
- [ ] Multi-timeframe analysis
- [ ] Sector heatmaps
- [ ] Relative strength ranking
- [ ] Options data integration
- [ ] API access for programmatic use
