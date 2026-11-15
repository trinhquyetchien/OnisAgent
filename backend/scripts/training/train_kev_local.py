"""Training script for local Kev Intent Classifier.

Reads:
  - backend/data/splits/kev_train.jsonl (1,380 samples)
  - backend/data/splits/kev_val.jsonl   (175 samples)
Trains the dual-layer calibrated pipeline.
Evaluates on validation split.
Saves model to:
  - backend/models/checkpoints/kev/kev_intent_model.joblib
"""

import json
from pathlib import Path
import joblib
from sklearn.metrics import accuracy_score, classification_report

from src.models.kev.kev_pipeline import build_kev_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints" / "kev"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = SPLITS_DIR / "kev_train.jsonl"
VAL_FILE = SPLITS_DIR / "kev_val.jsonl"
MODEL_PATH = CHECKPOINT_DIR / "kev_intent_model.joblib"


def load_data(file_path: Path):
    texts = []
    labels = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                texts.append(item["input"])
                labels.append(item["target"]["intent"])
    return texts, labels


def main():
    print("==========================================================")
    print("🚀 BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH KEV (FAST PATH INTENT MODEL)")
    print("==========================================================")
    print(f"• File huấn luyện: {TRAIN_FILE}")
    print(f"• File kiểm định:   {VAL_FILE}")

    X_train, y_train = load_data(TRAIN_FILE)
    X_val, y_val = load_data(VAL_FILE)

    print(f"\n📊 Kích thước tập dữ liệu:")
    print(f"  - Số mẫu Train: {len(X_train)}")
    print(f"  - Số mẫu Val:   {len(X_val)}")
    print(f"  - Số lượng nhãn Intent: {len(set(y_train))}")

    print("\n⚙️ Xây dựng pipeline đa tầng và huấn luyện...")
    pipeline = build_kev_pipeline()
    pipeline.fit(X_train, y_train)

    print("✅ Huấn luyện hoàn tất! Đang kiểm tra trên tập Validation...")
    val_preds = pipeline.predict(X_val)
    val_acc = accuracy_score(y_val, val_preds)

    print(f"\n🎯 ĐỘ CHÍNH XÁC TẬP VALIDATION (VAL ACCURACY): {val_acc * 100:.2f}%")
    if val_acc >= 0.90:
        print("  🌟 ĐẠT TIÊU CHUẨN XUẤT SẮC (> 90%)!")
    else:
        print("  ⚠️ Chưa đạt ngưỡng 90%, cần điều chỉnh tham số.")

    # Save model artifact
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\n💾 Đã lưu thành công model checkpoint tại: {MODEL_PATH}")
    print("==========================================================")


if __name__ == "__main__":
    main()
