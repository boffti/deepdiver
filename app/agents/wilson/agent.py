from google.adk.agents import Agent
from google.adk.models import LiteLlm

# Import config first to load environment variables
from app.config import get_settings
from app.agents.tools import (
    log_journal,
    check_market_status,
    fetch_market_data,
    write_scan_results,
    get_current_positions,
    get_watchlist,
    update_position,
    check_alerts,
    add_to_watchlist,
)
from app.agents.wilson.prompt import WILSON_SYSTEM_PROMPT

# Load settings (this sets OPENROUTER_API_KEY in env)
settings = get_settings()

# Configure LiteLlm for OpenRouter
# Model format: openrouter/<provider>/<model-name>
model = LiteLlm(
    model=settings.openrouter_llm_model,
)

# Define the Orchestrator
root_agent = wilson = Agent(
    name="Wilson",
    model=model,
    description="Lead trader agent for autonomous CANSLIM market analysis and trade execution",
    instruction=WILSON_SYSTEM_PROMPT,
    tools=[
        log_journal,
        check_market_status,
        fetch_market_data,
        write_scan_results,
        get_current_positions,
        get_watchlist,
        update_position,
        check_alerts,
        add_to_watchlist,
    ],
)
