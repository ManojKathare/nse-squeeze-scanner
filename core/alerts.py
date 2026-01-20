"""Alerts module for price and squeeze alerts"""

from typing import Dict, List, Optional
from datetime import datetime


def check_price_alerts(alerts: List[Dict], current_prices: Dict[str, float]) -> List[Dict]:
    """
    Check if any price alerts are triggered.

    Args:
        alerts: List of alert dictionaries with symbol, alert_type, threshold
        current_prices: Dictionary mapping symbol to current price

    Returns:
        List of triggered alerts
    """
    triggered = []

    for alert in alerts:
        if not alert.get('is_active', True):
            continue

        symbol = alert['symbol']
        if symbol not in current_prices:
            continue

        current_price = current_prices[symbol]
        threshold = alert['threshold']
        alert_type = alert['alert_type']

        is_triggered = False

        if alert_type == 'PRICE_ABOVE' and current_price >= threshold:
            is_triggered = True
        elif alert_type == 'PRICE_BELOW' and current_price <= threshold:
            is_triggered = True

        if is_triggered:
            triggered.append({
                **alert,
                'current_price': current_price,
                'triggered_at': datetime.now().isoformat()
            })

    return triggered


def check_squeeze_alerts(alerts: List[Dict], scan_results: Dict[str, Dict]) -> List[Dict]:
    """
    Check if any squeeze fire alerts are triggered.

    Args:
        alerts: List of alert dictionaries
        scan_results: Dictionary mapping symbol to scan result

    Returns:
        List of triggered alerts
    """
    triggered = []

    for alert in alerts:
        if not alert.get('is_active', True):
            continue

        if alert.get('alert_type') != 'SQUEEZE_FIRE':
            continue

        symbol = alert['symbol']
        if symbol not in scan_results:
            continue

        result = scan_results[symbol]

        if result.get('squeeze_fire', False):
            triggered.append({
                **alert,
                'direction': result.get('momentum_direction', 'UNKNOWN'),
                'triggered_at': datetime.now().isoformat()
            })

    return triggered


def create_alert(symbol: str, alert_type: str, threshold: float = 0.0,
                 company_name: str = '') -> Dict:
    """
    Create a new alert configuration.

    Args:
        symbol: Stock symbol
        alert_type: One of 'PRICE_ABOVE', 'PRICE_BELOW', 'SQUEEZE_FIRE'
        threshold: Price threshold (for price alerts)
        company_name: Company name

    Returns:
        Alert dictionary
    """
    return {
        'symbol': symbol,
        'company_name': company_name,
        'alert_type': alert_type,
        'threshold': threshold,
        'is_active': True,
        'created_at': datetime.now().isoformat(),
        'triggered_at': None
    }
