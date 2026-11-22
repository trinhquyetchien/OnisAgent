"""Dataset Integrity & Leakage Verification Script for Kev Splits.

Validates:
1. Total sample counts in train, val, and test.
2. 0% Data leakage (no input overlap between train, val, test).
3. 100% Intent Class coverage (every intent appears in all three splits).
4. Stratified balance distribution.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

TRAIN_FILE = SPLITS_DIR / "kev_train.jsonl"
VAL_FILE = SPLITS_DIR / "kev_val.jsonl"
TEST_FILE = SPLITS_DIR / "kev_test.jsonl"
EXTERNAL_FILE = SPLITS_DIR / "external_eval_benchmark.jsonl"


def load_split(path: Path) -> list[dict]:
    if not path.exists():
        print(f"Lỗi: Không tìm thấy file {path}")
        sys.exit(1)
    samples = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def main():
    train_data = load_split(TRAIN_FILE)
    val_data = load_split(VAL_FILE)
    test_data = load_split(TEST_FILE)
    external_data = load_split(EXTERNAL_FILE)

    total = len(train_data) + len(val_data) + len(test_data)
    print("=================================================================")
    print("📊 BÁO CÁO TOÀN VẸN DỮ LIỆU KEV DATASET (DATA INTEGRITY REPORT)")
    print("=================================================================")
    print(f"• Tập Huấn Luyện (Train): {len(train_data):4d} mẫu ({len(train_data)/total*100:.1f}%)")
    print(f"• Tập Kiểm Định (Val):    {len(val_data):4d} mẫu ({len(val_data)/total*100:.1f}%)")
    print(f"• Tập Kiểm Thử (Test):    {len(test_data):4d} mẫu ({len(test_data)/total*100:.1f}%)")
    print(f"• Tổng Cộng:              {total:4d} mẫu (100.0%)")

    # 1. Kiểm tra rò rỉ dữ liệu (Data Leakage)
    train_inputs = {x["input"].strip().lower() for x in train_data}
    val_inputs = {x["input"].strip().lower() for x in val_data}
    test_inputs = {x["input"].strip().lower() for x in test_data}
    external_inputs = {x["input"].strip().lower() for x in external_data}

    leakage_train_test = train_inputs.intersection(test_inputs)
    leakage_train_val = train_inputs.intersection(val_inputs)
    leakage_val_test = val_inputs.intersection(test_inputs)
    leakage_train_external = train_inputs.intersection(external_inputs)
    leakage_val_external = val_inputs.intersection(external_inputs)
    leakage_test_external = test_inputs.intersection(external_inputs)

    has_leakage = bool(
        leakage_train_test
        or leakage_train_val
        or leakage_val_test
        or leakage_train_external
        or leakage_val_external
        or leakage_test_external
    )
    print("\n🔍 1. KIỂM TRA RÒ RỈ DỮ LIỆU (DATA LEAKAGE CHECK):")
    if not has_leakage:
        print("  ✅ TUYỆT VỜI: 0% Data Leakage! Không có sample nào trùng giữa train/val/test và external holdout.")
    else:
        print(
            "  ❌ CẢNH BÁO LEAKAGE: "
            f"Train-Test: {len(leakage_train_test)}, "
            f"Train-Val: {len(leakage_train_val)}, "
            f"Val-Test: {len(leakage_val_test)}, "
            f"Train-External: {len(leakage_train_external)}, "
            f"Val-External: {len(leakage_val_external)}, "
            f"Test-External: {len(leakage_test_external)}"
        )

    # 2. Kiểm tra độ phủ Intent Classes (Coverage)
    train_classes = {x["target"]["intent"] for x in train_data}
    val_classes = {x["target"]["intent"] for x in val_data}
    test_classes = {x["target"]["intent"] for x in test_data}
    all_classes = train_classes.union(val_classes).union(test_classes)

    print(f"\n🎯 2. KIỂM TRA ĐỘ PHỦ INTENT (INTENT COVERAGE - {len(all_classes)} CLASSES):")
    missing_in_train = all_classes - train_classes
    missing_in_val = all_classes - val_classes
    missing_in_test = all_classes - test_classes

    if not missing_in_train and not missing_in_val and not missing_in_test:
        print(f"  ✅ HOÀN HẢO: 100% ({len(all_classes)}/{len(all_classes)}) các Intent đều có mặt trong cả 3 tập Train, Val, Test!")
    else:
        print(f"  ⚠️ Thiếu trong Train: {missing_in_train}")
        print(f"  ⚠️ Thiếu trong Val: {missing_in_val}")
        print(f"  ⚠️ Thiếu trong Test: {missing_in_test}")

    # 3. Phân bổ chi tiết từng Intent
    intent_counts = defaultdict(lambda: {"train": 0, "val": 0, "test": 0, "total": 0})
    for x in train_data:
        i = x["target"]["intent"]
        intent_counts[i]["train"] += 1
        intent_counts[i]["total"] += 1
    for x in val_data:
        i = x["target"]["intent"]
        intent_counts[i]["val"] += 1
        intent_counts[i]["total"] += 1
    for x in test_data:
        i = x["target"]["intent"]
        intent_counts[i]["test"] += 1
        intent_counts[i]["total"] += 1

    print("\n📈 3. PHÂN BỔ CHI TIẾT TỪNG NHÃN (STRATIFIED SAMPLES PER SPLIT):")
    print(f"  {'TÊN INTENT':32} | {'TRAIN':>6} | {'VAL':>5} | {'TEST':>5} | {'TỔNG':>6}")
    print("  " + "-" * 62)
    for intent, c in sorted(intent_counts.items(), key=lambda x: -x[1]["total"]):
        print(f"  {intent:32} | {c['train']:6d} | {c['val']:5d} | {c['test']:5d} | {c['total']:6d}")

    print("=================================================================\n")
    if not has_leakage and not missing_in_train and not missing_in_val and not missing_in_test:
        print("🎉 TẤT CẢ TIÊU CHUẨN DỮ LIỆU ĐỀU ĐẠT CHUẨN XUẤT SẮC ĐỂ HUẤN LUYỆN KEV MODEL!")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
