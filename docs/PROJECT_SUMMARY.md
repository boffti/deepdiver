# Project DeepDiver: Autonomous Trading Swarm

## 📦 Release Package

**Status**: 🛠️ Refactoring for DeepDiver Swarm  
**Version**: 2.1.0 (DeepDiver Beta - OpenRouter Support)  
**Date**: February 11, 2026

## 🎯 What This Is

DeepDiver is an autonomous trading system designed to run 24/7 on edge hardware (Raspberry Pi/Server). It combines the original CANSLIM Dashboard for human oversight with an AI agent swarm ("Wilson") for automated market analysis, signal generation, and logging.

## ✅ What's Included

### Core Files
- `run.py`: Main entry point (Flask App Factory).
- `app/`: New package structure.
  - `agents/`: AI logic (Wilson, Tools, Prompts).
  - `dashboard/`: The classic Web UI (Refactored to Blueprint).
  - `tasks.py`: Scheduler definitions (Morning Briefing, Market Monitor).
  - `extensions.py`: Shared resources (Supabase, Scheduler).

### Configuration
- `.env.example`: Template for API keys (OpenRouter, Supabase, Google Sheets).
- `pyproject.toml`: Modern dependency management (managed by `uv`).


### Features
- **Hybrid System**: 
  - **Human**: Visual dashboard for verifying data and discretionary trades.
  - **AI**: Autonomous agents performing routine scans and logging thoughts.
- **Cloud Persistence**: Supabase integration for logs and agent memory.
- **Event-Driven**: APScheduler triggers agent workflows based on market hours.
- **OpenRouter Integration**: Agents use OpenRouter API for flexible model selection (e.g., Gemini 2.0 Flash).

## 🚀 Quick Start

```bash
# 1. Setup Environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY, SUPABASE_URL, etc.

# 2. Install Dependencies (using uv)
uv sync

# 3. Run
./run.sh
# Access Dashboard at http://localhost:8080/
```

## 📁 File Structure

```
deepdiver/
├── app/
│   ├── agents/            # AI Swarm Logic
│   │   ├── wilson.py      # Lead Trader Agent (OpenRouter Supported)
│   │   ├── tools.py       # Agent Tools
│   │   └── prompts.py     # System Prompts
│   ├── dashboard/         # Web UI (Legacy Code Refactored)
│   │   ├── routes.py
│   │   └── utils.py
│   ├── templates/         # HTML Files
│   ├── data/              # Local Data (JSON)
│   ├── tasks.py           # Verification & Cron Jobs
│   └── extensions.py      # Database & Scheduler Init
├── run.py                 # Application Entry Point
├── run.sh                 # Startup Script
├── verify.sh              # Health Check
└── pyproject.toml         # Dependencies

```

## 🛣️ Roadmap

- [x] Refactor Monolith to Modular App Factory
- [x] Implement Wilson Agent Skeleton
- [x] Integrate Supabase Logging
- [x] Integrate OpenRouter for LLM flexibility
- [ ] Implement Real Broker Execution (Interactive Brokers/Alpaca)
- [ ] Add Multi-Agent Conversation (Debates between Bull/Bear agents)
