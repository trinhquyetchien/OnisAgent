"""Label unification and class balancing script for Kev Dataset.

1. Maps legacy intent labels to unified ADR-0006 standard:
   - expense.create -> finance.add_expense
   - income.create -> finance.add_income
   - balance.query -> finance.get_balance
   - loan.calculate -> finance.loan_installment_plan
   - savings.create -> finance.savings_goal
2. Augments low-frequency intents (< 35 samples) with rich natural Vietnamese samples.
3. Outputs to: backend/data/clean/kev_dataset_unified.jsonl
"""

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "clean"
INPUT_FILE = DATA_DIR / "kev_dataset_extended.jsonl"
OUTPUT_FILE = DATA_DIR / "kev_dataset_unified.jsonl"

LABEL_MAPPING = {
    "expense.create": "finance.add_expense",
    "income.create": "finance.add_income",
    "balance.query": "finance.get_balance",
    "loan.calculate": "finance.loan_installment_plan",
    "savings.create": "finance.savings_goal",
    "system2.escalate": "finance.financial_report",
    "task.query": "task.query_today",
}

# Augmentation templates for low-count classes
AUGMENTATION_BANK = {
    "task.query_deadline": [
        ("Tuần này có deadline nào gấp không?", {"time_range": "upcoming_48h"}),
        ("Hạn nộp đồ án tốt nghiệp VKU là khi nào?", {"time_range": "upcoming_48h"}),
        ("Kiểm tra các deadline cần hoàn thành gấp trong 3 ngày tới", {"time_range": "upcoming_72h"}),
        ("Có bài tập nào sắp hết hạn nộp bài không em?", {"time_range": "upcoming_48h"}),
        ("Xem những hạn chót cần làm gấp trong 24 giờ tới", {"time_range": "upcoming_24h"}),
        ("Deadline nộp báo cáo nghiên cứu khoa học còn bao lâu nữa?", {"time_range": "upcoming_48h"}),
        ("Check xem có việc nào sắp quá hạn không em ơi", {"time_range": "upcoming_48h"}),
        ("Liệt kê toàn bộ các hạn chót chưa hoàn thành tuần này", {"time_range": "this_week"}),
        ("Hôm nay có bài thi hay hạn chót nào phải nộp không?", {"time_range": "today"}),
        ("Deadline nộp tiền học phí học kỳ này khi nào hết hạn?", {"time_range": "upcoming_48h"}),
        ("Kiểm tra mốc thời gian hạn nộp hồ sơ xin học bổng", {"time_range": "upcoming_48h"}),
        ("Còn bao nhiêu ngày nữa là tới hạn nộp slide thuyết trình?", {"time_range": "upcoming_48h"}),
        ("Tra cứu các việc sắp trễ hạn trong ngày mai", {"time_range": "tomorrow"}),
        ("Xem cảnh báo deadline khẩn cấp", {"time_range": "urgent"}),
        ("Đồ án AI4Life hạn nộp chính xác là ngày mấy?", {"time_range": "upcoming_48h"}),
        ("Check giùm tôi danh sách deadline của tuần này", {"time_range": "this_week"}),
        ("Có hạn chót nào cần hoàn thành trước thứ Sáu không?", {"time_range": "this_week"}),
        ("Hạn đóng tiền phòng trọ là ngày mấy thế Onis?", {"time_range": "upcoming_48h"}),
        ("Danh sách deadline cấp bách nhất hiện tại", {"time_range": "urgent"}),
        ("Xem hạn chót các môn học trong kỳ", {"time_range": "all"}),
        ("Sắp tới có mốc thời gian nào quan trọng cần nhớ không?", {"time_range": "upcoming_48h"}),
        ("Deadline nộp bài tập lớn Java còn mấy tiếng nữa?", {"time_range": "upcoming_24h"}),
        ("Có việc gì sắp quá hạn cần giải quyết ngay không?", {"time_range": "urgent"}),
        ("Rà soát các hạn chót trong vòng 48h tới", {"time_range": "upcoming_48h"}),
        ("Thời hạn cuối cùng nộp bản mềm là mấy giờ?", {"time_range": "upcoming_24h"}),
    ],
    "task.query_today": [
        ("Hôm nay tôi có những việc gì cần làm?", {"date_filter": "today", "status": "pending"}),
        ("Lên danh sách việc hôm nay cần giải quyết", {"date_filter": "today", "status": "pending"}),
        ("Xem toàn bộ task ngày hôm nay của tôi", {"date_filter": "today", "status": "all"}),
        ("Hôm nay có việc gì gấp không Onis?", {"date_filter": "today", "status": "pending"}),
        ("Cho xem danh sách to-do list hôm nay", {"date_filter": "today", "status": "pending"}),
        ("Lịch trình làm việc ngày hôm nay thế nào?", {"date_filter": "today", "status": "pending"}),
        ("Check task ngày hôm nay giúp mình", {"date_filter": "today", "status": "pending"}),
        ("Còn những việc nào chưa làm xong trong ngày hôm nay?", {"date_filter": "today", "status": "pending"}),
        ("Hôm nay cần tập trung làm những đầu việc nào?", {"date_filter": "today", "status": "pending"}),
        ("Xem kế hoạch công việc ngày hôm nay", {"date_filter": "today", "status": "all"}),
        ("Liệt kê các việc đã lên lịch cho hôm nay", {"date_filter": "today", "status": "all"}),
        ("Hôm nay có lịch họp hay làm việc gì không?", {"date_filter": "today", "status": "all"}),
        ("Các công việc cần hoàn tất trước tối nay", {"date_filter": "today", "status": "pending"}),
        ("Hôm nay tôi phải hoàn thành những gì?", {"date_filter": "today", "status": "pending"}),
        ("Mở to-do list ngày hôm nay", {"date_filter": "today", "status": "pending"}),
        ("Kiểm tra danh mục việc cần làm sáng và chiều nay", {"date_filter": "today", "status": "pending"}),
        ("Hôm nay có bao nhiêu task đang chờ xử lý?", {"date_filter": "today", "status": "pending"}),
        ("Xem tiến độ các công việc trong ngày", {"date_filter": "today", "status": "all"}),
        ("Tổng hợp việc hôm nay của tôi", {"date_filter": "today", "status": "all"}),
        ("Việc hôm nay còn nhiều không trợ lý?", {"date_filter": "today", "status": "pending"}),
        ("Kiểm tra các nhiệm vụ ngày hôm nay", {"date_filter": "today", "status": "pending"}),
        ("Hôm nay có việc gì cần xử lý ngay lập tức không?", {"date_filter": "today", "status": "pending"}),
        ("Báo cáo công việc hôm nay của mình", {"date_filter": "today", "status": "all"}),
    ],
    "system.greeting_summary": [
        ("Chào buổi sáng Onis", {}),
        ("Bắt đầu ngày mới tóm tắt tình hình giúp mình", {}),
        ("Good morning, hôm nay thế nào rồi bạn?", {}),
        ("Tóm tắt nhanh số dư ví và task hôm nay", {}),
        ("Onis ơi, chào bạn nhé", {}),
        ("Hôm nay có gì mới và cần chú ý không em?", {}),
        ("Báo cáo tổng quan đầu ngày cho tôi", {}),
        ("Chào OnisAgent, tóm tắt tình hình ngày hôm nay", {}),
        ("Hello Onis, chúc một ngày tốt lành", {}),
        ("Chào buổi sáng, tóm lược công việc và ví tiền giùm tôi", {}),
        ("Xin chào, hôm nay tôi có những gì cần làm và tiền nong ra sao?", {}),
        ("Chào Onis, bắt đầu làm việc thôi nào", {}),
        ("Good morning OnisAgent, điểm tin nhanh buổi sáng", {}),
        ("Chào bạn, hôm nay tôi có bao nhiêu tiền và bao nhiêu task?", {}),
        ("Khởi động ngày mới, tóm tắt nhiệm vụ trọng tâm", {}),
        ("Chào buổi sáng trợ lý ảo của tôi", {}),
        ("Hello, tóm tắt nhanh tình trạng tài chính và công việc hôm nay", {}),
        ("Chào Onis, hôm nay ví còn tiền và có việc gì gấp không?", {}),
        ("Chào đầu ngày, sẵn sàng hỗ trợ tôi nhé", {}),
        ("Hi OnisAgent, tổng hợp ngày mới nào", {}),
        ("Chào buổi sáng, cho tôi xem 3 việc quan trọng nhất hôm nay", {}),
        ("Good morning, báo cáo ngắn gọn đầu ngày", {}),
    ],
    "system.help": [
        ("Bạn có thể giúp được những việc gì cho tôi?", {}),
        ("Hướng dẫn sử dụng OnisAgent chi tiết", {}),
        ("Trợ lý này làm được những tính năng gì?", {}),
        ("Cho tôi xem danh sách các câu lệnh mẫu", {}),
        ("Làm sao để ghi nhận chi tiêu bằng giọng nói tự nhiên?", {}),
        ("Cách dùng app OnisAgent như thế nào?", {}),
        ("Help me, hướng dẫn toàn bộ tính năng", {}),
        ("Trợ lý có tính được tiền lãi vay ngân hàng và lịch trả nợ không?", {}),
        ("Làm thế nào để tạo công việc lặp lại hàng ngày?", {}),
        ("Tôi có thể chia tiền hóa đơn nhóm trên OnisAgent được không?", {}),
        ("Hướng dẫn cách tra cứu số dư và đặt ngân sách", {}),
        ("Các lệnh cơ bản của OnisAgent là gì?", {}),
        ("Làm sao để bot hiểu các từ lóng như củ, xị, lít?", {}),
        ("Cách quản lý nợ và cho mượn tiền trên ứng dụng", {}),
        ("Chỉ cho tôi cách lên kế hoạch công việc theo ma trận Eisenhower", {}),
        ("Trợ lý có hỗ trợ nhắc hạn đóng tiền phòng không?", {}),
        ("Cho tôi xem menu trợ giúp", {}),
        ("Hướng dẫn ra lệnh giọng nói cho Onis", {}),
        ("Các tính năng quản lý tài chính gồm những gì?", {}),
        ("Tôi cần trợ giúp về cách sử dụng hệ thống", {}),
        ("Hiển thị bảng câu lệnh mẫu cho người mới bắt đầu", {}),
    ],
    "system.undo": [
        ("Ủa nhầm rồi, hoàn tác lại giúp mình", {}),
        ("Hủy giao dịch vừa ghi nhận tức thì", {}),
        ("Tôi vừa nói nhầm, xóa khoản chi vừa rồi đi", {}),
        ("Undo lại thao tác trước đó giúp tôi", {}),
        ("Nhầm số tiền rồi, hủy lệnh vừa tạo", {}),
        ("Không phải task đó đâu, hoàn tác lại giùm", {}),
        ("Xóa khoản vừa ghi sổ đi mình đọc lộn số liệu", {}),
        ("Quay lại bước trước đó giúp tôi", {}),
        ("Lệnh vừa rồi bị nhầm, hủy bỏ ngay nhé", {}),
        ("Tôi đọc nhầm tên danh mục, hoàn tác lại", {}),
        ("Hủy thao tác vừa thực hiện", {}),
        ("Undo hành động vừa rồi", {}),
        ("Nhầm rồi Onis ơi, hủy bản ghi vừa lưu đi", {}),
        ("Khoản tiền vừa nhập sai rồi, xóa đi giùm", {}),
        ("Bỏ lệnh vừa xong, tôi muốn làm lại", {}),
        ("Hủy bỏ việc vừa thêm vào danh sách", {}),
        ("Vừa ghi nhầm thu nhập thành chi tiêu, hoàn tác lại", {}),
        ("Quay lại thao tác trước", {}),
        ("Undo lại lệnh cuối cùng", {}),
        ("Tôi nói nhầm tên bạn, hủy khoản nợ vừa ghi", {}),
        ("Hủy bỏ hành động gần nhất trên hệ thống", {}),
    ],
    "task.query_completed": [
        ("Xem lại các việc tôi đã hoàn thành hôm nay", {"time_range": "today"}),
        ("Tuần này tôi đã làm xong được bao nhiêu task?", {"time_range": "this_week"}),
        ("Kiểm tra danh sách công việc đã hoàn thành trong tháng", {"time_range": "this_month"}),
        ("Hôm qua tôi đã tick xong những việc gì?", {"time_range": "yesterday"}),
        ("Xem tổng kết các đầu việc đã giải quyết tuần qua", {"time_range": "last_week"}),
        ("Cho xem lịch sử các task đã hoàn thành (done)", {"time_range": "today"}),
        ("Hôm nay đã làm được những gì rồi Onis?", {"time_range": "today"}),
        ("Liệt kê các việc đã hoàn tất ngày hôm qua", {"time_range": "yesterday"}),
        ("Xem lại các nhiệm vụ đã tick hoàn thành", {"time_range": "all"}),
        ("Tuần này năng suất của tôi thế nào, đã xong những việc gì?", {"time_range": "this_week"}),
        ("Kiểm tra các task đã xong trong tuần", {"time_range": "this_week"}),
        ("Thống kê số lượng công việc đã hoàn thành tháng này", {"time_range": "this_month"}),
        ("Xem nhật ký các việc đã làm xong", {"time_range": "all"}),
        ("Những công việc nào đã được đánh dấu hoàn tất hôm nay?", {"time_range": "today"}),
        ("Tổng hợp các mục tiêu đã đạt được trong tuần", {"time_range": "this_week"}),
        ("Hôm nay tôi đã xử lý xong những task nào?", {"time_range": "today"}),
    ],
    "task.plan_schedule": [
        ("Lên kế hoạch công việc cho tuần tới giúp mình", {"time_frame": "tuần tới"}),
        ("Sắp xếp thứ tự ưu tiên các việc hôm nay theo ma trận Eisenhower", {"time_frame": "hôm nay"}),
        ("Lập lịch trình làm việc ngày mai sao cho hiệu quả", {"time_frame": "ngày mai"}),
        ("Tối ưu hóa thời gian biểu tuần này để kịp deadline", {"time_frame": "tuần này"}),
        ("Hôm nay có nhiều task quá, nên làm việc gì trước?", {"time_frame": "hôm nay"}),
        ("Gợi ý thời gian biểu làm việc cho ngày mai từ 8h đến 18h", {"time_frame": "ngày mai"}),
        ("Lập kế hoạch phân bổ thời gian học tập và làm việc thứ 7", {"time_frame": "thứ 7"}),
        ("Sắp xếp lại lịch trình công việc hôm nay tránh quá tải", {"time_frame": "hôm nay"}),
        ("Lên kế hoạch ôn thi tuần tới cho các môn chuyên ngành", {"time_frame": "tuần tới"}),
        ("Tư vấn thứ tự giải quyết các nhiệm vụ tồn đọng", {"time_frame": "hôm nay"}),
        ("Lập kế hoạch hành động chi tiết cho tuần này", {"time_frame": "tuần này"}),
        ("Gợi ý cách sắp xếp công việc ngày hôm nay", {"time_frame": "hôm nay"}),
    ],
    "task.query_by_tag": [
        ("Xem các công việc thuộc dự án AI4Life", {"tag": "AI4Life"}),
        ("Lọc danh sách việc môn Lập trình Web", {"tag": "Lập trình Web"}),
        ("Có những task nào gắn nhãn Cá nhân?", {"tag": "Cá nhân"}),
        ("Xem toàn bộ việc của dự án tốt nghiệp VKU", {"tag": "VKU"}),
        ("Kiểm tra các việc trong nhóm Học tập", {"tag": "Học tập"}),
        ("Liệt kê danh sách việc gắn tag Công việc công ty", {"tag": "Công ty"}),
        ("Xem các task liên quan đến nghiên cứu khoa học", {"tag": "Nghiên cứu"}),
        ("Lọc các đầu việc của kỳ thi học kỳ 1", {"tag": "Thi cử"}),
        ("Tìm các nhiệm vụ thuộc nhãn Gia đình", {"tag": "Gia đình"}),
        ("Xem danh mục việc dự án OnisAgent", {"tag": "OnisAgent"}),
        ("Lọc các task có tag Quan trọng", {"tag": "Quan trọng"}),
        ("Kiểm tra các công việc dự án khởi nghiệp", {"tag": "Startup"}),
    ],
    "task.search": [
        ("Tìm các công việc có chữ slide", {"keyword": "slide"}),
        ("Tìm kiếm task liên quan đến tiền điện", {"keyword": "tiền điện"}),
        ("Tìm lịch hẹn có tên anh Tuấn", {"keyword": "anh Tuấn"}),
        ("Tra cứu việc có từ khóa báo cáo", {"keyword": "báo cáo"}),
        ("Tìm xem tôi có ghi việc mua quà sinh nhật không", {"keyword": "mua quà"}),
        ("Kiểm tra xem có task nào nhắc nộp hồ sơ không", {"keyword": "hồ sơ"}),
        ("Search các công việc có chữ họp nhóm", {"keyword": "họp nhóm"}),
        ("Tìm công việc liên quan đến hợp đồng", {"keyword": "hợp đồng"}),
        ("Tìm task có ghi chú tiếng Anh", {"keyword": "tiếng Anh"}),
        ("Tra cứu nhiệm vụ có từ khóa deadline", {"keyword": "deadline"}),
        ("Tìm xem có việc nào nhắc đi khám bệnh không", {"keyword": "khám bệnh"}),
    ],
    "finance.financial_report": [
        ("Báo cáo tài chính tháng này của tôi thế nào?", {"period": "tháng này"}),
        ("Tháng này tôi phung phí ở đâu nhiều nhất?", {"period": "tháng này"}),
        ("Phân tích tỷ trọng chi tiêu tuần này giúp mình", {"period": "tuần này"}),
        ("Đánh giá sức khỏe tài chính và dòng tiền tháng 11", {"period": "tháng này"}),
        ("Tổng kết tình hình thu chi quý vừa rồi xem có dư không", {"period": "quý này"}),
        ("Cố vấn cách cắt giảm chi tiêu tháng tới", {"period": "tháng tới"}),
        ("So sánh chi tiêu tháng này với tháng trước tăng giảm sao", {"period": "tháng này vs tháng trước"}),
        ("Tôi có đang chi tiêu vượt mức thu nhập an toàn không?", {"period": "tháng này"}),
        ("Báo cáo tổng kết dòng tiền tuần qua", {"period": "tuần trước"}),
        ("Phân tích cơ cấu chi tiêu xem mục nào chiếm tỷ trọng lớn", {"period": "tháng này"}),
        ("Đánh giá khả năng tiết kiệm và dòng tiền tự do của tôi", {"period": "tháng này"}),
    ]
}


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Source dataset not found: {INPUT_FILE}")

    samples_by_intent = defaultdict(list)
    total_raw = 0

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            total_raw += 1
            old_intent = item["target"]["intent"]
            unified_intent = LABEL_MAPPING.get(old_intent, old_intent)
            item["target"]["intent"] = unified_intent

            # Auto-align route
            if unified_intent in ["finance.financial_report", "finance.budget_plan", "task.plan_schedule", "cross.plan_expense_task"]:
                item["target"]["route"] = "REASONING_PATH"
            else:
                item["target"]["route"] = "FAST_PATH"

            samples_by_intent[unified_intent].append(item)

    print(f"Tổng mẫu gốc đọc vào: {total_raw}")
    print(f"Số lượng intents nhận diện: {len(samples_by_intent)}")

    # Augment low-count classes
    augmented_count = 0
    for intent, items in AUGMENTATION_BANK.items():
        existing_inputs = {x["input"].strip().lower() for x in samples_by_intent[intent]}
        for inp, slots in items:
            if inp.strip().lower() not in existing_inputs:
                route = "REASONING_PATH" if intent in ["finance.financial_report", "finance.budget_plan", "task.plan_schedule", "cross.plan_expense_task"] else "FAST_PATH"
                sample = {
                    "input": inp,
                    "target": {
                        "intent": intent,
                        "confidence": 0.98,
                        "route": route,
                        "slots": slots
                    }
                }
                samples_by_intent[intent].append(sample)
                existing_inputs.add(inp.strip().lower())
                augmented_count += 1

    print(f"Đã bổ sung thêm: {augmented_count} mẫu augment cho các intent ít mẫu.")

    # Flatten and deduplicate
    unified_dataset = []
    seen = set()
    for intent, items in samples_by_intent.items():
        for item in items:
            key = item["input"].strip().lower()
            if key not in seen:
                seen.add(key)
                unified_dataset.append(item)

    random.shuffle(unified_dataset)

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for item in unified_dataset:
            out.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Đã lưu thành công tập dữ liệu chuẩn hóa tại: {OUTPUT_FILE}")
    print(f"Tổng số mẫu sau chuẩn hóa & augment: {len(unified_dataset)}")

    print("\n=== THỐNG KÊ CHI TIẾT SỐ LƯỢNG MẪU TỪNG INTENT ===")
    counts = defaultdict(int)
    for x in unified_dataset:
        counts[x["target"]["intent"]] += 1

    for intent, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {intent:32}: {count:4d} mẫu")


if __name__ == "__main__":
    main()
