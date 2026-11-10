"""Clean Kev JSONL data and remove duplicate inputs without editing the source."""

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "kev_dataset_raw.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "clean" / "kev_dataset_clean.jsonl"


def clean_dataset(
    input_file: str | Path = DEFAULT_INPUT,
    output_file: str | Path = DEFAULT_OUTPUT,
    *,
    overwrite: bool = False,
) -> dict[str, int]:
    source = Path(input_file)
    destination = Path(output_file)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output paths must be different to preserve the source dataset.")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing dataset: {destination}")

    seen_inputs: set[str] = set()
    cleaned_data: list[dict[str, Any]] = []
    invalid_count = 0
    duplicate_count = 0

    with source.open(encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("```"):
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                invalid_count += 1
                continue

            if not isinstance(record, dict):
                invalid_count += 1
                continue
            user_input = record.get("input")
            if not isinstance(user_input, str) or not user_input.strip() or "target" not in record:
                invalid_count += 1
                continue

            normalized_input = user_input.strip().casefold()
            if normalized_input in seen_inputs:
                duplicate_count += 1
                continue
            seen_inputs.add(normalized_input)
            cleaned_data.append(record)

    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as file:
        for record in cleaned_data:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "records_written": len(cleaned_data),
        "duplicates_removed": duplicate_count,
        "invalid_records": invalid_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file if it already exists.",
    )
    args = parser.parse_args()
    stats = clean_dataset(args.input, args.output, overwrite=args.overwrite)
    print(
        f"Wrote {stats['records_written']} records; "
        f"removed {stats['duplicates_removed']} duplicates; "
        f"skipped {stats['invalid_records']} invalid records."
    )
    print(f"Clean dataset: {args.output}")


if __name__ == "__main__":
    main()