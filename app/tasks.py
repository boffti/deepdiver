from app.extensions import scheduler
from app.agents.wilson import wilson

@scheduler.task('cron', id='morning_briefing', day_of_week='mon-fri', hour=8, minute=30)
def task_morning_briefing():
    """Runs at 8:30 AM ET on Weekdays - Wilson performs CANSLIM scan."""
    print("⏰ Trigger: Morning Briefing / CANSLIM Scan")

    prompt = """It's 8:30 AM ET. Perform your morning CANSLIM scan:

    1. Check if market is open using check_market_status()
    2. Fetch market data for top momentum stocks using fetch_market_data()
       - Start with these tickers: AAPL,MSFT,GOOGL,NVDA,TSLA,META,AMZN
    3. Analyze each stock against CANSLIM criteria:
       - C: Current quarterly earnings (25%+ growth)
       - A: Annual earnings (25%+ growth over 3 years)
       - N: New highs, products, management
       - S: Supply & demand (volume, institutional buying)
       - L: Leader or laggard (RS rating > 80)
       - I: Institutional sponsorship
       - M: Market direction (confirm market regime)
    4. Determine market regime (Confirmed/Rally Attempt/Under Pressure/Correction)
    5. Write results using write_scan_results()
    6. Check alerts with check_alerts()
    7. Review current positions with get_current_positions()
    8. Log your analysis and recommendations to journal using log_journal()
    """

    try:
        response = wilson.run(prompt)
        print(f"✓ Morning scan completed")
        print(f"Wilson's response: {response.text}")
    except Exception as e:
        print(f"✗ Morning scan failed: {e}")
        # Log error to journal
        try:
            from app.agents.tools import log_journal
            log_journal("System", "Error", f"Morning scan failed: {e}")
        except:
            pass

@scheduler.task('cron', id='market_monitor', day_of_week='mon-fri', hour='9-16', minute='*/15')
def task_market_monitor():
    """Runs every 15 mins during market hours - Wilson monitors positions."""
    print("⏰ Trigger: Market Monitor")

    prompt = """Monitor the market and current positions:

    1. Check current positions using get_current_positions()
    2. Check if any alerts have triggered using check_alerts()
    3. Fetch latest prices for positions using fetch_market_data()
    4. If any positions need attention (hit stops, reached targets), log to journal
    5. Update watchlist if you see new opportunities
    """

    try:
        response = wilson.run(prompt)
        print(f"✓ Market monitor completed: {response.text}")
    except Exception as e:
        print(f"✗ Market monitor failed: {e}")
