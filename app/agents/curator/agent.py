"""
Curator Agent - AI Stock Universe Manager

Discovers, scores, and categorizes AI stocks from Russell 3000 index.
Promotes high-quality AI stocks to watchlist for Wilson to trade.
"""

from google.adk.agents import Agent
from google.adk.models import LiteLlm

# Import config first to load environment variables
from app.config import get_settings

# Import Curator's tools
from app.agents.curator.tools import scan_stock_for_ai, update_trading_universe, get_trading_universe

# Import shared tools (reused from Wilson)
from app.agents.tools import log_journal, add_to_watchlist, fetch_market_data

# Import system prompt
from app.agents.curator.prompt import CURATOR_SYSTEM_PROMPT

# Load settings (this sets OPENROUTER_API_KEY in env)
settings = get_settings()

# Configure LiteLlm for OpenRouter (same as Wilson)
# Model format: openrouter/<provider>/<model-name>
model = LiteLlm(
    model=settings.openrouter_llm_model,
)

# Define Curator Agent
root_agent = curator = Agent(
    name="Curator",
    model=model,
    description="AI Stock Universe Manager for DeepDiver trading system",
    instruction=CURATOR_SYSTEM_PROMPT,
    tools=[
        # Curator-specific tools (3 new)
        scan_stock_for_ai,
        update_trading_universe,
        get_trading_universe,
        # Shared tools (3 reused from Wilson)
        log_journal,
        add_to_watchlist,
        fetch_market_data,
    ],
)
