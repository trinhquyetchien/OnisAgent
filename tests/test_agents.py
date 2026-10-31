import pytest

from src.agents.base_agent import build_agent
from src.agents.prompts import (
    ADVISORY_SYSTEM_PROMPT,
    ANALYSIS_SYSTEM_PROMPT,
    CATEGORIZATION_SYSTEM_PROMPT,
)


def test_build_agent_requires_bedrock_model_id(monkeypatch):
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)

    with pytest.raises(ValueError, match="BEDROCK_MODEL_ID"):
        build_agent("test prompt")


def test_categorization_prompt_supports_vietnamese_text_and_receipt_ocr():
    assert "bản chép lời nói" in CATEGORIZATION_SYSTEM_PROMPT
    assert "OCR từ ảnh hóa đơn" in CATEGORIZATION_SYSTEM_PROMPT
    assert "suy đoán thông tin còn thiếu" in CATEGORIZATION_SYSTEM_PROMPT


def test_financial_prompts_analyze_anomalies_and_preserve_user_approval():
    assert "biến động bất thường" in ANALYSIS_SYSTEM_PROMPT
    assert "tự thay đổi dữ liệu" in ANALYSIS_SYSTEM_PROMPT
    assert "tỷ lệ phân bổ thu nhập cố định" in ADVISORY_SYSTEM_PROMPT
    assert "calculator `Decimal`" in ADVISORY_SYSTEM_PROMPT
    assert "chưa có xác nhận của người dùng" in ADVISORY_SYSTEM_PROMPT
