"""Convert Kev JSONL records to common fine-tuning chat formats."""

import argparse
import json
from pathlib import Path
from typing import Any

FORMAT_NAMES = ("unsloth", "llama_factory", "ollama")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "clean" / "kev_dataset_clean.jsonl"


def _record_parts(record: dict[str, Any]) -> tuple[str, str]:
    user_input = record.get("input")
    if not isinstance(user_input, str) or not user_input.strip():
        raise ValueError("Each record must contain a non-empty string 'input'.")
    if "target" not in record:
        raise ValueError("Each record must contain a 'target'.")
    target = record["target"]
    output = target if isinstance(target, str) else json.dumps(
        target,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return user_input.strip(), output


def format_record(record: dict[str, Any], format_name: str) -> dict[str, Any]:
    if format_name not in FORMAT_NAMES:
        raise ValueError(f"Unsupported format {format_name!r}; choose from {FORMAT_NAMES}.")
    user_input, output = _record_parts(record)

    if format_name == "llama_factory":
        return {"instruction": user_input, "input": "", "output": output}

    return {
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": output},
        ]
    }


def format_jsonl(
    input_path: str | Path,
    output_path: str | Path,
    format_name: str,
    *,
    overwrite: bool = False,
) -> int:
    source = Path(input_path)
    destination = Path(output_path)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output paths must be different to preserve the source dataset.")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing dataset: {destination}")

    formatted: list[dict[str, Any]] = []
    with source.open(encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number}: invalid JSONL record") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{source}:{line_number}: expected a JSON object")
            try:
                formatted.append(format_record(record, format_name))
            except ValueError as exc:
                raise ValueError(f"{source}:{line_number}: {exc}") from exc

    if not formatted:
        raise ValueError(f"No records found in {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as file:
        for record in formatted:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(formatted)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=FORMAT_NAMES, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    count = format_jsonl(args.input, args.output, args.format, overwrite=args.overwrite)
    print(f"Formatted {count} records as {args.format}: {args.output}")


if __name__ == "__main__":
    main()
