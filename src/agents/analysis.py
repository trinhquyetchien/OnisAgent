"""Cash-flow analysis agent."""

from src.agents.base_agent import build_agent
from src.agents.prompts import ANALYSIS_SYSTEM_PROMPT as SYSTEM_PROMPT


def create_agent():
    """Create the transaction analysis agent."""
    return build_agent(SYSTEM_PROMPT)
