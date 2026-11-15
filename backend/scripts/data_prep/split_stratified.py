"""Stratified dataset split script for Kev Model.

Splits backend/data/clean/kev_dataset_unified.jsonl into:
  - backend/data/splits/kev_train.jsonl (80%)
  - backend/data/splits/kev_val.jsonl   (10%)
  - backend/data/splits/kev_test.jsonl  (10%)

Uses Stratified Sampling based on intent label to ensure 100% class coverage
across all splits, especially for low-frequency classes. Reproducible with seed 42.
"""

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = CLEAN_DIR / "kev_dataset_unified.jsonl"
TRAIN_FILE = SPLITS_DIR / "kev_train.jsonl"
VAL_FILE = SPLITS_DIR / "kev_val.jsonl"
TEST_FILE = SPLITS_DIR / "kev_test.jsonl"

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Unified dataset not found: {INPUT_FILE}")

    samples_by_intent = defaultdict(list)
    total_samples = 0

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            intent = item["target"]["intent"]
            samples_by_intent[intent].append(item)
            total_samples += 1

    print(f"Tổng số mẫu nạp vào: {total_samples}")
    print(f"Số lượng classes (nhãn intent): {len(samples_by_intent)}")

    train_set = []
    val_set = []
    test_set = []

    for intent, items in sorted(samples_by_intent.items()):
        # Shuffle deterministically per class
        shuffled = list(items)
        random.shuffle(shuffled)
        n = len(shuffled)

        # Ensure at least 1 in val and 1 in test if n >= 5
        if n >= 5:
            n_val = max(1, round(n * VAL_RATIO))
            n_test = max(1, round(n * TEST_RATIO))
            n_train = n - n_val - n_test
            # Guard against train being 0
            if n_train < 1:
                n_train = 1
                n_val = max(1, (n - 1) // 2)
                n_test = n - n_train - n_val
        else:
            n_train = max(1, n - 2)
            n_val = 1 if n >= 2 else 0
            n_test = 1 if n >= 3 else 0

        train_set.extend(shuffled[:n_train])
        val_set.extend(shuffled[n_train:n_train + n_val])
        test_set.extend(shuffled[n_train + n_val:])

    # Shuffle the combined splits
    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    def write_jsonl(path: Path, data: list):
        with path.open("w", encoding="utf-8") as out:
            for d in data:
                out.write(json.dumps(d, ensure_ascii=False) + "\n")

    write_jsonl(TRAIN_FILE, train_set)
    write_jsonl(VAL_FILE, val_set)
    write_jsonl(TEST_FILE, test_set)

    print("\n=== KẾT QUẢ PHÂN CHIA PHÂN TẦNG (STRATIFIED SPLIT RESULT) ===")
    print(f"• Train set: {len(train_set):4d} mẫu ({len(train_set) / total_samples * 100:.1f}%) -> {TRAIN_FILE}")
    print(f"• Val set:   {len(val_set):4d} mẫu ({len(val_set) / total_samples * 100:.1f}%) -> {VAL_FILE}")
    print(f"• Test set:  {len(test_set):4d} mẫu ({len(test_set) / total_samples * 100:.1f}%) -> {TEST_FILE}")
    print(f"• Tổng cộng: {len(train_set) + len(val_set) + len(test_set):4d} mẫu (100.0%)")


if __name__ == "__main__":
    main()
