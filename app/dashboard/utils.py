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

def _get_supabase():
    """Get Supabase client (lazy import to avoid circular dependency)"""
    from app.extensions import supabase
    return supabase

# Scan helpers
def get_latest_scan():
    """Get most recent CANSLIM scan with stocks."""
    supabase = _get_supabase()
    try:
        result = supabase.table('scans') \
            .select('*, scan_stocks(*)') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching latest scan: {e}")
        return None

def get_scan_by_id(scan_id):
    """Get specific scan with stocks."""
    supabase = _get_supabase()
    try:
        result = supabase.table('scans') \
            .select('*, scan_stocks(*)') \
            .eq('id', scan_id) \
            .single() \
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching scan {scan_id}: {e}")
        return None

def get_all_scans(limit=50):
    """Get historical scans."""
    supabase = _get_supabase()
    try:
        result = supabase.table('scans') \
            .select('id, created_at, scan_time, market_regime, actionable_count') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching scans: {e}")
        return []

# Settings helpers
def get_settings():
    """Get all settings as dict."""
    supabase = _get_supabase()
    try:
        result = supabase.table('settings').select('*').execute()
        settings = {row['key']: row['value'] for row in result.data}
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
    supabase = _get_supabase()
    try:
        supabase.table('settings') \
            .upsert({'key': key, 'value': value}) \
            .execute()
        return True
    except Exception as e:
        print(f"Error updating setting {key}: {e}")
        return False

# Alert helpers
def get_all_alerts():
    """Get all alerts."""
    supabase = _get_supabase()
    try:
        result = supabase.table('alerts') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []

def add_alert(ticker, condition, price):
    """Add new alert."""
    supabase = _get_supabase()
    try:
        result = supabase.table('alerts').insert({
            'ticker': ticker.upper(),
            'condition': condition,
            'price': float(price),
            'triggered': False
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error adding alert: {e}")
        return None

def delete_alert(alert_id):
    """Delete alert by ID."""
    supabase = _get_supabase()
    try:
        supabase.table('alerts').delete().eq('id', alert_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting alert: {e}")
        return False

# Earnings helpers
def get_all_earnings():
    """Get earnings calendar."""
    supabase = _get_supabase()
    try:
        result = supabase.table('earnings').select('*').execute()
        return {row['ticker']: row['earnings_date'] for row in result.data}
    except Exception as e:
        print(f"Error fetching earnings: {e}")
        return {}

def set_earnings_date(ticker, date):
    """Set earnings date for ticker."""
    supabase = _get_supabase()
    try:
        supabase.table('earnings') \
            .upsert({'ticker': ticker.upper(), 'earnings_date': date}) \
            .execute()
        return True
    except Exception as e:
        print(f"Error setting earnings for {ticker}: {e}")
        return False

# Position helpers
def get_all_positions(status=None):
    """Get positions filtered by status."""
    supabase = _get_supabase()
    try:
        query = supabase.table('positions').select('*')
        if status:
            query = query.eq('status', status)
        result = query.order('entry_date', desc=True).execute()
        return result.data
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []

def add_position(position_data):
    """Add new position."""
    supabase = _get_supabase()
    try:
        result = supabase.table('positions').insert(position_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error adding position: {e}")
        return None

def update_position(position_id, updates):
    """Update position."""
    supabase = _get_supabase()
    try:
        result = supabase.table('positions') \
            .update(updates) \
            .eq('id', position_id) \
            .execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error updating position: {e}")
        return None

def delete_position(position_id):
    """Delete position."""
    supabase = _get_supabase()
    try:
        supabase.table('positions').delete().eq('id', position_id).execute()
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
    supabase = _get_supabase()
    try:
        result = supabase.table('covered_calls') \
            .select('*') \
            .order('sell_date', desc=True) \
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def add_call(call_data):
    """Add new covered call."""
    supabase = _get_supabase()
    try:
        result = supabase.table('covered_calls').insert(call_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error adding call: {e}")
        return None

def update_call(call_id, updates):
    """Update covered call."""
    supabase = _get_supabase()
    try:
        result = supabase.table('covered_calls') \
            .update(updates) \
            .eq('id', call_id) \
            .execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error updating call: {e}")
        return None

def delete_call(call_id):
    """Delete covered call."""
    supabase = _get_supabase()
    try:
        supabase.table('covered_calls').delete().eq('id', call_id).execute()
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
    supabase = _get_supabase()
    try:
        result = supabase.table('routines') \
            .select('*') \
            .eq('date', date_str) \
            .execute()

        routines = {'date': date_str}
        for row in result.data:
            routines[row['routine_type']] = row['data']
        return routines
    except Exception as e:
        print(f"Error fetching routine for {date_str}: {e}")
        return {'date': date_str}

def save_routine(date_str, routine_type, data):
    """Save routine data."""
    supabase = _get_supabase()
    try:
        supabase.table('routines') \
            .upsert({
                'date': date_str,
                'routine_type': routine_type,
                'data': data
            }) \
            .execute()
        return True
    except Exception as e:
        print(f"Error saving routine: {e}")
        return False

def get_all_routine_dates():
    """Get set of dates that have routine records."""
    supabase = _get_supabase()
    try:
        result = supabase.table('routines') \
            .select('date, routine_type') \
            .execute()

        dates = {}
        for row in result.data:
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
