from google.adk.tools import FunctionTool
from app.db import execute_query, execute_insert, execute_update
from app.config import get_settings
import requests
import json
from datetime import datetime


def _log_journal(agent: str, category: str, content: str) -> str:
    """Logs an event to the local PostgreSQL database.

    Args:
        agent: Name of the agent (e.g., 'Wilson', 'Scanner').
        category: Type of log (Trade, Error, Summary, Signal, Thinking).
        content: The message to log.
    """
    try:
        data = {
            "agent_name": agent,
            "category": category,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        }
        execute_insert(
            "INSERT INTO journal (agent_name, category, content, created_at) VALUES (%s, %s, %s, %s)",
            (data["agent_name"], data["category"], data["content"], data["created_at"])
        )
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
    from datetime import datetime
    import pytz

    tz = pytz.timezone("US/Eastern")
    now = datetime.now(tz)

    is_weekday = now.weekday() < 5
    is_market_hours = (now.hour > 9 or (now.hour == 9 and now.minute >= 30)) and (
        now.hour < 16
    )

    status = "OPEN" if is_weekday and is_market_hours else "CLOSED"
    return f"Market is {status} (Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')})"


def _fetch_market_data(tickers: str) -> str:
    """Fetches real-time price and technical data from Alpaca.

    Args:
        tickers: Comma-separated list of stock symbols (e.g., "AAPL,MSFT,GOOGL")

    Returns:
        JSON string with price data and technical indicators for each ticker
    """
    settings = get_settings()
    api_key = settings.alpaca_api_key
    secret_key = settings.alpaca_secret_key.get_secret_value()

    if not api_key or not secret_key:
        return "Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment"

    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockSnapshotRequest

        client = StockHistoricalDataClient(api_key, secret_key)
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        # Create request for stock snapshots
        request = StockSnapshotRequest(symbol_or_symbols=ticker_list)
        snapshots = client.get_stock_snapshot(request)

        results = []
        for ticker in ticker_list:
            try:
                snapshot = snapshots.get(ticker)
                if snapshot and snapshot.latest_trade:
                    # Calculate change percentage
                    if (
                        snapshot.daily_bar
                        and snapshot.daily_bar.close
                        and snapshot.previous_daily_bar
                    ):
                        prev_close = snapshot.previous_daily_bar.close
                        current_close = snapshot.daily_bar.close
                        change_pct = ((current_close - prev_close) / prev_close) * 100
                    else:
                        change_pct = 0.0

                    data = {
                        "ticker": ticker,
                        "price": float(snapshot.latest_trade.price)
                        if snapshot.latest_trade
                        else 0,
                        "volume": int(snapshot.daily_bar.volume)
                        if snapshot.daily_bar
                        else 0,
                        "change_pct": round(change_pct, 2),
                        "high": float(snapshot.daily_bar.high)
                        if snapshot.daily_bar
                        else 0,
                        "low": float(snapshot.daily_bar.low)
                        if snapshot.daily_bar
                        else 0,
                    }
                    results.append(data)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue

        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Error fetching market data: {str(e)}"


def _write_scan_results(
    market_regime: str, stocks_json: str, metadata_json: str = "{}"
) -> str:
    """Writes CANSLIM scan results to local PostgreSQL.

    Args:
        market_regime: Current market condition (e.g., "Confirmed", "Rally Attempt")
        stocks_json: JSON string with list of stock candidates
        metadata_json: JSON string with scan metadata (optional)

    Returns:
        Confirmation message with scan ID
    """
    try:
        stocks = json.loads(stocks_json)
        metadata = json.loads(metadata_json)

        scan_data = {
            "scan_time": datetime.now().isoformat(),
            "market_regime": market_regime,
            "dist_days": metadata.get("dist_days", ""),
            "buy_ok": metadata.get("buy_ok", ""),
            "account_balance": metadata.get("account_balance"),
            "risk_per_trade": metadata.get("risk_per_trade"),
            "actionable_count": len(stocks),
            "metadata": json.dumps(metadata),
        }

        # Insert scan
        scan_id = execute_insert(
            """INSERT INTO scans (scan_time, market_regime, dist_days, buy_ok, account_balance, risk_per_trade, actionable_count, metadata)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (scan_data["scan_time"], scan_data["market_regime"], scan_data["dist_days"],
             scan_data["buy_ok"], scan_data["account_balance"], scan_data["risk_per_trade"],
             scan_data["actionable_count"], scan_data["metadata"])
        )

        # Insert stocks
        for stock in stocks:
            execute_insert(
                """INSERT INTO scan_stocks (scan_id, ticker, pivot, stop, rs_rating, comp_rating, eps_rating, setup_type, notes, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (scan_id, stock.get("ticker"), stock.get("pivot"), stock.get("stop"),
                 stock.get("rs_rating"), stock.get("comp_rating"), stock.get("eps_rating"),
                 stock.get("setup_type"), stock.get("notes"),
                 json.dumps(stock.get("metadata", {})))
            )

        return f"✓ Scan saved successfully (ID: {scan_id}, {len(stocks)} stocks)"

    except Exception as e:
        return f"Error saving scan: {str(e)}"


def _get_current_positions() -> str:
    """Retrieves all open positions from local PostgreSQL.

    Returns:
        JSON string with list of open positions
    """
    try:
        result = execute_query(
            "SELECT * FROM positions WHERE status = %s",
            ("open",)
        )
        return json.dumps([dict(r) for r in result], indent=2, default=str)

    except Exception as e:
        return f"Error fetching positions: {str(e)}"


def _get_watchlist() -> str:
    """Gets stocks currently being monitored.

    Returns:
        JSON string with watchlist stocks
    """
    try:
        result = execute_query("SELECT * FROM watchlist")
        return json.dumps([dict(r) for r in result], indent=2, default=str)

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
    try:
        updates = json.loads(updates_json)

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [position_id]

        execute_update(
            f"UPDATE positions SET {set_clause} WHERE id = %s",
            tuple(values)
        )

        return f"✓ Position {position_id} updated successfully"

    except Exception as e:
        return f"Error updating position: {str(e)}"


def _check_alerts() -> str:
    """Checks if any price alerts have triggered.

    Returns:
        JSON string with triggered alerts
    """
    try:
        result = execute_query(
            "SELECT * FROM alerts WHERE triggered = %s",
            (False,)
        )
        return json.dumps([dict(r) for r in result], indent=2, default=str)

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
    try:
        # Try update first
        updated = execute_update(
            "UPDATE watchlist SET status = %s, sentiment_score = %s, last_updated = NOW() WHERE ticker = %s",
            (status, score, ticker.upper())
        )
        if updated == 0:
            # Insert if not exists
            execute_insert(
                "INSERT INTO watchlist (ticker, status, sentiment_score) VALUES (%s, %s, %s)",
                (ticker.upper(), status, score)
            )

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
