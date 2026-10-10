import pytest

from src.agents.base_agent import build_agent


def test_build_agent_requires_bedrock_model_id(monkeypatch):
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)

    with pytest.raises(ValueError, match="BEDROCK_MODEL_ID"):
        build_agent("test prompt")
