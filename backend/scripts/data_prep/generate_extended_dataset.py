"""Synthetic & Extended Dataset Generator for OnisAgent.

Generates 1,200+ realistic Vietnamese training samples covering 27 intents
across Finance, Task, Cross-domain, and System.
Outputs to: backend/data/clean/kev_dataset_extended.jsonl
"""

import json
import random
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "clean"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = DATA_DIR / "kev_dataset_extended.jsonl"

# ----------------- VOCABULARY & SLANG BANK -----------------
MONEY_SLANG = [
    ("15k", 15000), ("20k", 20000), ("25k", 25000), ("30k", 30000), ("35 nghìn", 35000),
    ("40k", 40000), ("45k", 45000), ("50 nghìn", 50000), ("60k", 60000), ("75k", 75000),
    ("80 ngàn", 80000), ("100k", 100000), ("120k", 120000), ("150k", 150000),
    ("1 xị", 100000), ("2 xị", 200000), ("3 xị", 300000), ("5 xị", 500000),
    ("1 lít", 100000), ("2 lít", 200000), ("5 lít", 500000),
    ("1 củ", 1000000), ("1 củ rưỡi", 1500000), ("2 củ", 2000000), ("3 củ", 3000000),
    ("3 củ rưỡi", 3500000), ("5 củ", 5000000), ("10 củ", 10000000), ("15 củ", 15000000),
    ("20 củ", 20000000), ("50 củ", 50000000), ("100 củ", 100000000),
    ("1tr2", 1200000), ("1tr5", 1500000), ("2tr", 2000000), ("2tr5", 2500000),
    ("3 triệu", 3000000), ("4 triệu rưỡi", 4500000), ("5 triệu", 5000000),
    ("8 triệu", 8000000), ("10 triệu", 10000000), ("12 triệu", 12000000),
    ("15 triệu", 15000000), ("20 triệu", 20000000), ("25 triệu", 25000000),
    ("50 triệu", 50000000), ("100 triệu", 100000000), ("200 triệu", 200000000),
    ("500 triệu", 500000000), ("1 tỷ", 1000000000), ("2 tỷ", 2000000000)
]

ACCOUNTS = ["Vietcombank", "Momo", "MB Bank", "tiền mặt", "ZaloPay", "ShopeePay", "Techcombank", "VPBank"]
PEOPLE = ["thằng Nam", "anh Tuấn", "chị Lan", "con Hằng", "bạn cùng phòng", "thằng Huy", "bác chủ trọ", "mẹ", "bố", "Hải"]
TIME_SLANG = ["sáng nay", "trưa nay", "chiều nay", "tối nay", "mai", "ngày mai", "mốt", "ngày mốt", "tuần này", "tuần sau", "thứ Hai tới", "cuối tuần"]

EXPENSE_ITEMS = [
    ("trà sữa", "đồ uống"), ("cà phê muối", "đồ uống"), ("bún bò", "ăn uống"), ("phở gà", "ăn uống"),
    ("cơm tấm", "ăn uống"), ("tiền điện", "hóa đơn"), ("tiền nước", "hóa đơn"), ("tiền mạng wifi", "hóa đơn"),
    ("tiền phòng trọ", "nhà ở"), ("đổ xăng", "di chuyển"), ("vé xem phim", "giải trí"), ("mua áo sơ mi", "mua sắm"),
    ("mua giày sneaker", "mua sắm"), ("đi siêu thị Winmart", "ăn uống"), ("bánh mì thịt", "ăn uống"),
    ("gọi GrabCar", "di chuyển"), ("mua sách chuyên ngành", "giáo dục"), ("thuốc tây đau đầu", "sức khỏe")
]

INCOME_SOURCES = ["lương tháng", "thưởng dự án", "tiền freelance", "bố mẹ cho", "bán đồ cũ", "cổ tức", "tiền tip", "thắng kèo game"]

TASKS_POOL = [
    ("nộp slide đồ án AI4Life", "Học tập"), ("gửi báo cáo tài chính cho sếp", "Công ty"),
    ("họp nhóm dự án OnisAgent", "AI4Life"), ("đi khám răng định kỳ", "Sức khỏe"),
    ("tập gym ngực vai", "Cá nhân"), ("mua sữa tươi cho gia đình", "Gia đình"),
    ("đóng học phí kỳ 1", "Học tập"), ("gọi điện hỏi thăm bố mẹ", "Cá nhân"),
    ("viết tài liệu kỹ thuật backend", "Công việc"), ("sửa lỗi responsive trên mobile", "Công việc"),
    ("đọc 2 chương sách tâm lý", "Phát triển bản thân"), ("dọn dẹp phòng trọ cuối tuần", "Cá nhân")
]


def gen_samples() -> list[dict]:
    samples = []

    # 1. finance.get_balance (50 samples)
    for _ in range(50):
        acc = random.choice(ACCOUNTS + ["all", "tất cả"])
        template = random.choice([
            f"Số dư hiện tại của {acc} còn bao nhiêu?",
            f"Ví {acc} còn tiền không em?",
            f"Kiểm tra số dư tài khoản {acc}",
            f"Cho xem tổng tài sản hiện có trong {acc}",
            f"{acc} còn lại nhiêu tiền thế",
            f"Check số dư khả dụng {acc}",
            f"Tài chính hiện tại của tôi trong {acc} ra sao",
        ])
        slots = {"account": "all" if acc in ["all", "tất cả"] else acc}
        samples.append({
            "input": template,
            "target": {"intent": "finance.get_balance", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 2. finance.add_expense (100 samples)
    for _ in range(100):
        item, cat = random.choice(EXPENSE_ITEMS)
        money_str, money_val = random.choice(MONEY_SLANG[:25])
        t_str = random.choice(TIME_SLANG[:5])
        acc = random.choice(ACCOUNTS)
        template = random.choice([
            f"Chi {money_str} {item}",
            f"{t_str} vừa mua {item} hết {money_str}",
            f"Đã trả {money_str} tiền {item} qua {acc}",
            f"Vừa tiêu {money_str} cho {item}",
            f"Mới quẹt thẻ {money_str} {item}",
            f"Ghi sổ chi {item} {money_str}",
            f"Vừa thanh toán {item} {money_str} bằng {acc}",
            f"Hết {money_str} tiền {item} rồi",
        ])
        slots = {"amount": money_val, "category": cat, "note": item, "account": acc}
        samples.append({
            "input": template,
            "target": {"intent": "finance.add_expense", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 3. finance.add_income (70 samples)
    for _ in range(70):
        src = random.choice(INCOME_SOURCES)
        money_str, money_val = random.choice(MONEY_SLANG[15:40])
        acc = random.choice(ACCOUNTS)
        template = random.choice([
            f"Nhận {src} {money_str} rồi nè",
            f"Vừa được chuyển {money_str} tiền {src} vào {acc}",
            f"Thu về {money_str} từ {src}",
            f"Hôm nay kiếm được {money_str} {src}",
            f"Cộng {money_str} vào ví {acc} do {src}",
            f"Được thưởng {money_str} tiền {src}",
            f"Tiền {src} đã về {money_str}",
        ])
        slots = {"amount": money_val, "source": src, "account": acc}
        samples.append({
            "input": template,
            "target": {"intent": "finance.add_income", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 4. finance.transfer (50 samples)
    for _ in range(50):
        acc1, acc2 = random.sample(ACCOUNTS, 2)
        money_str, money_val = random.choice(MONEY_SLANG[:25])
        template = random.choice([
            f"Chuyển {money_str} từ {acc1} sang {acc2} giúp mình",
            f"Bắn {money_str} từ {acc1} qua {acc2}",
            f"Rút {money_str} từ {acc1} về {acc2}",
            f"Nạp {money_str} vào {acc2} từ {acc1}",
            f"Chuyển tiền nội bộ {money_str} từ {acc1} đến {acc2}",
        ])
        slots = {"amount": money_val, "from_account": acc1, "to_account": acc2}
        samples.append({
            "input": template,
            "target": {"intent": "finance.transfer", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 5. finance.record_debt (50 samples)
    for _ in range(50):
        person = random.choice(PEOPLE)
        money_str, money_val = random.choice(MONEY_SLANG[:25])
        is_lend = random.choice([True, False])
        if is_lend:
            template = random.choice([
                f"Cho {person} mượn {money_str} hẹn cuối tuần trả",
                f"Ghi sổ cho {person} vay {money_str}",
                f"{person} mượn {money_str} tiền ăn trưa",
                f"Vừa cho {person} mượn {money_str}",
            ])
            dtype = "lend"
        else:
            template = random.choice([
                f"Mượn {person} {money_str} mua đồ mai trả",
                f"Vay {person} {money_str} đóng tiền nhà",
                f"Mới mượn {person} {money_str}",
            ])
            dtype = "borrow"
        slots = {"amount": money_val, "person": person, "debt_type": dtype}
        samples.append({
            "input": template,
            "target": {"intent": "finance.record_debt", "confidence": 0.96, "route": "FAST_PATH", "slots": slots}
        })

    # 6. finance.debt_repay (50 samples)
    for _ in range(50):
        person = random.choice(PEOPLE)
        money_str, money_val = random.choice(MONEY_SLANG[:25])
        template = random.choice([
            f"{person} vừa trả {money_str} tiền nợ hôm bữa",
            f"Đã trả {money_str} cho {person}",
            f"Thu nợ {money_str} từ {person}",
            f"Thanh toán nợ {money_str} cho {person} xong rồi",
            f"{person} gửi lại {money_str} tiền mượn",
        ])
        slots = {"amount": money_val, "person": person}
        samples.append({
            "input": template,
            "target": {"intent": "finance.debt_repay", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 7. finance.split_bill (50 samples)
    for _ in range(50):
        money_str, money_val = random.choice(MONEY_SLANG[10:30])
        num = random.randint(2, 8)
        item, _ = random.choice(EXPENSE_ITEMS)
        template = random.choice([
            f"Hóa đơn {item} {money_str} chia đều cho {num} người",
            f"Tiền {item} hết {money_str} share cho {num} đứa",
            f"Chia tiền {item} {money_str} cho {num} người thì mỗi người bao nhiêu",
            f"Ăn {item} hết {money_str} chia {num}",
        ])
        slots = {"total_amount": money_val, "members_count": num, "description": item}
        samples.append({
            "input": template,
            "target": {"intent": "finance.split_bill", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 8. finance.pay_bill (50 samples)
    for _ in range(50):
        bill_type = random.choice(["tiền điện", "tiền nước", "tiền internet", "tiền trọ", "tiền học phí", "tiền rác"])
        money_str, money_val = random.choice(MONEY_SLANG[5:35])
        template = random.choice([
            f"Đóng {bill_type} tháng này hết {money_str}",
            f"Vừa thanh toán hóa đơn {bill_type} {money_str}",
            f"Nộp {bill_type} {money_str} qua banking",
            f"Đã đóng {bill_type} {money_str}",
        ])
        slots = {"amount": money_val, "bill_type": bill_type}
        samples.append({
            "input": template,
            "target": {"intent": "finance.pay_bill", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 9. finance.query_transactions (50 samples)
    for _ in range(50):
        cat = random.choice(["cà phê", "ăn uống", "mua sắm", "đi lại", "hóa đơn"])
        t = random.choice(["tuần này", "tháng này", "hôm qua", "tuần trước", "tháng trước"])
        template = random.choice([
            f"{t.capitalize()} tôi chi bao nhiêu tiền cho {cat} rồi?",
            f"Xem lịch sử chi tiêu {cat} {t}",
            f"Kiểm tra các khoản tiêu cho {cat} {t}",
            f"Liệt kê các giao dịch {cat} trong {t}",
            f"Thống kê tiền {cat} {t} qua",
        ])
        slots = {"category": cat, "time_range": t}
        samples.append({
            "input": template,
            "target": {"intent": "finance.query_transactions", "confidence": 0.96, "route": "FAST_PATH", "slots": slots}
        })

    # 10. finance.budget_plan (45 samples)
    for _ in range(45):
        money_str, money_val = random.choice(MONEY_SLANG[15:35])
        cat = random.choice(["ăn uống", "mua sắm", "tổng thể", "giải trí"])
        template = random.choice([
            f"Đặt hạn mức chi tiêu tháng này là {money_str}",
            f"Kiểm tra ngân sách {cat} tuần này còn bao nhiêu",
            f"Cài đặt ngân sách {cat} tối đa {money_str} một tháng",
            f"Giới hạn chi tiêu {cat} dưới {money_str}",
            f"Lập kế hoạch ngân sách {cat} {money_str}",
        ])
        slots = {"limit_amount": money_val, "category": cat, "period": "this_month"}
        samples.append({
            "input": template,
            "target": {"intent": "finance.budget_plan", "confidence": 0.95, "route": "REASONING_PATH", "slots": slots}
        })

    # 11. finance.update_budget (35 samples)
    for _ in range(35):
        money_str, money_val = random.choice(MONEY_SLANG[15:35])
        cat = random.choice(["ăn uống", "mua sắm", "tổng thể"])
        template = random.choice([
            f"Tăng ngân sách {cat} lên {money_str}",
            f"Giảm hạn mức {cat} xuống còn {money_str}",
            f"Chỉnh lại ngân sách {cat} thành {money_str}",
            f"Thay đổi hạn mức chi tiêu {cat} {money_str}",
        ])
        slots = {"category": cat, "new_limit": money_val}
        samples.append({
            "input": template,
            "target": {"intent": "finance.update_budget", "confidence": 0.96, "route": "FAST_PATH", "slots": slots}
        })

    # 12. finance.loan_installment_plan (50 samples)
    for _ in range(50):
        money_str, money_val = random.choice(MONEY_SLANG[25:])
        months = random.choice([6, 12, 18, 24, 36, 48])
        rate = random.choice([8, 9, 10, 11, 12, 14])
        purpose = random.choice(["mua xe", "mua laptop", "sửa nhà", "mua điện thoại"])
        template = random.choice([
            f"Tính kế hoạch trả góp {purpose} {money_str} trong {months} tháng lãi {rate}%",
            f"Vay {money_str} trả góp {months} tháng lãi {rate}%/năm mỗi tháng trả bao nhiêu",
            f"Dự toán bảng nợ vay {money_str} kỳ hạn {months} tháng lãi suất {rate}% dư nợ giảm dần",
            f"Bảng trả góp {purpose} {money_str} chia {months} tháng",
        ])
        slots = {"principal": money_val, "term_months": months, "annual_rate": rate / 100, "method": "reducing_balance", "purpose": purpose}
        samples.append({
            "input": template,
            "target": {"intent": "finance.loan_installment_plan", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 13. finance.savings_goal (50 samples)
    for _ in range(50):
        money_str, money_val = random.choice(MONEY_SLANG[20:45])
        goal = random.choice(["mua xe máy", "mua iPhone", "quỹ khẩn cấp", "du lịch Nhật", "mua laptop mới", "cưới vợ"])
        template = random.choice([
            f"Tạo quỹ tiết kiệm {goal} {money_str}",
            f"Tôi muốn để dành {money_str} để {goal}",
            f"Đặt mục tiêu tích lũy {money_str} cho {goal}",
            f"Mở hũ tiết kiệm {goal} mục tiêu {money_str}",
            f"Thêm kế hoạch tiết kiệm {goal} {money_str}",
        ])
        slots = {"goal_name": goal, "target_amount": money_val}
        samples.append({
            "input": template,
            "target": {"intent": "finance.savings_goal", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 14. finance.financial_report (45 samples)
    for _ in range(45):
        t = random.choice(["tháng này", "tuần này", "tháng vừa rồi", "quý này"])
        template = random.choice([
            f"Báo cáo tài chính {t} của tôi thế nào?",
            f"Tháng này tôi phung phí ở đâu nhiều nhất?",
            f"Phân tích tỷ trọng chi tiêu {t} giúp mình",
            f"Đánh giá sức khỏe tài chính và dòng tiền {t}",
            f"Tổng kết tình hình thu chi {t} xem có dư không",
            f"Cố vấn cách cắt giảm chi tiêu {t}",
        ])
        slots = {"period": t}
        samples.append({
            "input": template,
            "target": {"intent": "finance.financial_report", "confidence": 0.96, "route": "REASONING_PATH", "slots": slots}
        })

    # 15. task.create (100 samples)
    for _ in range(100):
        task, cat = random.choice(TASKS_POOL)
        t = random.choice(TIME_SLANG)
        p = random.choice(["gấp", "quan trọng", "bình thường", "ưu tiên cao"])
        template = random.choice([
            f"Thêm việc {task} {t}",
            f"Nhắc tôi {task} vào {t}",
            f"Tạo task {task} mức độ {p}",
            f"Ghi chú việc {task} hạn chót {t}",
            f"Lên lịch {task} giúp mình",
            f"Thêm nhiệm vụ mới: {task}",
            f"Tạo công việc {task}",
        ])
        slots = {"title": task, "deadline": t, "category": cat}
        samples.append({
            "input": template,
            "target": {"intent": "task.create", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 16. task.create_recurring (45 samples)
    for _ in range(45):
        habit = random.choice(["đi tập gym", "đọc sách 30 phút", "uống thuốc", "học tiếng Anh", "dọn phòng", "chạy bộ"])
        freq = random.choice(["mỗi ngày", "thứ 2 4 6", "mỗi tối lúc 22h", "mỗi sáng 7h", "hàng tuần"])
        template = random.choice([
            f"Nhắc tôi {habit} vào {freq}",
            f"Thêm thói quen {habit} {freq}",
            f"Đặt lịch lặp lại {habit} {freq}",
            f"Lên lịch định kỳ {habit} {freq}",
        ])
        slots = {"title": habit, "recurrence": freq}
        samples.append({
            "input": template,
            "target": {"intent": "task.create_recurring", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 17. task.query_today (50 samples)
    for _ in range(50):
        template = random.choice([
            "Hôm nay tôi có những việc gì cần làm?",
            "Lên danh sách việc hôm nay",
            "Xem task ngày hôm nay của tôi",
            "Hôm nay có việc gì gấp không Onis",
            "Cho xem danh sách to-do list hôm nay",
            "Lịch làm việc hôm nay thế nào",
            "Check task ngày hôm nay",
            "Còn những việc nào chưa làm xong hôm nay",
        ])
        samples.append({
            "input": template,
            "target": {"intent": "task.query_today", "confidence": 0.98, "route": "FAST_PATH", "slots": {"date_filter": "today", "status": "pending"}}
        })

    # 18. task.query_deadline (50 samples)
    for _ in range(50):
        template = random.choice([
            "Tuần này có deadline nào gấp không?",
            "Hạn nộp đồ án VKU là khi nào?",
            "Kiểm tra các deadline sắp tới trong 3 ngày tới",
            "Có bài tập nào sắp hết hạn nộp không em",
            "Xem những hạn chót cần làm gấp trong 24h tới",
            "Deadline bài báo khoa học còn bao lâu nữa",
            "Check xem có việc nào sắp quá hạn không",
            "Liệt kê các hạn chót chưa hoàn thành",
        ])
        samples.append({
            "input": template,
            "target": {"intent": "task.query_deadline", "confidence": 0.97, "route": "FAST_PATH", "slots": {"time_range": "upcoming_48h"}}
        })

    # 19. task.query_by_tag (40 samples)
    for _ in range(40):
        tag = random.choice(["AI4Life", "VKU", "Học tập", "Cá nhân", "Đồ án", "Công ty"])
        template = random.choice([
            f"Xem các công việc thuộc dự án {tag}",
            f"Lọc danh sách việc môn {tag}",
            f"Có những task nào gắn nhãn {tag}",
            f"Kiểm tra các việc trong nhóm {tag}",
            f"Liệt kê danh sách việc tag {tag}",
        ])
        slots = {"tag": tag}
        samples.append({
            "input": template,
            "target": {"intent": "task.query_by_tag", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 20. task.query_completed (40 samples)
    for _ in range(40):
        t = random.choice(["hôm nay", "tuần này", "hôm qua", "tháng này"])
        template = random.choice([
            f"Xem lại các việc tôi đã hoàn thành {t}",
            f"{t.capitalize()} tôi đã làm xong được bao nhiêu task?",
            f"Kiểm tra danh sách công việc đã hoàn tất trong {t}",
            f"Cho xem lịch sử các task đã done {t}",
            f"Hôm nay đã làm được những gì rồi Onis",
        ])
        slots = {"time_range": t}
        samples.append({
            "input": template,
            "target": {"intent": "task.query_completed", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 21. task.schedule_event (45 samples)
    for _ in range(45):
        event = random.choice(["cà phê với anh Tuấn", "họp nhóm lab AI", "gặp thầy hướng dẫn", "phỏng vấn thực tập", "đá bóng cty"])
        t = random.choice(["9h sáng mai", "14h chiều thứ 2", "15h30 chiều thứ 5", "10h sáng thứ Sáu", "19h tối mốt"])
        loc = random.choice(["Highlands", "Lab VKU", "Google Meet", "sân bóng", "quán ăn"])
        template = random.choice([
            f"Đặt lịch hẹn {event} lúc {t}",
            f"Lên lịch {event} {t} tại {loc}",
            f"Hẹn {event} lúc {t}",
            f"Thêm lịch hẹn {event} vào {t}",
        ])
        slots = {"title": event, "start_time": t, "location": loc}
        samples.append({
            "input": template,
            "target": {"intent": "task.schedule_event", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 22. task.reschedule (40 samples)
    for _ in range(40):
        task, _ = random.choice(TASKS_POOL)
        t = random.choice(["20h tối mai", "15h chiều thứ 4", "Chủ nhật tuần này", "ngày mốt"])
        template = random.choice([
            f"Dời deadline {task} sang {t}",
            f"Hoãn {task} sang {t}",
            f"Lùi lịch {task} lại sang {t}",
            f"Đổi hạn nộp {task} thành {t}",
            f"Chuyển thời gian {task} sang {t}",
        ])
        slots = {"title": task, "new_deadline": t}
        samples.append({
            "input": template,
            "target": {"intent": "task.reschedule", "confidence": 0.96, "route": "FAST_PATH", "slots": slots}
        })

    # 23. task.plan_schedule (45 samples)
    for _ in range(45):
        t = random.choice(["tuần tới", "ngày mai", "hôm nay", "thứ 7"])
        template = random.choice([
            f"Lên kế hoạch công việc cho {t} giúp mình",
            f"Sắp xếp thứ tự ưu tiên các việc {t} theo ma trận Eisenhower",
            f"Lập lịch trình làm việc {t} sao cho hiệu quả",
            f"Tối ưu hóa thời gian biểu {t} để kịp deadline",
            f"Hôm nay có nhiều task quá, nên làm việc gì trước",
            f"Gợi ý thời gian biểu làm việc {t}",
        ])
        slots = {"time_frame": t}
        samples.append({
            "input": template,
            "target": {"intent": "task.plan_schedule", "confidence": 0.96, "route": "REASONING_PATH", "slots": slots}
        })

    # 24. task.complete (50 samples)
    for _ in range(50):
        task, _ = random.choice(TASKS_POOL)
        template = random.choice([
            f"Xong task {task} rồi nhé",
            f"Đánh dấu hoàn thành việc {task} giúp mình",
            f"Đã làm xong {task}",
            f"Tick xong task {task}",
            f"Hoàn tất {task} rồi nè",
            f"Check done {task}",
        ])
        slots = {"title": task}
        samples.append({
            "input": template,
            "target": {"intent": "task.complete", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 25. task.cancel (40 samples)
    for _ in range(40):
        task, _ = random.choice(TASKS_POOL)
        template = random.choice([
            f"Hủy cuộc họp {task} chiều nay do bận",
            f"Tạm hoãn việc {task} sang tuần sau",
            f"Bỏ task {task} đi không cần làm nữa",
            f"Hủy {task} hôm nay nhé",
        ])
        slots = {"title": task}
        samples.append({
            "input": template,
            "target": {"intent": "task.cancel", "confidence": 0.96, "route": "FAST_PATH", "slots": slots}
        })

    # 26. task.delete (45 samples)
    for _ in range(45):
        task, _ = random.choice(TASKS_POOL)
        template = random.choice([
            f"Xóa task {task} khỏi danh sách",
            f"Xóa vĩnh viễn việc {task}",
            f"Xóa bỏ công việc {task}",
            f"Delete task {task}",
            f"Xóa nhiệm vụ {task} giùm",
        ])
        slots = {"title": task, "requires_hitl": True}
        samples.append({
            "input": template,
            "target": {"intent": "task.delete", "confidence": 0.98, "route": "FAST_PATH", "slots": slots}
        })

    # 27. task.search (35 samples)
    for _ in range(35):
        kw = random.choice(["slide", "báo cáo", "tiền điện", "anh Tuấn", "học phí", "AI4Life", "vé máy bay"])
        template = random.choice([
            f"Tìm các công việc có chữ {kw}",
            f"Tìm kiếm task liên quan đến {kw}",
            f"Tra cứu việc có từ khóa {kw}",
            f"Tìm xem tôi có ghi việc {kw} không",
        ])
        slots = {"keyword": kw}
        samples.append({
            "input": template,
            "target": {"intent": "task.search", "confidence": 0.96, "route": "FAST_PATH", "slots": slots}
        })

    # 28. cross.plan_expense_task (40 samples)
    for _ in range(40):
        event = random.choice(["đi du lịch Đà Nẵng 3 ngày 2 đêm", "tổ chức tiệc sinh nhật", "tổ chức workshop AI", "chuyển phòng trọ mới"])
        money_str, money_val = random.choice(MONEY_SLANG[15:35])
        template = random.choice([
            f"Lập kế hoạch {event} ngân sách {money_str}",
            f"Lên danh sách việc cần làm và dự trù chi phí {event} {money_str}",
            f"Lập plan {event} kinh phí {money_str}",
            f"Kế hoạch {event} và tính toán chi phí {money_str}",
        ])
        slots = {"event_name": event, "budget": money_val}
        samples.append({
            "input": template,
            "target": {"intent": "cross.plan_expense_task", "confidence": 0.95, "route": "REASONING_PATH", "slots": slots}
        })

    # 29. cross.bill_due_reminder (40 samples)
    for _ in range(40):
        bill = random.choice(["tiền trọ", "tiền điện", "tiền mạng", "học phí", "tiền thẻ tín dụng"])
        money_str, money_val = random.choice(MONEY_SLANG[10:35])
        t = random.choice(["ngày 20", "ngày mai", "cuối tháng", "thứ 6 tới", "ngày 25"])
        template = random.choice([
            f"Nhắc tôi đóng {bill} {money_str} vào {t}",
            f"Tạo lịch nhắc nộp {bill} {money_str} trước {t}",
            f"Đặt lịch nhắc thanh toán {bill} {money_str} {t}",
            f"Nhắc chuyển khoản {bill} {money_str} {t}",
        ])
        slots = {"bill_name": bill, "amount": money_val, "due_date": t}
        samples.append({
            "input": template,
            "target": {"intent": "cross.bill_due_reminder", "confidence": 0.97, "route": "FAST_PATH", "slots": slots}
        })

    # 30. system.greeting_summary (35 samples)
    for _ in range(35):
        template = random.choice([
            "Chào buổi sáng Onis",
            "Bắt đầu ngày mới tóm tắt tình hình giúp mình",
            "Good morning, hôm nay thế nào rồi",
            "Tóm tắt nhanh số dư và task hôm nay",
            "Onis ơi, chào bạn",
            "Hôm nay có gì mới không em",
            "Báo cáo đầu ngày cho tôi",
            "Chào OnisAgent, tóm tắt ngày hôm nay",
        ])
        samples.append({
            "input": template,
            "target": {"intent": "system.greeting_summary", "confidence": 0.98, "route": "FAST_PATH", "slots": {}}
        })

    # 31. system.help (35 samples)
    for _ in range(35):
        template = random.choice([
            "Bạn có thể giúp được gì cho tôi?",
            "Hướng dẫn sử dụng OnisAgent",
            "Trợ lý này làm được những việc gì",
            "Cho tôi xem các câu lệnh mẫu",
            "Làm sao để ghi chi tiêu bằng giọng nói",
            "Cách dùng app OnisAgent thế nào",
            "Help me, hướng dẫn các tính năng",
        ])
        samples.append({
            "input": template,
            "target": {"intent": "system.help", "confidence": 0.98, "route": "FAST_PATH", "slots": {}}
        })

    # 32. system.undo (35 samples)
    for _ in range(35):
        template = random.choice([
            "Ủa nhầm rồi, hoàn tác lại giúp mình",
            "Hủy giao dịch vừa ghi nhận",
            "Tôi vừa nói nhầm, xóa khoản chi vừa rồi đi",
            "Undo lại thao tác trước đó",
            "Nhầm số tiền rồi, hủy lệnh vừa tạo",
            "Không phải task đó, hoàn tác lại",
            "Xóa khoản vừa ghi sổ đi mình đọc lộn",
        ])
        samples.append({
            "input": template,
            "target": {"intent": "system.undo", "confidence": 0.98, "route": "FAST_PATH", "slots": {}}
        })

    return samples


def main():
    extended_samples = gen_samples()
    random.shuffle(extended_samples)

    # Load existing clean samples to merge (preserve original real-world samples)
    clean_file = DATA_DIR / "kev_dataset_clean.jsonl"
    existing_samples = []
    if clean_file.exists():
        with clean_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_samples.append(json.loads(line))

    # Combine & deduplicate inputs
    seen_inputs = set()
    final_dataset = []

    for item in existing_samples + extended_samples:
        inp = item["input"].strip()
        if inp not in seen_inputs:
            seen_inputs.add(inp)
            final_dataset.append(item)

    print(f"Tổng số mẫu câu sau khi mở rộng: {len(final_dataset)}")

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for item in final_dataset:
            out.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Đã lưu dataset mở rộng thành công tại: {OUTPUT_FILE}")

    # Stat summary
    intent_counts = {}
    for item in final_dataset:
        intent = item["target"]["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\n=== PHÂN BỐ CÁC NHÃN INTENT (INTENT DISTRIBUTION) ===")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"  {intent:32}: {count} mẫu")


if __name__ == "__main__":
    main()
