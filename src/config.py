"""Application configuration loaded from environment variables and .env."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    aws_region: str
    bedrock_model_id: str
    dynamodb_table_name: str
    user_id: str
    data_source: str
    sample_data_path: Path


def load_settings() -> Settings:
    """Read and validate settings used by the application."""
    data_source = os.getenv("DATA_SOURCE", "csv").strip().lower()
    if data_source not in {"csv", "dynamodb"}:
        raise ValueError("DATA_SOURCE must be either 'csv' or 'dynamodb'.")

    sample_path = Path(os.getenv("SAMPLE_DATA_PATH", "data/sample_transactions_onis.csv"))
    if not sample_path.is_absolute():
        sample_path = PROJECT_ROOT / sample_path

    return Settings(
        aws_region=os.getenv("AWS_REGION", "ap-southeast-1"),
        bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "").strip(),
        dynamodb_table_name=os.getenv("DYNAMODB_TABLE_NAME", "").strip(),
        user_id=os.getenv("USER_ID", "demo").strip(),
        data_source=data_source,
        sample_data_path=sample_path,
    )
