import json
import os

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Keep DATA_DIR for backwards compatibility, but won't use it
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    'account_equity': 100000,
    'risk_pct': 0.01,
    'max_positions': 6
}

# Database helpers
def _get_db():
    """Get database module (lazy import to avoid circular dependency)"""
    from app import db
    return db


def _json_serialize(obj):
    """Serialize objects for JSON storage."""
    if obj is None:
        return None
    if hasattr(obj, '__dict__'):
        return json.dumps(obj.__dict__)
    return json.dumps(obj) if not isinstance(obj, (str, int, float, bool, list, dict)) else obj


# Scan helpers
def get_latest_scan():
    """Get most recent CANSLIM scan with stocks."""
    from app.db import execute_query

    try:
        # Get the latest scan
        scans = execute_query(
            "SELECT * FROM scans ORDER BY created_at DESC LIMIT 1"
        )

        if not scans:
            return None

        scan = dict(scans[0])

        # Get stocks for this scan
        stocks = execute_query(
            "SELECT * FROM scan_stocks WHERE scan_id = %s ORDER BY created_at",
            (scan['id'],)
        )

        scan['scan_stocks'] = [dict(s) for s in stocks]
        return scan
    except Exception as e:
        print(f"Error fetching latest scan: {e}")
        return None


def get_scan_by_id(scan_id):
    """Get specific scan with stocks."""
    from app.db import execute_query

    try:
        scans = execute_query(
            "SELECT * FROM scans WHERE id = %s",
            (scan_id,)
        )

        if not scans:
            return None

        scan = dict(scans[0])

        # Get stocks for this scan
        stocks = execute_query(
            "SELECT * FROM scan_stocks WHERE scan_id = %s ORDER BY created_at",
            (scan_id,)
        )

        scan['scan_stocks'] = [dict(s) for s in stocks]
        return scan
    except Exception as e:
        print(f"Error fetching scan {scan_id}: {e}")
        return None


def get_all_scans(limit=50):
    """Get historical scans."""
    from app.db import execute_query

    try:
        result = execute_query(
            "SELECT id, created_at, scan_time, market_regime, actionable_count FROM scans ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        return [dict(r) for r in result]
    except Exception as e:
        print(f"Error fetching scans: {e}")
        return []


# Settings helpers
def get_settings():
    """Get all settings as dict."""
    from app.db import execute_query

    try:
        result = execute_query("SELECT * FROM settings")
        settings = {row['key']: row['value'] for row in result}
        # Merge with defaults for missing keys
        for k, v in DEFAULT_SETTINGS.items():
            if k not in settings:
                settings[k] = v
        return settings
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return DEFAULT_SETTINGS.copy()


def update_setting(key, value):
    """Update a single setting."""
    from app.db import execute_update

    try:
        value_json = json.dumps(value) if not isinstance(value, str) else value
        # Try update first
        updated = execute_update(
            "UPDATE settings SET value = %s, updated_at = NOW() WHERE key = %s",
            (value_json, key)
        )
        if updated == 0:
            # Insert if not exists
            from app.db import execute_insert
            execute_insert(
                "INSERT INTO settings (key, value) VALUES (%s, %s)",
                (key, value_json)
            )
        return True
    except Exception as e:
        print(f"Error updating setting {key}: {e}")
        return False


# Alert helpers
def get_all_alerts():
    """Get all alerts."""
    from app.db import execute_query

    try:
        result = execute_query(
            "SELECT * FROM alerts ORDER BY created_at DESC"
        )
        return [dict(r) for r in result]
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []


def add_alert(ticker, condition, price):
    """Add new alert."""
    from app.db import execute_insert

    try:
        result = execute_insert(
            "INSERT INTO alerts (ticker, condition, price, triggered) VALUES (%s, %s, %s, %s) RETURNING *",
            (ticker.upper(), condition, float(price), False)
        )
        return dict(result) if result else None
    except Exception as e:
        print(f"Error adding alert: {e}")
        return None


def delete_alert(alert_id):
    """Delete alert by ID."""
    from app.db import execute_update

    try:
        execute_update(
            "DELETE FROM alerts WHERE id = %s",
            (alert_id,)
        )
        return True
    except Exception as e:
        print(f"Error deleting alert: {e}")
        return False


# Earnings helpers
def get_all_earnings():
    """Get earnings calendar."""
    from app.db import execute_query

    try:
        result = execute_query("SELECT * FROM earnings")
        return {row['ticker']: row['earnings_date'] for row in result}
    except Exception as e:
        print(f"Error fetching earnings: {e}")
        return {}


def set_earnings_date(ticker, date):
    """Set earnings date for ticker."""
    from app.db import execute_update, execute_insert

    try:
        # Try update first
        updated = execute_update(
            "UPDATE earnings SET earnings_date = %s, updated_at = NOW() WHERE ticker = %s",
            (date, ticker.upper())
        )
        if updated == 0:
            # Insert if not exists
            execute_insert(
                "INSERT INTO earnings (ticker, earnings_date) VALUES (%s, %s)",
                (ticker.upper(), date)
            )
        return True
    except Exception as e:
        print(f"Error setting earnings for {ticker}: {e}")
        return False


# Position helpers
def get_all_positions(status=None):
    """Get positions filtered by status."""
    from app.db import execute_query

    try:
        if status:
            result = execute_query(
                "SELECT * FROM positions WHERE status = %s ORDER BY entry_date DESC",
                (status,)
            )
        else:
            result = execute_query(
                "SELECT * FROM positions ORDER BY entry_date DESC"
            )
        return [dict(r) for r in result]
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []


def add_position(position_data):
    """Add new position."""
    from app.db import execute_insert

    try:
        # Map field names to DB columns
        columns = ['ticker', 'account', 'trade_type', 'entry_date', 'entry_price',
                   'shares', 'cost_basis', 'stop_price', 'target_price', 'setup_type',
                   'status']
        values = []
        for col in columns:
            values.append(position_data.get(col))

        result = execute_insert(
            f"INSERT INTO positions ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))}) RETURNING *",
            tuple(values)
        )
        return dict(result) if result else None
    except Exception as e:
        print(f"Error adding position: {e}")
        return None


def update_position(position_id, updates):
    """Update position."""
    from app.db import execute_update, execute_query

    try:
        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [position_id]

        execute_update(
            f"UPDATE positions SET {set_clause} WHERE id = %s",
            tuple(values)
        )

        # Return updated position
        result = execute_query(
            "SELECT * FROM positions WHERE id = %s",
            (position_id,)
        )
        return dict(result[0]) if result else None
    except Exception as e:
        print(f"Error updating position: {e}")
        return None


def delete_position(position_id):
    """Delete position."""
    from app.db import execute_update

    try:
        execute_update(
            "DELETE FROM positions WHERE id = %s",
            (position_id,)
        )
        return True
    except Exception as e:
        print(f"Error deleting position: {e}")
        return False


def _positions_summary(positions):
    """Calculate positions summary."""
    open_pos = [p for p in positions if p.get('status') == 'open']
    closed_pos = [p for p in positions if p.get('status') != 'open']
    total_pnl = sum(p.get('pnl', 0) or 0 for p in closed_pos)

    return {
        'open_count': len(open_pos),
        'closed_count': len(closed_pos),
        'total_pnl': total_pnl
    }


# Covered calls helpers
def get_all_calls():
    """Get all covered calls."""
    from app.db import execute_query

    try:
        result = execute_query(
            "SELECT * FROM covered_calls ORDER BY sell_date DESC"
        )
        return [dict(r) for r in result]
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []


def add_call(call_data):
    """Add new covered call."""
    from app.db import execute_insert

    try:
        columns = ['ticker', 'sell_date', 'expiry', 'strike', 'contracts',
                   'premium_per_contract', 'premium_total', 'delta', 'stock_price_at_sell',
                   'status']
        values = []
        for col in columns:
            values.append(call_data.get(col))

        result = execute_insert(
            f"INSERT INTO covered_calls ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))}) RETURNING *",
            tuple(values)
        )
        return dict(result) if result else None
    except Exception as e:
        print(f"Error adding call: {e}")
        return None


def update_call(call_id, updates):
    """Update covered call."""
    from app.db import execute_update, execute_query

    try:
        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [call_id]

        execute_update(
            f"UPDATE covered_calls SET {set_clause} WHERE id = %s",
            tuple(values)
        )

        # Return updated call
        result = execute_query(
            "SELECT * FROM covered_calls WHERE id = %s",
            (call_id,)
        )
        return dict(result[0]) if result else None
    except Exception as e:
        print(f"Error updating call: {e}")
        return None


def delete_call(call_id):
    """Delete covered call."""
    from app.db import execute_update

    try:
        execute_update(
            "DELETE FROM covered_calls WHERE id = %s",
            (call_id,)
        )
        return True
    except Exception as e:
        print(f"Error deleting call: {e}")
        return False


def _calls_summary(trades):
    """Calculate calls summary."""
    def _summarize(subset, capital=100000):
        if not subset:
            return {'total_premium': 0, 'total_pnl': 0, 'total_trades': 0,
                    'expired': 0, 'called_away': 0, 'open': 0,
                    'weekly_avg': 0, 'annualized_yield': 0}
        total_premium = sum(t.get('premium_total', 0) for t in subset)
        closed = [t for t in subset if t.get('status') != 'open']
        total_pnl = sum(t.get('pnl', t.get('premium_total', 0)) for t in closed)
        open_t = [t for t in subset if t.get('status') == 'open']
        expired = [t for t in subset if t.get('status') == 'expired']
        called = [t for t in subset if t.get('status') == 'called_away']
        if subset:
            dates = sorted(set(t.get('sell_date', '')[:7] for t in subset if t.get('sell_date')))
            months = max(len(dates), 1)
            annualized = (total_premium / months) * 12 / max(capital, 1) * 100
        else:
            annualized = 0
        return {
            'total_premium': total_premium,
            'total_pnl': total_pnl,
            'total_trades': len(subset),
            'expired': len(expired),
            'called_away': len(called),
            'open': len(open_t),
            'weekly_avg': total_premium / max(len(subset), 1),
            'annualized_yield': annualized,
        }

    overall = _summarize(trades)
    tickers = sorted(set(t.get('ticker', 'SPY') for t in trades)) if trades else []
    by_ticker = {}
    for tk in tickers:
        subset = [t for t in trades if t.get('ticker', 'SPY') == tk]
        by_ticker[tk] = _summarize(subset, 100000)

    overall['tickers'] = tickers
    overall['by_ticker'] = by_ticker
    return overall


# Routine helpers
def get_routine(date_str):
    """Get routine for specific date."""
    from app.db import execute_query

    try:
        result = execute_query(
            "SELECT * FROM routines WHERE date = %s",
            (date_str,)
        )

        routines = {'date': date_str}
        for row in result:
            routines[row['routine_type']] = row['data']
        return routines
    except Exception as e:
        print(f"Error fetching routine for {date_str}: {e}")
        return {'date': date_str}


def save_routine(date_str, routine_type, data):
    """Save routine data."""
    from app.db import execute_update, execute_insert
    import json

    try:
        data_json = json.dumps(data) if not isinstance(data, str) else data

        # Try update first
        updated = execute_update(
            "UPDATE routines SET data = %s, updated_at = NOW() WHERE date = %s AND routine_type = %s",
            (data_json, date_str, routine_type)
        )
        if updated == 0:
            # Insert if not exists
            execute_insert(
                "INSERT INTO routines (date, routine_type, data) VALUES (%s, %s, %s)",
                (date_str, routine_type, data_json)
            )
        return True
    except Exception as e:
        print(f"Error saving routine: {e}")
        return False


def get_all_routine_dates():
    """Get set of dates that have routine records."""
    from app.db import execute_query

    try:
        result = execute_query(
            "SELECT date, routine_type FROM routines"
        )

        dates = {}
        for row in result:
            ds = row['date']
            if ds not in dates:
                dates[ds] = {'has_premarket': False, 'has_postclose': False}
            if row['routine_type'] == 'premarket':
                dates[ds]['has_premarket'] = True
            elif row['routine_type'] == 'postclose':
                dates[ds]['has_postclose'] = True
        return dates
    except Exception as e:
        print(f"Error fetching routine dates: {e}")
        return {}


# Backwards compatibility - legacy function names
load_calls = get_all_calls
save_calls = lambda trades: None  # No-op, use add_call/update_call instead
load_positions = lambda: get_all_positions()
save_positions = lambda positions: None  # No-op, use add_position/update_position instead
load_routine = get_routine
