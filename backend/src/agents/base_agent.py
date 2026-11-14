"""Shared Amazon Bedrock-backed Strands agent construction."""

from collections.abc import Callable, Sequence
from typing import Any

from src.config import load_settings


def build_agent(
    system_prompt: str,
    tools: Sequence[Callable[..., Any]] | None = None,
) -> Any:
    """Create a Strands Agent using the configured Amazon Bedrock model."""
    settings = load_settings()
    if not settings.bedrock_model_id:
        raise ValueError("Set BEDROCK_MODEL_ID before creating a Bedrock agent.")

    from strands import Agent
    from strands.models import BedrockModel

    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )
    return Agent(model=model, tools=list(tools or ()), system_prompt=system_prompt)
