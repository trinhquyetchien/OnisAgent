"""Unit tests for Ollama Local LLM Client (Reasoning Path)."""

from unittest.mock import MagicMock, patch
import pytest

from src.agents.ollama_client import OllamaClient


def test_ollama_client_init_defaults():
    client = OllamaClient()
    assert client.base_url.startswith("http")
    assert "qwen" in client.model.lower()
    assert client.timeout > 0


def test_ollama_client_is_available_live_or_mock():
    client = OllamaClient()
    # Check live response or mock check
    res = client.is_available()
    assert isinstance(res, bool)


def test_ollama_generate_reasoning_response_fallback_on_error():
    client = OllamaClient(base_url="http://127.0.0.1:99999", timeout=0.1)
    prompt = "Phân tích tài chính cá nhân giúp tôi"
    reply = client.generate_reasoning_response(prompt=prompt)
    assert len(reply) > 20
    assert "tài chính" in reply.lower() or "dự phòng" in reply.lower()


def test_ollama_generate_reasoning_response_with_mocked_success():
    client = OllamaClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"content": "Chào bạn, đây là phân tích chi tiêu tối ưu cho bạn."}
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = client.generate_reasoning_response(
            prompt="Phân tích chi tiêu",
            context={"balance": 18450000},
        )
        assert "tối ưu" in res
