from google.adk.tools import FunctionTool
from app.extensions import supabase
import requests
import json
import os
from datetime import datetime
from polygon import RESTClient

def _log_journal(agent: str, category: str, content: str) -> str:
    """Logs an event to the cloud database (Supabase).
    
    Args:
        agent: Name of the agent (e.g., 'Wilson', 'Scanner').
        category: Type of log (Trade, Error, Summary, Signal, Thinking).
        content: The message to log.
    """
    if not supabase:
        print(f"[Fallback Log] {agent} | {category}: {content}")
        return "Supabase not connected. Logged to stdout."
        
    try:
        data = {
            "agent_name": agent, 
            "category": category, 
            "content": content,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("journal").insert(data).execute()
        return "Logged successfully."
    except Exception as e:
        print(f"[Log Error] {e}")
        return f"Log failed: {e}"

def _check_market_status() -> str:
    """Checks if the US stock market is currently open.
    
    Returns:
        A string indicating if the market is OPEN or CLOSED, and the time.
    """
    # Simple check based on time (9:30 AM - 4:00 PM ET)
    # For a real implementation, use pandas_market_calendars
    from datetime import datetime
    import pytz
    
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    
    is_weekday = now.weekday() < 5
    is_market_hours = (
        (now.hour > 9 or (now.hour == 9 and now.minute >= 30)) and
        (now.hour < 16)
    )
    
    status = "OPEN" if is_weekday and is_market_hours else "CLOSED"
    return f"Market is {status} (Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')})"

def _fetch_market_data(tickers: str) -> str:
    """Fetches real-time price and technical data from Polygon.io.

    Args:
        tickers: Comma-separated list of stock symbols (e.g., "AAPL,MSFT,GOOGL")

    Returns:
        JSON string with price data and technical indicators for each ticker
    """
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        return "Error: POLYGON_API_KEY not set in environment"

    try:
        client = RESTClient(api_key)
        ticker_list = [t.strip().upper() for t in tickers.split(',')]
        results = []

        for ticker in ticker_list:
            try:
                snapshot = client.get_snapshot_ticker('stocks', ticker)

                if snapshot and snapshot.ticker:
                    data = {
                        'ticker': ticker,
                        'price': snapshot.day.close if snapshot.day else 0,
                        'volume': snapshot.day.volume if snapshot.day else 0,
                        'change_pct': snapshot.day.change_percent if snapshot.day else 0,
                        'high': snapshot.day.high if snapshot.day else 0,
                        'low': snapshot.day.low if snapshot.day else 0,
                    }
                    results.append(data)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue

        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Error fetching market data: {str(e)}"

def _write_scan_results(market_regime: str, stocks_json: str, metadata_json: str = "{}") -> str:
    """Writes CANSLIM scan results to Supabase.

    Args:
        market_regime: Current market condition (e.g., "Confirmed", "Rally Attempt")
        stocks_json: JSON string with list of stock candidates
        metadata_json: JSON string with scan metadata (optional)

    Returns:
        Confirmation message with scan ID
    """
    if not supabase:
        return "Error: Supabase not connected"

    try:
        stocks = json.loads(stocks_json)
        metadata = json.loads(metadata_json)

        scan_data = {
            'scan_time': datetime.now().isoformat(),
            'market_regime': market_regime,
            'dist_days': metadata.get('dist_days', ''),
            'buy_ok': metadata.get('buy_ok', ''),
            'account_balance': metadata.get('account_balance'),
            'risk_per_trade': metadata.get('risk_per_trade'),
            'actionable_count': len(stocks),
            'metadata': metadata
        }

        scan_result = supabase.table('scans').insert(scan_data).execute()
        scan_id = scan_result.data[0]['id']

        for stock in stocks:
            stock['scan_id'] = scan_id

        supabase.table('scan_stocks').insert(stocks).execute()

        return f"✓ Scan saved successfully (ID: {scan_id}, {len(stocks)} stocks)"

    except Exception as e:
        return f"Error saving scan: {str(e)}"

def _get_current_positions() -> str:
    """Retrieves all open positions from Supabase.

    Returns:
        JSON string with list of open positions
    """
    if not supabase:
        return "Error: Supabase not connected"

    try:
        result = supabase.table('positions') \
            .select('*') \
            .eq('status', 'open') \
            .execute()

        return json.dumps(result.data, indent=2)

    except Exception as e:
        return f"Error fetching positions: {str(e)}"

def _get_watchlist() -> str:
    """Gets stocks currently being monitored.

    Returns:
        JSON string with watchlist stocks
    """
    if not supabase:
        return "Error: Supabase not connected"

    try:
        result = supabase.table('watchlist').select('*').execute()

        return json.dumps(result.data, indent=2)

    except Exception as e:
        return f"Error fetching watchlist: {str(e)}"

def _update_position(position_id: int, updates_json: str) -> str:
    """Updates a position (change stop, close, etc.).

    Args:
        position_id: Position ID to update
        updates_json: JSON string with fields to update

    Returns:
        Confirmation message
    """
    if not supabase:
        return "Error: Supabase not connected"

    try:
        updates = json.loads(updates_json)

        result = supabase.table('positions') \
            .update(updates) \
            .eq('id', position_id) \
            .execute()

        return f"✓ Position {position_id} updated successfully"

    except Exception as e:
        return f"Error updating position: {str(e)}"

def _check_alerts() -> str:
    """Checks if any price alerts have triggered.

    Returns:
        JSON string with triggered alerts
    """
    if not supabase:
        return "Error: Supabase not connected"

    try:
        result = supabase.table('alerts') \
            .select('*') \
            .eq('triggered', False) \
            .execute()

        alerts = result.data
        return json.dumps(alerts, indent=2)

    except Exception as e:
        return f"Error checking alerts: {str(e)}"

def _add_to_watchlist(ticker: str, status: str, score: float = 50.0) -> str:
    """Adds or updates a stock in the watchlist.

    Args:
        ticker: Stock symbol
        status: 'Watching', 'Long', or 'Short'
        score: Sentiment score 0-100

    Returns:
        Confirmation message
    """
    if not supabase:
        return "Error: Supabase not connected"

    try:
        data = {
            'ticker': ticker.upper(),
            'status': status,
            'sentiment_score': score
        }

        supabase.table('watchlist').upsert(data).execute()

        return f"✓ Added {ticker} to watchlist (status: {status})"

    except Exception as e:
        return f"Error adding to watchlist: {str(e)}"

# Wrap all functions with FunctionTool for google-adk compatibility
log_journal = FunctionTool(_log_journal)
check_market_status = FunctionTool(_check_market_status)
fetch_market_data = FunctionTool(_fetch_market_data)
write_scan_results = FunctionTool(_write_scan_results)
get_current_positions = FunctionTool(_get_current_positions)
get_watchlist = FunctionTool(_get_watchlist)
update_position = FunctionTool(_update_position)
check_alerts = FunctionTool(_check_alerts)
add_to_watchlist = FunctionTool(_add_to_watchlist)
