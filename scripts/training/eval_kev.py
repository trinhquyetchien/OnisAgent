"""Evaluate Kev predictions against intent, route, or other scalar labels."""

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.data_prep.split_dataset import read_jsonl
from src.models.kev.inference_handler import InferenceHandler, resolve_callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST = PROJECT_ROOT / "data" / "splits" / "kev_test.jsonl"


def _field_value(value: Any, field: str) -> Any:
    current = value
    for part in field.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ValueError(f"Prediction/target is missing label field {field!r}.")
        current = current[part]
    if isinstance(current, (dict, list)) or current is None:
        raise ValueError(f"Label field {field!r} must contain a scalar value.")
    return current


def classification_metrics(
    ground_truth: Sequence[Any],
    predictions: Sequence[Any],
) -> dict[str, float]:
    """Return accuracy and unweighted macro precision, recall, and F1."""
    if not ground_truth or len(ground_truth) != len(predictions):
        raise ValueError("Ground-truth and prediction lists must be non-empty and equal length.")
    labels = list(dict.fromkeys((*ground_truth, *predictions)))
    accuracy = sum(actual == predicted for actual, predicted in zip(ground_truth, predictions)) / len(ground_truth)

    precision_scores: list[float] = []
    recall_scores: list[float] = []
    f1_scores: list[float] = []
    for label in labels:
        true_positive = sum(actual == label and predicted == label for actual, predicted in zip(ground_truth, predictions))
        predicted_count = sum(predicted == label for predicted in predictions)
        actual_count = sum(actual == label for actual in ground_truth)
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / actual_count if actual_count else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)

    return {
        "accuracy": accuracy,
        "precision_macro": sum(precision_scores) / len(precision_scores),
        "recall_macro": sum(recall_scores) / len(recall_scores),
        "f1_macro": sum(f1_scores) / len(f1_scores),
    }


def evaluate_records(
    records: Sequence[dict[str, Any]],
    predictor: Callable[[str], Any],
    fields: Sequence[str] = ("intent", "route"),
) -> dict[str, dict[str, float]]:
    if not records:
        raise ValueError("No evaluation records were provided.")
    if not fields:
        raise ValueError("At least one label field must be selected.")
    evaluated: list[tuple[Any, Any]] = []
    for index, record in enumerate(records, start=1):
        user_input = record.get("input")
        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError(f"Record {index} has no non-empty input.")
        if "target" not in record:
            raise ValueError(f"Record {index} has no target.")
        evaluated.append((record["target"], predictor(user_input)))
    return {
        field: classification_metrics(
            [_field_value(target, field) for target, _ in evaluated],
            [_field_value(prediction, field) for _, prediction in evaluated],
        )
        for field in fields
    }


def _handler_predictor(handler: InferenceHandler) -> Callable[[str], Any]:
    return lambda user_input: handler.predict(user_input).prediction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", type=Path, default=DEFAULT_TEST)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--loader", required=True, help="Checkpoint loader callable as 'module:callable'.")
    parser.add_argument("--fields", default="intent,route", help="Comma-separated target fields; supports dotted paths.")
    parser.add_argument("--report", type=Path, help="Optional JSON report path.")
    parser.add_argument("--overwrite-report", action="store_true")
    args = parser.parse_args()

    records = read_jsonl(args.test)
    loader = resolve_callable(args.loader)
    handler = InferenceHandler.from_checkpoint(args.checkpoint, loader)
    fields = tuple(field.strip() for field in args.fields.split(",") if field.strip())
    report = evaluate_records(records, _handler_predictor(handler), fields)

    print(f"Evaluation records: {len(records)}")
    for field, metrics in report.items():
        print(f"\n{field}")
        for name, value in metrics.items():
            print(f"  {name.replace('_', ' ').title():<18} {value:.4f}")

    if args.report:
        if args.report.exists() and not args.overwrite_report:
            raise FileExistsError(f"Refusing to overwrite report: {args.report}")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")


if __name__ == "__main__":
    main()
