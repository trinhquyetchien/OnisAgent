import json

import pytest

from scripts.data_prep.clean_dataset import clean_dataset
from scripts.data_prep.split_dataset import split_records, write_splits
from scripts.training.eval_kev import classification_metrics, evaluate_records
from scripts.training.train_kev import TrainingConfig, run_training
from src.models.kev.dataset_formatter import format_record
from src.models.kev.inference_handler import InferenceHandler


def test_dataset_formatter_preserves_nested_labels_without_mutating_source():
    record = {
        "input": "xem số dư",
        "target": {"intent": "balance.query", "route": "FAST_PATH"},
    }
    original = json.loads(json.dumps(record))

    unsloth = format_record(record, "unsloth")
    llama_factory = format_record(record, "llama_factory")
    ollama = format_record(record, "ollama")

    assert unsloth["messages"][0] == {"role": "user", "content": "xem số dư"}
    assert json.loads(unsloth["messages"][1]["content"]) == record["target"]
    assert llama_factory["instruction"] == "xem số dư"
    assert json.loads(llama_factory["output"]) == record["target"]
    assert ollama["messages"] == unsloth["messages"]
    assert record == original


def test_split_records_is_reproducible_and_keeps_all_examples():
    records = [{"input": str(index), "target": {"intent": "test"}} for index in range(20)]
    first = split_records(records, seed=13)
    second = split_records(records, seed=13)

    assert first == second
    assert [len(first[name]) for name in ("train", "val", "test")] == [16, 2, 2]
    assert {row["input"] for rows in first.values() for row in rows} == {
        row["input"] for row in records
    }


def test_split_writer_refuses_to_overwrite_existing_files(tmp_path):
    records = [{"input": str(index), "target": {"intent": "test"}} for index in range(10)]
    splits = split_records(records)
    write_splits(splits, tmp_path)

    with pytest.raises(FileExistsError):
        write_splits(splits, tmp_path)


def test_training_entrypoint_validates_data_and_delegates_to_adapter(tmp_path):
    train_path = tmp_path / "train.jsonl"
    validation_path = tmp_path / "val.jsonl"
    record = json.dumps({"input": "test", "target": {"intent": "test"}})
    train_path.write_text(record + "\n", encoding="utf-8")
    validation_path.write_text(record + "\n", encoding="utf-8")
    output_dir = tmp_path / "checkpoints"
    config = TrainingConfig(
        framework="unsloth",
        base_model="model-id-or-local-path",
        train_path=train_path,
        validation_path=validation_path,
        output_dir=output_dir,
        batch_size=2,
        learning_rate=0.0002,
        epochs=1,
    )
    calls = []

    result = run_training(config, lambda received: calls.append(received) or "done")

    assert result == "done"
    assert calls == [config]
    assert output_dir.is_dir()


def test_training_entrypoint_refuses_nonempty_checkpoint_directory(tmp_path):
    train_path = tmp_path / "train.jsonl"
    record = json.dumps({"input": "test", "target": {"intent": "test"}})
    train_path.write_text(record + "\n", encoding="utf-8")
    output_dir = tmp_path / "checkpoints"
    output_dir.mkdir()
    (output_dir / "existing.bin").write_bytes(b"keep")
    config = TrainingConfig(
        framework="llama_factory",
        base_model="model-id-or-local-path",
        train_path=train_path,
        validation_path=train_path,
        output_dir=output_dir,
        batch_size=1,
        learning_rate=0.0001,
        epochs=1,
    )

    with pytest.raises(FileExistsError):
        run_training(config, lambda _: pytest.fail("trainer must not run"))

    assert (output_dir / "existing.bin").read_bytes() == b"keep"


def test_clean_dataset_handles_jsonl_fences_deduplicates_and_preserves_input(tmp_path):
    source = tmp_path / "source.jsonl"
    output = tmp_path / "clean.jsonl"
    source.write_text(
        '```jsonl\n{"input":"A","target":{"intent":"x"}}\n'
        '{"input":" a ","target":{"intent":"x"}}\n```\n',
        encoding="utf-8",
    )
    original = source.read_bytes()

    stats = clean_dataset(source, output)

    assert stats == {
        "records_written": 1,
        "duplicates_removed": 1,
        "invalid_records": 0,
    }
    assert source.read_bytes() == original
    assert json.loads(output.read_text(encoding="utf-8"))["input"] == "A"


def test_clean_dataset_refuses_to_overwrite_its_input(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text('{"input":"A","target":"x"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="different"):
        clean_dataset(source, source, overwrite=True)


def test_classification_metrics_report_macro_precision_recall_and_f1():
    metrics = classification_metrics(
        ["expense", "expense", "income"],
        ["expense", "income", "income"],
    )

    assert metrics == {
        "accuracy": pytest.approx(2 / 3),
        "precision_macro": pytest.approx(0.75),
        "recall_macro": pytest.approx(0.75),
        "f1_macro": pytest.approx(2 / 3),
    }


def test_evaluate_records_supports_multiple_target_labels_with_one_prediction():
    calls = []

    def predictor(user_input):
        calls.append(user_input)
        return {"intent": "balance.query", "route": "FAST_PATH"}

    results = evaluate_records(
        [
            {
                "input": "số dư",
                "target": {"intent": "balance.query", "route": "FAST_PATH"},
            }
        ],
        predictor,
    )

    assert calls == ["số dư"]
    assert results["intent"]["accuracy"] == 1
    assert results["route"]["f1_macro"] == 1


def test_inference_handler_measures_prediction_and_validates_input(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    handler = InferenceHandler.from_checkpoint(checkpoint, lambda path: lambda text: {"intent": text})

    result = handler.predict("balance?")

    assert result.prediction == {"intent": "balance?"}
    assert result.latency_ms >= 0
    assert len(handler.benchmark(["first", "second"], repetitions=2)) == 4
    with pytest.raises(ValueError, match="input"):
        handler.benchmark("not-a-sequence")
    with pytest.raises(ValueError, match="repetitions"):
        handler.benchmark(["first"], repetitions=0)
    with pytest.raises(ValueError, match="non-empty"):
        handler.predict(" ")
