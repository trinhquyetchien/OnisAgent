"""Generate 75 diverse Vietnamese training utterances for finance.query_debt.

Append to backend/data/clean/kev_dataset_unified.jsonl.
"""

import json
from pathlib import Path

DATASET_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "clean" / "kev_dataset_unified.jsonl"

QUERY_DEBT_SAMPLES = [
    # General queries (all debts)
    ("tôi có nợ ai không", {"debt_type": "borrow"}),
    ("tôi có đang nợ ai không vậy bot", {"debt_type": "borrow"}),
    ("tôi đang nợ những ai", {"debt_type": "borrow"}),
    ("check xem tôi nợ ai", {"debt_type": "borrow"}),
    ("danh sách các khoản nợ của tôi", {"debt_type": "borrow"}),
    ("tôi còn thiếu tiền ai không", {"debt_type": "borrow"}),
    ("kiểm tra các khoản nợ phải trả", {"debt_type": "borrow"}),
    ("tổng tiền tôi đang nợ là bao nhiêu", {"debt_type": "borrow"}),
    ("xem sổ nợ của tôi", {"debt_type": "all"}),
    ("mở sổ ghi nợ xem nào", {"debt_type": "all"}),
    ("danh sách nợ nần hiện tại", {"debt_type": "all"}),
    ("tôi có mượn nợ ai tiền không", {"debt_type": "borrow"}),
    ("xem danh sách các khoản vay nợ cá nhân", {"debt_type": "borrow"}),
    ("danh sách mượn nợ", {"debt_type": "borrow"}),
    ("kiểm tra xem tôi có đang vay tiền ai không", {"debt_type": "borrow"}),
    ("tổng dư nợ hiện tại của tôi", {"debt_type": "borrow"}),
    ("tôi có thiếu nợ ai đồng nào không", {"debt_type": "borrow"}),
    ("cho xem danh sách các chủ nợ", {"debt_type": "borrow"}),
    ("các khoản tôi cần trả nợ trong tháng này", {"debt_type": "borrow"}),
    ("xem lại những ai tôi đang mượn tiền", {"debt_type": "borrow"}),

    # Lending queries (who owes me money)
    ("có ai vay tiền tôi không", {"debt_type": "lend"}),
    ("có ai đang nợ tiền tôi không", {"debt_type": "lend"}),
    ("ai đang mượn tiền tôi", {"debt_type": "lend"}),
    ("ai còn thiếu tiền tôi không", {"debt_type": "lend"}),
    ("danh sách con nợ", {"debt_type": "lend"}),
    ("danh sách những người đang nợ tôi", {"debt_type": "lend"}),
    ("những ai đang vay tiền của tôi", {"debt_type": "lend"}),
    ("kiểm tra xem ai nợ tiền tôi", {"debt_type": "lend"}),
    ("xem danh sách cho mượn tiền", {"debt_type": "lend"}),
    ("hôm nay có khoản nợ nào cần đòi không", {"debt_type": "lend"}),
    ("tổng tiền người ta nợ tôi là bao nhiêu", {"debt_type": "lend"}),
    ("danh sách những người tôi cho vay", {"debt_type": "lend"}),
    ("những ai mượn tiền tôi chưa trả", {"debt_type": "lend"}),
    ("ai chưa trả tiền tôi vậy", {"debt_type": "lend"}),
    ("xem các khoản cho mượn chưa thu hồi", {"debt_type": "lend"}),
    ("tiền cho mượn còn bao nhiêu chưa đòi được", {"debt_type": "lend"}),
    ("check xem còn ai thiếu nợ tôi không bot ơi", {"debt_type": "lend"}),
    ("danh sách các khoản cho vay cá nhân", {"debt_type": "lend"}),
    ("ai đang giữ tiền của tôi chưa trả", {"debt_type": "lend"}),
    ("tổng số tiền cho bạn bè mượn hiện tại", {"debt_type": "lend"}),

    # Specific person queries
    ("thằng Tuấn có nợ tôi đồng nào không", {"debt_type": "lend", "person": "Tuấn"}),
    ("Hải còn nợ tôi tiền không", {"debt_type": "lend", "person": "Hải"}),
    ("Lan có đang mượn tiền tôi không", {"debt_type": "lend", "person": "Lan"}),
    ("check nợ của Nam", {"debt_type": "all", "person": "Nam"}),
    ("thằng Huy còn thiếu tôi bao nhiêu tiền", {"debt_type": "lend", "person": "Huy"}),
    ("tôi có nợ tiền anh Hùng không", {"debt_type": "borrow", "person": "anh Hùng"}),
    ("tôi có nợ gì chị Thảo không", {"debt_type": "borrow", "person": "chị Thảo"}),
    ("kiểm tra nợ với Hoàng", {"debt_type": "all", "person": "Hoàng"}),
    ("bạn cùng phòng còn nợ tôi tiền phòng không", {"debt_type": "lend", "person": "bạn cùng phòng"}),
    ("thằng bạn thân có nợ tôi không", {"debt_type": "lend", "person": "bạn thân"}),
    ("check xem tôi nợ Tuấn bao nhiêu", {"debt_type": "borrow", "person": "Tuấn"}),
    ("Hương đã trả hết nợ cho tôi chưa", {"debt_type": "lend", "person": "Hương"}),
    ("khoản nợ của Minh thế nào rồi", {"debt_type": "all", "person": "Minh"}),
    ("Linh còn nợ tiền trà sữa không", {"debt_type": "lend", "person": "Linh"}),
    ("tôi có đang mượn tiền mẹ không", {"debt_type": "borrow", "person": "mẹ"}),

    # Natural conversation / colloquial variations
    ("xem sổ nợ nần ai nợ ai", {"debt_type": "all"}),
    ("tổng hợp nợ nần giúp tôi", {"debt_type": "all"}),
    ("ai nợ ai mượn gì xem hết đi", {"debt_type": "all"}),
    ("tra cứu sổ nợ chi tiết", {"debt_type": "all"}),
    ("xem tình hình vay mượn tiền", {"debt_type": "all"}),
    ("check tình hình nợ nần tháng này", {"debt_type": "all"}),
    ("có đứa nào mượn tiền chưa trả không bot", {"debt_type": "lend"}),
    ("đứa nào đang nợ tiền tao", {"debt_type": "lend"}),
    ("tao có đang nợ tiền ai không", {"debt_type": "borrow"}),
    ("xem danh sách ai vay tiền", {"debt_type": "lend"}),
    ("xem danh sách ai mượn nợ", {"debt_type": "all"}),
    ("hỏi xem có ai nợ tôi tiền không", {"debt_type": "lend"}),
    ("cho hỏi tôi có đang vay nợ ai không", {"debt_type": "borrow"}),
    ("báo cáo các khoản nợ cần thu và cần trả", {"debt_type": "all"}),
    ("xem tiền cho mượn và tiền đi vay", {"debt_type": "all"}),
    ("check dư nợ với bạn bè", {"debt_type": "all"}),
    ("danh sách người vay tiền của mình", {"debt_type": "lend"}),
    ("mình có đang nợ ai đồng nào không ta", {"debt_type": "borrow"}),
    ("kiểm tra xem ai đang vay nợ tôi", {"debt_type": "lend"}),
    ("danh sách những ai đang nợ tiền mình", {"debt_type": "lend"}),
    ("xem ai đang mượn tiền của tôi", {"debt_type": "lend"}),
    ("có ai đang thiếu tiền tôi không", {"debt_type": "lend"}),
    ("cho xem danh sách các khoản nợ", {"debt_type": "all"}),
    ("tôi có nợ ai tiền không nhỉ", {"debt_type": "borrow"}),
    ("tra cứu danh sách người nợ tiền", {"debt_type": "lend"}),
]


def main():
    print(f"Adding {len(QUERY_DEBT_SAMPLES)} samples for 'finance.query_debt'...")
    new_records = []
    for text, slots in QUERY_DEBT_SAMPLES:
        rec = {
            "input": text,
            "target": {
                "intent": "finance.query_debt",
                "confidence": 0.98,
                "route": "FAST_PATH",
                "slots": slots,
            },
        }
        new_records.append(rec)

    with DATASET_FILE.open("a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Successfully appended {len(new_records)} samples to {DATASET_FILE}")


if __name__ == "__main__":
    main()
