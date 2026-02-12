import os
from google.adk.agents import Agent
from google.adk.models import LiteLlm
from app.agents.tools import (
    log_journal,
    check_market_status,
    fetch_market_data,
    write_scan_results,
    get_current_positions,
    get_watchlist,
    update_position,
    check_alerts,
    add_to_watchlist
)
from app.agents.prompts import WILSON_SYSTEM_PROMPT

# Configure LiteLlm for OpenRouter
openrouter_key = os.environ.get("OPENROUTER_API_KEY")

# Create a LiteLlm instance configured for OpenRouter
# LiteLlm uses litellm under the hood which supports OpenRouter
model = LiteLlm(
    model="openrouter/google/gemini-2.0-flash-thinking-exp:free",
    api_key=openrouter_key,
    api_base="https://openrouter.ai/api/v1"
)

# Define the Orchestrator
wilson = Agent(
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
        add_to_watchlist
    ]
)

