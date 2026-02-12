# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DeepDiver** is an autonomous trading system combining a CANSLIM Scanner Dashboard (Flask web UI) with an AI agent swarm for 24/7 market analysis. The system fetches real-time stock data from Google Sheets and provides trading tools including position sizing, alerts, earnings calendar, and automated agent workflows.

**Key Components:**
- **Dashboard**: Web UI for human oversight and discretionary trading
- **Wilson Agent**: Autonomous AI trader using Google ADK + OpenRouter
- **Cloud Persistence**: Supabase for agent logs and memory
- **Scheduled Tasks**: APScheduler for automated market monitoring

## Development Commands

### Running the Application

```bash
# Quick start (installs deps via uv, starts server)
./run.sh

# Manual setup
uv sync          # Install dependencies via uv
uv run run.py    # Run the Flask app
```

The app runs on `http://localhost:8080` by default (configurable via `PORT` in `.env`).

### Package Management

This project uses **uv** for dependency management:

```bash
# Install/sync dependencies
uv sync

# Add a new dependency
uv add package-name

# Update dependencies
uv lock --upgrade
```

Dependencies are defined in `pyproject.toml`, NOT `requirements.txt`.

### Verification

```bash
# Run health checks (verifies structure, sensitive data, config)
./verify.sh
```

Checks for:
- Required files and directories
- Sensitive data in code
- Environment variable configuration
- Executable permissions

### Testing Data Fetching

```bash
# Test gog CLI integration manually
gog sheets get $GOOGLE_SHEET_ID 'Main'!A1:W50 --json
```

## Configuration

Required environment variables in `.env`:

**Google Sheets:**
- `GOOGLE_SHEET_ID` - Google Sheet ID from URL
- `GOG_ACCOUNT` - Service account email with Viewer access
- `SHEET_RANGE` - Range to read (default: `'Main'!A1:W50`)
- `CACHE_DURATION` - Cache time in seconds (default: 300)

**AI Agent (Wilson):**
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM access
- `GEMINI_API_KEY` - (Optional) Direct Gemini API fallback

**Cloud Persistence:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anonymous key

**App:**
- `PORT` - Server port (default: 8080)
- `FLASK_ENV` - Environment (development/production)

## Architecture

### Application Structure

**Flask Application Factory Pattern** (`app/__init__.py`):
- `create_app()` initializes Flask app
- Registers blueprints (Dashboard)
- Initializes extensions (Supabase, APScheduler)
- Starts scheduled tasks on app startup

```
app/
├── __init__.py           # App factory (create_app)
├── extensions.py         # Shared resources (Supabase, Scheduler)
├── tasks.py              # Scheduled jobs (morning briefing, market monitor)
├── agents/               # AI Agent Logic
│   ├── wilson.py         # Lead trader agent (Google ADK)
│   ├── tools.py          # Agent tools (log_journal, check_market_status)
│   └── prompts.py        # System prompts
├── dashboard/            # Web UI Blueprint
│   ├── __init__.py       # Blueprint registration
│   ├── routes.py         # API endpoints and page routes
│   └── utils.py          # Data fetching, parsing, file I/O
├── templates/            # Jinja2 HTML templates
└── data/                 # JSON persistence (auto-created)
    ├── settings.json
    ├── alerts.json
    ├── history/
    └── routines/
```

Entry point: `run.py` calls `create_app()` and runs the Flask server.

### Data Flow

**Google Sheets → Dashboard:**
1. `fetch_sheet_data()` calls `gog` CLI subprocess
2. Returns JSON with sheet values
3. `parse_sheet_data()` extracts market regime, stocks, metadata
4. Cached for `CACHE_DURATION` seconds

**Sheet Data Structure:**
- **Row 0**: Title + scan timestamp
- **Row 1**: Market regime (Confirmed, Rally Attempt, Under Pressure, Correction)
- **Row 2**: Account balance, risk per trade, actionable count
- **Row 4**: Column headers
- **Rows 5+**: Stock data

**Position Sizing Logic** (in `dashboard/routes.py:api_data()`):
```python
risk_per_share = pivot - stop
shares = int(risk_per_trade / risk_per_share)
cost = shares * pivot
```

### AI Agent System

**Wilson Agent** (`app/agents/wilson.py`):
- Built with Google ADK (Agent Development Kit)
- Uses OpenRouter for LLM flexibility (default: `gemini-2.0-flash-001`)
- Tools: `log_journal()`, `check_market_status()`
- Autonomous decision-making (no user prompts)

**Agent Tools** (`app/agents/tools.py`):
- `@tool` decorator from Google ADK
- `log_journal(agent, category, content)` → Supabase `journal` table
- `check_market_status()` → Returns OPEN/CLOSED based on ET market hours

**Scheduled Tasks** (`app/tasks.py`):
- `task_morning_briefing()`: Runs 8:30 AM ET (Mon-Fri)
- `task_market_monitor()`: Every 15 mins during market hours (9 AM - 4 PM ET)

### Data Persistence

**Local JSON Files** (`app/data/`):
- `settings.json` - Account equity, risk %, max positions
- `alerts.json` - Price alerts
- `earnings.json` - Earnings dates by ticker
- `covered_calls.json` - Covered call trades
- `positions.json` - Stock positions
- `history/` - Historical scan snapshots
- `routines/` - Daily trading routines by date

**File Locking**: Uses `fcntl.flock()` for atomic writes with `.lock` and `.tmp` files.

**Cloud Storage** (Supabase):
- `journal` table - Agent logs (agent_name, category, content, created_at)

### Dashboard API Endpoints

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

**System:**
- `GET /system/health` - Health check endpoint

## Key Implementation Details

### Caching Strategy

Global cache dict in `dashboard/utils.py` tracks:
- `data` - Parsed sheet data
- `timestamp` - When cache was last updated
- `last_scan_time` - Scan timestamp to avoid duplicate snapshots

Cache invalidated when: force refresh requested OR cache age > `CACHE_DURATION`.

### Historical Snapshots

Automatically saved when `scan_time` changes in `get_cached_data()`. Prevents duplicate snapshots of same scan. Stored in `app/data/history/scan_YYYY-MM-DD_HHMM.json`.

### Input Validation

All POST/PATCH endpoints validate:
- Tickers: max 10 chars, alphanumeric + `.` and `-`
- Prices: positive, reasonable maximums
- Shares/contracts: positive integers with limits

Returns `400 Bad Request` for validation failures.

### Templates

All in `app/templates/`:
- `index.html` - Main dashboard (includes embedded CSS/JS)
- `calendar.html` - Calendar view for routines
- `calls.html` - Covered calls tracker
- `routine.html` - Daily routine viewer
- `routine_form.html` - Routine entry form

Templates use vanilla JavaScript (no frameworks).

### Scheduled Task System

**APScheduler** configured in `app/extensions.py`:
- Initialized via `scheduler.init_app(app)`
- Started in `create_app()` after loading `app/tasks.py`
- Uses `@scheduler.task()` decorator with cron expressions

**Adding a New Task:**
1. Add function to `app/tasks.py` with `@scheduler.task()` decorator
2. Scheduler auto-loads on app startup

### AI Agent Configuration

**OpenRouter Integration** (`app/agents/wilson.py`):
```python
model = Model(
    model_name="openai/google/gemini-2.0-flash-001",
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1"
)

wilson = Agent(
    name="Wilson",
    model=model,
    intro=WILSON_SYSTEM_PROMPT,
    tools=[log_journal, check_market_status]
)
```

**Invoking the Agent:**
```python
response = wilson.run("Your prompt here")
print(response.text)
```

## Common Development Tasks

### Adding a New Dashboard Feature

1. Add route in `app/dashboard/routes.py` (follow existing pattern)
2. Create or modify template in `app/templates/`
3. If persisting data, use `load_json_file()` and `save_json_file()` from `utils.py`
4. Add API endpoint under `/api/*` if needed

### Adding a New Agent Tool

1. Define function in `app/agents/tools.py`
2. Add `@tool` decorator from `google.adk.tools`
3. Register tool in `wilson.py` tools list
4. Tool will be auto-discovered by agent

### Adding a New Scheduled Task

1. Add function to `app/tasks.py`
2. Decorate with `@scheduler.task('cron', ...)`
3. Scheduler starts automatically on app launch

### Modifying Position Sizing Logic

Edit `app/dashboard/routes.py`, `api_data()` route around lines 39-53. Current formula:
```python
risk_per_share = pivot - stop
shares = int(risk_per_trade / risk_per_share)
```

### Changing Google Sheets Format

Update `parse_sheet_data()` in `app/dashboard/utils.py` to match new row structure.

### Adding a New Dependency

```bash
# Add package
uv add package-name

# Update pyproject.toml manually, then sync
uv sync
```

## External Dependencies

**Required:**
- **uv**: Package installer and resolver (replaces pip + venv)
- **gog CLI**: Required for Google Sheets integration. Must be installed and authenticated.
- **Google Sheets API**: Service account needs Viewer access to sheet.

**Python Packages** (see `pyproject.toml`):
- Flask 3.1.2+ (web framework)
- google-adk 1.25.0+ (agent framework)
- supabase 2.28.0+ (cloud database)
- flask-apscheduler 1.13.1+ (task scheduling)
- openai 2.20.0+ (OpenRouter client compatibility)

## Troubleshooting Development

**"Failed to fetch data":**
- Check `GOOGLE_SHEET_ID` and `GOG_ACCOUNT` in `.env`
- Verify sheet is shared with service account
- Test: `gog auth list` and `gog sheets get $GOOGLE_SHEET_ID 'Main'!A1:W50 --json`

**Port already in use:**
- Change `PORT=8081` in `.env`

**Cache not refreshing:**
- Click 🔄 Refresh button in UI (calls `/api/refresh`)
- Reduce `CACHE_DURATION` in `.env`
- Check scan timestamp in sheet is updating

**Scheduler not running:**
- Check console for "Scheduler started" message
- Verify tasks are defined in `app/tasks.py`
- Check `scheduler.get_jobs()` in Python shell

**Agent failing:**
- Verify `OPENROUTER_API_KEY` is set and valid
- Check Supabase connection: `SUPABASE_URL` and `SUPABASE_KEY`
- View logs in Supabase `journal` table
- Test agent manually: `uv run python -c "from app.agents.wilson import wilson; print(wilson.run('test'))"`

**uv command not found:**
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Or via pip: `pip install uv`
