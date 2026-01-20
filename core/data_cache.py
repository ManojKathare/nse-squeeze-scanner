"""Data caching module - Store fetched stock data locally"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import pickle

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')

# Cache expiry times (in hours)
CACHE_EXPIRY = {
    '6mo': 24,      # 1 day
    '1y': 24,       # 1 day
    '2y': 48,       # 2 days
    '5y': 168,      # 7 days
    'max': 168      # 7 days
}


def ensure_cache_dir():
    """Ensure cache directory exists"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_path(symbol: str, period: str) -> str:
    """Get cache file path for a symbol and period"""
    ensure_cache_dir()
    safe_symbol = symbol.replace('.', '_').replace('&', '_')
    return os.path.join(CACHE_DIR, f"{safe_symbol}_{period}.pkl")


def get_cache_meta_path() -> str:
    """Get cache metadata file path"""
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, "cache_meta.json")


def load_cache_meta() -> Dict:
    """Load cache metadata"""
    meta_path = get_cache_meta_path()
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache_meta(meta: Dict):
    """Save cache metadata"""
    meta_path = get_cache_meta_path()
    with open(meta_path, 'w') as f:
        json.dump(meta, f)


def is_cache_valid(symbol: str, period: str) -> bool:
    """Check if cache is still valid"""
    meta = load_cache_meta()
    cache_key = f"{symbol}_{period}"

    if cache_key not in meta:
        return False

    cached_time = datetime.fromisoformat(meta[cache_key]['timestamp'])
    expiry_hours = CACHE_EXPIRY.get(period, 24)

    return datetime.now() - cached_time < timedelta(hours=expiry_hours)


def get_cached_data(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """Get cached data for a symbol"""
    if not is_cache_valid(symbol, period):
        return None

    cache_path = get_cache_path(symbol, period)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading cache for {symbol}: {e}")
        return None


def save_to_cache(symbol: str, period: str, df: pd.DataFrame):
    """Save data to cache"""
    if df is None or df.empty:
        return

    cache_path = get_cache_path(symbol, period)

    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)

        # Update metadata
        meta = load_cache_meta()
        cache_key = f"{symbol}_{period}"
        meta[cache_key] = {
            'timestamp': datetime.now().isoformat(),
            'rows': len(df)
        }
        save_cache_meta(meta)
    except Exception as e:
        print(f"Error saving cache for {symbol}: {e}")


def clear_cache(symbol: str = None, period: str = None):
    """Clear cache - all or specific"""
    ensure_cache_dir()

    if symbol and period:
        # Clear specific cache
        cache_path = get_cache_path(symbol, period)
        if os.path.exists(cache_path):
            os.remove(cache_path)

        meta = load_cache_meta()
        cache_key = f"{symbol}_{period}"
        if cache_key in meta:
            del meta[cache_key]
            save_cache_meta(meta)
    else:
        # Clear all cache
        for file in os.listdir(CACHE_DIR):
            file_path = os.path.join(CACHE_DIR, file)
            try:
                os.remove(file_path)
            except:
                pass


def get_cache_stats() -> Dict:
    """Get cache statistics"""
    ensure_cache_dir()
    meta = load_cache_meta()

    total_files = len([f for f in os.listdir(CACHE_DIR) if f.endswith('.pkl')])
    total_size = sum(
        os.path.getsize(os.path.join(CACHE_DIR, f))
        for f in os.listdir(CACHE_DIR)
        if os.path.isfile(os.path.join(CACHE_DIR, f))
    )

    return {
        'total_cached': total_files,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'entries': len(meta)
    }
