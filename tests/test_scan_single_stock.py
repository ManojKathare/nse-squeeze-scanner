import pandas as pd

import core.squeeze_detector as squeeze_detector


def _build_base_df(momentum: float, above_dma_200: bool) -> pd.DataFrame:
    rows = 30
    close_values = [100.0 + (i * 0.5) for i in range(rows)]

    return pd.DataFrame(
        {
            "Close": close_values,
            "Squeeze_On": [False] * rows,
            "Squeeze_Off": [True] * rows,
            "Squeeze_Fire": [False] * rows,
            "Squeeze_Duration": [0] * rows,
            "Squeeze_Momentum": [momentum] * rows,
            "Momentum_Direction": ["neutral"] * rows,
            "BB_Width": [2.0] * rows,
            "Volume": [1000] * rows,
            "DMA_200": [95.0] * rows,
            "Above_DMA_200": [above_dma_200] * rows,
            "DMA_200_Distance": [5.0] * rows,
        }
    )


def test_scan_single_stock_neutral_momentum_remains_valid(monkeypatch):
    df = _build_base_df(momentum=0.0, above_dma_200=False)

    monkeypatch.setattr(squeeze_detector, "fetch_stock_data", lambda *_args, **_kwargs: df)
    monkeypatch.setattr(squeeze_detector, "detect_squeeze", lambda input_df: input_df)

    result = squeeze_detector.scan_single_stock("TEST.NS", "Test Co")

    assert result is not None
    assert result["signal_valid"] is True


def test_scan_single_stock_positive_momentum_requires_above_dma(monkeypatch):
    df = _build_base_df(momentum=1.2, above_dma_200=False)

    monkeypatch.setattr(squeeze_detector, "fetch_stock_data", lambda *_args, **_kwargs: df)
    monkeypatch.setattr(squeeze_detector, "detect_squeeze", lambda input_df: input_df)

    result = squeeze_detector.scan_single_stock("TEST.NS", "Test Co")

    assert result is not None
    assert result["signal_valid"] is False


def test_scan_single_stock_negative_momentum_requires_below_dma(monkeypatch):
    df = _build_base_df(momentum=-1.2, above_dma_200=True)

    monkeypatch.setattr(squeeze_detector, "fetch_stock_data", lambda *_args, **_kwargs: df)
    monkeypatch.setattr(squeeze_detector, "detect_squeeze", lambda input_df: input_df)

    result = squeeze_detector.scan_single_stock("TEST.NS", "Test Co")

    assert result is not None
    assert result["signal_valid"] is False
