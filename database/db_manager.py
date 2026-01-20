"""Database manager for watchlist and alerts using SQLite"""

import sqlite3
import os
import json
from typing import List, Dict, Optional
from datetime import datetime, date


class DatabaseManager:
    """SQLite database manager for watchlist, alerts, and settings"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'nse_squeeze.db')

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL UNIQUE,
                company_name VARCHAR(200),
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                target_price DECIMAL(10,2),
                stop_loss DECIMAL(10,2)
            )
        ''')

        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                company_name VARCHAR(200),
                alert_type VARCHAR(20) NOT NULL,
                threshold DECIMAL(10,2),
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_date TIMESTAMP
            )
        ''')

        # User settings table (for persisting selected indices, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Historical stock data table (for intelligent caching)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                trade_date DATE NOT NULL,
                open_price DECIMAL(12,4),
                high_price DECIMAL(12,4),
                low_price DECIMAL(12,4),
                close_price DECIMAL(12,4),
                volume BIGINT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, trade_date)
            )
        ''')

        # Scan results cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                scan_date DATE NOT NULL,
                current_price DECIMAL(12,4),
                price_change_pct DECIMAL(8,4),
                squeeze_on BOOLEAN,
                squeeze_off BOOLEAN,
                squeeze_fire BOOLEAN,
                squeeze_duration INTEGER,
                momentum DECIMAL(12,6),
                momentum_direction VARCHAR(20),
                bb_width DECIMAL(8,4),
                volume BIGINT,
                dma_200 DECIMAL(12,4),
                above_dma_200 BOOLEAN,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, scan_date)
            )
        ''')

        # Last scan metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_type VARCHAR(50) NOT NULL,
                indices_scanned TEXT,
                total_stocks INTEGER,
                scan_date DATE NOT NULL,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                period VARCHAR(20)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_data_symbol_date ON stock_data(symbol, trade_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_cache_symbol_date ON scan_cache(symbol, scan_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_metadata_date ON scan_metadata(scan_date)')

        conn.commit()
        conn.close()

    # User Settings operations
    def save_setting(self, key: str, value: any) -> bool:
        """Save a user setting"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            value_json = json.dumps(value)
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (key, value, updated_date)
                VALUES (?, ?, ?)
            ''', (key, value_json, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving setting: {e}")
            return False

    def get_setting(self, key: str, default: any = None) -> any:
        """Get a user setting"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM user_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row['value'])
            return default
        except Exception as e:
            print(f"Error getting setting: {e}")
            return default

    def get_selected_indices(self) -> List[str]:
        """Get saved selected indices"""
        return self.get_setting('selected_indices', ['NIFTY_50'])

    def save_selected_indices(self, indices: List[str]) -> bool:
        """Save selected indices"""
        return self.save_setting('selected_indices', indices)

    # Scan cache operations
    def save_scan_result(self, result: Dict, scan_date: date = None) -> bool:
        """Save a single stock scan result to cache"""
        if scan_date is None:
            scan_date = date.today()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scan_cache
                (symbol, scan_date, current_price, price_change_pct, squeeze_on,
                 squeeze_off, squeeze_fire, squeeze_duration, momentum,
                 momentum_direction, bb_width, volume, dma_200, above_dma_200, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('symbol'),
                scan_date.isoformat(),
                result.get('current_price'),
                result.get('price_change_pct'),
                result.get('squeeze_on'),
                result.get('squeeze_off'),
                result.get('squeeze_fire'),
                result.get('squeeze_duration'),
                result.get('momentum'),
                result.get('momentum_direction'),
                result.get('bb_width'),
                result.get('volume'),
                result.get('dma_200'),
                result.get('above_dma_200'),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving scan result: {e}")
            return False

    def save_scan_results_batch(self, results: List[Dict], scan_date: date = None) -> bool:
        """Save multiple scan results in batch"""
        if scan_date is None:
            scan_date = date.today()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for result in results:
                cursor.execute('''
                    INSERT OR REPLACE INTO scan_cache
                    (symbol, scan_date, current_price, price_change_pct, squeeze_on,
                     squeeze_off, squeeze_fire, squeeze_duration, momentum,
                     momentum_direction, bb_width, volume, dma_200, above_dma_200, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.get('symbol'),
                    scan_date.isoformat(),
                    result.get('current_price'),
                    result.get('price_change_pct'),
                    result.get('squeeze_on'),
                    result.get('squeeze_off'),
                    result.get('squeeze_fire'),
                    result.get('squeeze_duration'),
                    result.get('momentum'),
                    result.get('momentum_direction'),
                    result.get('bb_width'),
                    result.get('volume'),
                    result.get('dma_200'),
                    result.get('above_dma_200'),
                    datetime.now().isoformat()
                ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving scan results batch: {e}")
            return False

    def get_cached_scan_results(self, scan_date: date = None, symbols: List[str] = None) -> List[Dict]:
        """Get cached scan results for a date"""
        if scan_date is None:
            scan_date = date.today()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if symbols:
                placeholders = ','.join(['?' for _ in symbols])
                cursor.execute(f'''
                    SELECT * FROM scan_cache
                    WHERE scan_date = ? AND symbol IN ({placeholders})
                    ORDER BY squeeze_on DESC, squeeze_fire DESC, squeeze_duration DESC
                ''', [scan_date.isoformat()] + symbols)
            else:
                cursor.execute('''
                    SELECT * FROM scan_cache
                    WHERE scan_date = ?
                    ORDER BY squeeze_on DESC, squeeze_fire DESC, squeeze_duration DESC
                ''', (scan_date.isoformat(),))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting cached scan results: {e}")
            return []

    def get_symbols_needing_scan(self, symbols: List[str], scan_date: date = None) -> List[str]:
        """Get list of symbols that don't have cached data for the given date"""
        if scan_date is None:
            scan_date = date.today()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in symbols])
            cursor.execute(f'''
                SELECT symbol FROM scan_cache
                WHERE scan_date = ? AND symbol IN ({placeholders})
            ''', [scan_date.isoformat()] + symbols)
            cached_symbols = set(row['symbol'] for row in cursor.fetchall())
            conn.close()
            return [s for s in symbols if s not in cached_symbols]
        except Exception as e:
            print(f"Error checking symbols needing scan: {e}")
            return symbols

    # Scan metadata operations
    def save_scan_metadata(self, indices: List[str], total_stocks: int,
                          period: str, scan_date: date = None) -> bool:
        """Save scan metadata"""
        if scan_date is None:
            scan_date = date.today()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_metadata
                (scan_type, indices_scanned, total_stocks, scan_date, scan_time, period)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'full_scan',
                json.dumps(indices),
                total_stocks,
                scan_date.isoformat(),
                datetime.now().isoformat(),
                period
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving scan metadata: {e}")
            return False

    def get_last_scan_metadata(self) -> Optional[Dict]:
        """Get the most recent scan metadata"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scan_metadata
                ORDER BY scan_time DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            conn.close()
            if row:
                result = dict(row)
                result['indices_scanned'] = json.loads(result['indices_scanned'])
                return result
            return None
        except Exception as e:
            print(f"Error getting last scan metadata: {e}")
            return None

    def has_scan_for_today(self, symbols: List[str] = None) -> bool:
        """Check if we have scan data for today"""
        today = date.today()
        if symbols:
            cached = self.get_cached_scan_results(today, symbols)
            return len(cached) >= len(symbols) * 0.9  # 90% threshold
        else:
            cached = self.get_cached_scan_results(today)
            return len(cached) > 0

    # Watchlist operations
    def add_to_watchlist(self, symbol: str, company_name: str = '',
                        notes: str = '', target_price: float = None,
                        stop_loss: float = None) -> bool:
        """Add a stock to watchlist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO watchlist
                (symbol, company_name, notes, target_price, stop_loss)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, company_name, notes, target_price, stop_loss))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False

    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove a stock from watchlist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False

    def get_watchlist(self) -> List[Dict]:
        """Get all watchlist items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM watchlist ORDER BY added_date DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_watchlist_item(self, symbol: str, notes: str = None,
                             target_price: float = None,
                             stop_loss: float = None) -> bool:
        """Update watchlist item"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            updates = []
            values = []

            if notes is not None:
                updates.append('notes = ?')
                values.append(notes)
            if target_price is not None:
                updates.append('target_price = ?')
                values.append(target_price)
            if stop_loss is not None:
                updates.append('stop_loss = ?')
                values.append(stop_loss)

            if updates:
                values.append(symbol)
                cursor.execute(f'''
                    UPDATE watchlist SET {', '.join(updates)} WHERE symbol = ?
                ''', values)
                conn.commit()

            conn.close()
            return True
        except Exception as e:
            print(f"Error updating watchlist: {e}")
            return False

    def is_in_watchlist(self, symbol: str) -> bool:
        """Check if symbol is in watchlist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM watchlist WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    # Alert operations
    def create_alert(self, symbol: str, alert_type: str, threshold: float = 0.0,
                    company_name: str = '') -> int:
        """Create a new alert"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (symbol, company_name, alert_type, threshold)
                VALUES (?, ?, ?, ?)
            ''', (symbol, company_name, alert_type, threshold))
            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return alert_id
        except Exception as e:
            print(f"Error creating alert: {e}")
            return -1

    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alerts WHERE is_active = 1 ORDER BY created_date DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_alerts_for_symbol(self, symbol: str) -> List[Dict]:
        """Get all alerts for a symbol"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alerts WHERE symbol = ? ORDER BY created_date DESC', (symbol,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def mark_alert_triggered(self, alert_id: int) -> bool:
        """Mark an alert as triggered"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts SET is_active = 0, triggered_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), alert_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking alert triggered: {e}")
            return False

    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting alert: {e}")
            return False

    def toggle_alert(self, alert_id: int) -> bool:
        """Toggle alert active status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE alerts SET is_active = NOT is_active WHERE id = ?', (alert_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error toggling alert: {e}")
            return False
