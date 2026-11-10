"""Create deterministic train, validation, and test JSONL splits."""

import argparse
import json
import random
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "clean" / "kev_dataset_clean.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "splits"
SPLIT_NAMES = ("train", "val", "test")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    records: list[dict[str, Any]] = []
    with source.open(encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number}: invalid JSONL record") from exc
            if not isinstance(record, dict) or not isinstance(record.get("input"), str) or "target" not in record:
                raise ValueError(f"{source}:{line_number}: expected an object with input and target")
            records.append(record)
    if not records:
        raise ValueError(f"No records found in {source}")
    return records


def split_records(
    records: list[dict[str, Any]],
    *,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    ratios = (train_ratio, val_ratio, test_ratio)
    if any(ratio <= 0 for ratio in ratios) or abs(sum(ratios) - 1.0) > 1e-9:
        raise ValueError("Train, validation, and test ratios must be positive and sum to 1.")
    if len(records) < 3:
        raise ValueError("At least 3 records are required to create non-empty splits.")

    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    exact_counts = [len(shuffled) * ratio for ratio in ratios]
    counts = [int(count) for count in exact_counts]
    remainder = len(shuffled) - sum(counts)
    remainder_order = sorted(
        range(len(SPLIT_NAMES)),
        key=lambda index: (exact_counts[index] - counts[index], -index),
        reverse=True,
    )
    for index in remainder_order[:remainder]:
        counts[index] += 1
    train_end = counts[0]
    val_end = train_end + counts[1]
    if any(count == 0 for count in counts):
        raise ValueError("Ratios produce an empty split; use a larger dataset or adjust ratios.")
    return {
        "train": shuffled[:train_end],
        "val": shuffled[train_end:val_end],
        "test": shuffled[val_end:],
    }


def write_splits(
    splits: dict[str, list[dict[str, Any]]],
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    *,
    overwrite: bool = False,
) -> dict[str, Path]:
    destination = Path(output_dir)
    paths = {
        name: destination / f"kev_{name}.jsonl"
        for name in SPLIT_NAMES
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Refusing to overwrite existing split(s): "
            + ", ".join(str(path) for path in existing)
        )

    destination.mkdir(parents=True, exist_ok=True)
    for name, path in paths.items():
        mode = "w" if overwrite else "x"
        with path.open(mode, encoding="utf-8", newline="\n") as file:
            for record in splits[name]:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    records = read_jsonl(args.input)
    splits = split_records(
        records,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    paths = write_splits(splits, args.output_dir, overwrite=args.overwrite)
    for name, path in paths.items():
        print(f"{name}: {len(splits[name])} records -> {path}")


if __name__ == "__main__":
    main()
