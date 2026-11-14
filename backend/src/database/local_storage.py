"""CSV-backed local transaction storage for development."""

import csv
from pathlib import Path
from typing import Any

from src.config import load_settings

FIELDNAMES = [
    "transaction_id",
    "user_id",
    "date",
    "description",
    "amount",
    "type",
    "category",
]


def load_transactions(path: Path | None = None) -> list[dict[str, str]]:
    """Load transactions from the configured CSV file."""
    csv_path = path or load_settings().sample_data_path
    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def save_transaction(transaction: dict[str, Any], path: Path | None = None) -> None:
    """Append one transaction to a local CSV file."""
    csv_path = path or load_settings().sample_data_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, extrasaction="raise")
        if write_header:
            writer.writeheader()
        writer.writerow(transaction)
