# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CANSLIM Scanner Dashboard is a Flask web application that displays real-time stock scans based on CANSLIM methodology. It fetches data from Google Sheets via the `gog` CLI tool and provides trading tools including position sizing, alerts, earnings calendar, covered calls tracking, and daily routine management.

## Development Commands

### Running the Application

```bash
# Start the dashboard (creates venv, installs deps, starts server)
./run.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The app runs on `http://localhost:5561` by default (configurable via `PORT` in `.env`).

### Verification

```bash
# Run verification checks
./verify.sh
```

Checks for required files, sensitive data, and configuration validity.

### Testing Data Fetching

```bash
# Manually test gog CLI integration
gog sheets get $GOOGLE_SHEET_ID 'Main'!A1:W50 --json
```

## Configuration

Required environment variables in `.env`:
- `GOOGLE_SHEET_ID` - Google Sheet ID from URL
- `GOG_ACCOUNT` - Service account email with Viewer access to sheet

Optional:
- `SHEET_RANGE` - Range to read (default: `'Main'!A1:W50`)
- `CACHE_DURATION` - Cache time in seconds (default: 300)
- `PORT` - Server port (default: 5561)

## Architecture

### Application Structure

**Single-file Flask application** (`app.py`, ~914 lines):
- Routes for dashboard, calendar, routines, covered calls
- RESTful API endpoints (`/api/*`)
- JSON file-based persistence in `data/` directory
- Template rendering via Jinja2 in `templates/`

### Data Flow

1. **Google Sheets → gog CLI → Flask**
   - `fetch_sheet_data()` calls `gog` CLI subprocess
   - Returns JSON with sheet values
   - Cached for CACHE_DURATION seconds

2. **Sheet Data Parsing** (`parse_sheet_data()`)
   - Row 0: Title + scan timestamp
   - Row 1: Market regime (Confirmed, Rally Attempt, etc.)
   - Row 2: Account balance, risk per trade, actionable count
   - Row 4: Column headers
   - Rows 5+: Stock data

3. **Position Sizing Logic** (in `/api/data` route)
   - Loads settings from `data/settings.json`
   - Calculates `Shares = risk_per_trade / (pivot - stop)`
   - Calculates `Cost = shares × pivot`

### Data Persistence

All user data stored as JSON files in `data/`:
- `settings.json` - Account equity, risk %, max positions
- `alerts.json` - Price alerts
- `earnings.json` - Earnings dates by ticker
- `covered_calls.json` - Covered call trades
- `positions.json` - Stock positions
- `history/` - Historical scan snapshots
- `routines/` - Daily trading routines by date

**File locking**: Uses `fcntl.flock()` for atomic writes with `.lock` and `.tmp` files.

### API Endpoints

**Data:**
- `GET /api/data` - Current scan data (with caching)
- `GET /api/refresh` - Force cache refresh
- `GET /api/export?filter=` - Export CSV

**Alerts:**
- `GET /api/alerts` - List all alerts
- `POST /api/alerts` - Add alert (ticker, condition, price)
- `DELETE /api/alerts/<index>` - Delete alert

**Earnings:**
- `GET /api/earnings` - Get earnings calendar
- `POST /api/earnings` - Set earnings date

**History:**
- `GET /api/history` - List snapshots
- `GET /api/history/<filename>` - Get specific snapshot

**Settings:**
- `GET /api/settings` - Get account settings
- `POST /api/settings` - Update settings

**Covered Calls:**
- `GET /api/calls` - List trades + summary
- `POST /api/calls` - Add new trade
- `PATCH /api/calls/<id>` - Close trade
- `DELETE /api/calls/<id>` - Delete trade

**Positions:**
- `GET /api/positions` - List positions + summary
- `POST /api/positions` - Add position
- `PATCH /api/positions/<id>` - Update/close position
- `DELETE /api/positions/<id>` - Delete position

**Routines:**
- `GET /routine` - Redirect to today
- `GET /routine/<date>` - View routine for date
- `GET /api/routine/<date>` - Get routine JSON
- `POST /api/routine/<date>` - Save routine

## Key Implementation Details

### Caching Strategy

Global cache dict tracks:
- `data` - Parsed sheet data
- `timestamp` - When cache was last updated
- `last_scan_time` - Scan timestamp to avoid duplicate snapshots

Cache invalidated when: force refresh requested OR cache age > CACHE_DURATION.

### Historical Snapshots

Automatically saved when scan_time changes (in `get_cached_data()`). Prevents duplicate snapshots of same scan. Stored in `data/history/scan_YYYY-MM-DD_HHMM.json`.

### Input Validation

All POST/PATCH endpoints validate:
- Tickers: max 10 chars, alphanumeric + `.` and `-`
- Prices: positive, reasonable maximums
- Shares/contracts: positive integers with limits

Returns `400 Bad Request` for validation failures.

### Templates

All in `templates/`:
- `index.html` - Main dashboard (53KB, includes embedded CSS/JS)
- `calendar.html` - Calendar view for routines
- `calls.html` - Covered calls tracker (41KB)
- `routine.html` - Daily routine viewer
- `routine_form.html` - Routine entry form

Templates use vanilla JavaScript (no frameworks).

## Common Development Tasks

### Adding a New Feature to Dashboard

1. Add route in `app.py` (follow existing pattern)
2. Create or modify template in `templates/`
3. If persisting data, use `load_json_file()` and `save_json_file()`
4. Add API endpoint under `/api/*` if needed

### Modifying Position Sizing Logic

Edit the `/api/data` route around lines 186-206. Current formula:
```python
risk_per_share = pivot - stop
shares = int(risk_per_trade / risk_per_share)
```

### Changing Google Sheets Format

Update `parse_sheet_data()` function (lines 126-172) to match new row structure.

### Adding New Data Storage

1. Define filepath constant at top of `app.py` (e.g., `FOO_FILE`)
2. Use `load_json_file(FOO_FILE, default)` to read
3. Use `save_json_file(FOO_FILE, data)` to write (handles locking)

## External Dependencies

- **gog CLI**: Required for Google Sheets integration. Must be installed and authenticated.
- **Google Sheets API**: Service account needs Viewer access to sheet.
- **Python packages**: Flask 3.0.0, Werkzeug 3.0.1 (see `requirements.txt`)

## Troubleshooting Development

**"Failed to fetch data":**
- Check `GOOGLE_SHEET_ID` and `GOG_ACCOUNT` in `.env`
- Verify sheet is shared with service account
- Test: `gog auth list` and manual `gog sheets get` command

**Port already in use:**
- Change `PORT=5562` in `.env`

**Cache not refreshing:**
- Click 🔄 Refresh button in UI (calls `/api/refresh`)
- Reduce `CACHE_DURATION` in `.env`
- Check scan timestamp in sheet is updating
