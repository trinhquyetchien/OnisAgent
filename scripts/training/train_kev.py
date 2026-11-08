"""Training entry point that delegates to an explicitly selected framework adapter."""

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from scripts.data_prep.split_dataset import read_jsonl
from src.models.kev.inference_handler import resolve_callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAIN = PROJECT_ROOT / "data" / "splits" / "kev_train.jsonl"
DEFAULT_VALIDATION = PROJECT_ROOT / "data" / "splits" / "kev_val.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "checkpoints" / "kev"


@dataclass(frozen=True)
class TrainingConfig:
    framework: str
    base_model: str
    train_path: Path
    validation_path: Path
    output_dir: Path
    batch_size: int
    learning_rate: float
    epochs: int


def run_training(
    config: TrainingConfig,
    trainer: Callable[[TrainingConfig], Any],
    *,
    overwrite_output: bool = False,
) -> Any:
    if config.framework not in {"unsloth", "llama_factory"}:
        raise ValueError(f"Unsupported fine-tuning framework: {config.framework}")
    if not config.base_model.strip():
        raise ValueError("A base model identifier or local path is required.")
    if (
        config.batch_size <= 0
        or config.epochs <= 0
        or not math.isfinite(config.learning_rate)
        or config.learning_rate <= 0
    ):
        raise ValueError("Batch size, epochs, and learning rate must be positive.")
    read_jsonl(config.train_path)
    read_jsonl(config.validation_path)
    if config.output_dir.exists() and any(config.output_dir.iterdir()) and not overwrite_output:
        raise FileExistsError(
            f"Checkpoint directory is not empty: {config.output_dir}; "
            "pass overwrite_output=True to allow reuse."
        )
    config.output_dir.mkdir(parents=True, exist_ok=True)
    return trainer(config)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", choices=("unsloth", "llama_factory"), required=True)
    parser.add_argument("--trainer", required=True, help="Adapter callable as 'module:callable'.")
    parser.add_argument("--base-model", required=True, help="Model ID or local model path.")
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--overwrite-output", action="store_true")
    args = parser.parse_args()

    config = TrainingConfig(
        framework=args.framework,
        base_model=args.base_model,
        train_path=args.train,
        validation_path=args.validation,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
    )
    trainer = resolve_callable(args.trainer)
    result = run_training(config, trainer, overwrite_output=args.overwrite_output)
    print(f"Training adapter completed. Checkpoints: {config.output_dir}")
    if result is not None:
        print(result)


if __name__ == "__main__":
    main()
