"""Generate 75 diverse Vietnamese training utterances for cross.plan_expense_task.

Focus on patterns like:
- "tính đi... dự chi..."
- "dự định đi... tính tiêu..."
- "kế hoạch đi... dự toán..."
- "dự kiến chi... cho chuyến..."
- "lên kế hoạch... ngân sách..."
- "tính tổ chức... kinh phí..."
"""

import json
from pathlib import Path

DATASET_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "clean" / "kev_dataset_unified.jsonl"

SAMPLES = [
    # Du lịch & Phượt
    ("tính đi đà lạt 3 ngày dự chi khoảng 3 triệu", {"event_name": "đi đà lạt 3 ngày", "budget": 3000000}),
    ("tính đi đà lạt cuối tuần này dự trù khoảng 2 củ rưỡi", {"event_name": "đi đà lạt cuối tuần", "budget": 2500000}),
    ("dự định đi du lịch sapa tuần sau tính tiêu 5 củ", {"event_name": "du lịch sapa tuần sau", "budget": 5000000}),
    ("kế hoạch đi phượt hà giang dự toán 2tr", {"event_name": "đi phượt hà giang", "budget": 2000000}),
    ("tính đi chơi vũng tàu cuối tuần này dự trù 2 triệu", {"event_name": "đi chơi vũng tàu", "budget": 2000000}),
    ("lên kế hoạch đi đà nẵng dự chi 4 củ", {"event_name": "đi đà nẵng", "budget": 4000000}),
    ("tính làm chuyến du lịch nha trang 4 ngày 3 đêm ngân sách 5 triệu", {"event_name": "du lịch nha trang 4 ngày 3 đêm", "budget": 5000000}),
    ("dự định đi phú quốc với người yêu tính chi tầm 8 củ", {"event_name": "đi phú quốc", "budget": 8000000}),
    ("kế hoạch đi cắm trại hồ trị an kinh phí 500k", {"event_name": "cắm trại hồ trị an", "budget": 500000}),
    ("tính đi trek tà năng phan dũng dự toán 1tr8", {"event_name": "trek tà năng phan dũng", "budget": 1800000}),
    ("dự định phượt quy nhơn bằng xe máy tính tiêu khoảng 2 củ", {"event_name": "phượt quy nhơn bằng xe máy", "budget": 2000000}),
    ("lập plan đi huế chơi 3 ngày kinh phí 2tr5", {"event_name": "đi huế chơi 3 ngày", "budget": 2500000}),
    ("tính đi tây bắc ngắm lúa chín dự chi 6 triệu", {"event_name": "đi tây bắc ngắm lúa chín", "budget": 6000000}),
    ("kế hoạch du lịch bangkok thái lan ngân sách 12 củ", {"event_name": "du lịch bangkok thái lan", "budget": 12000000}),
    ("tính đi singapore tự túc 3 ngày dự trù 15 triệu", {"event_name": "đi singapore tự túc", "budget": 15000000}),
    ("dự định đi côn đảo cuối tháng tính tiêu cỡ 6 triệu", {"event_name": "đi côn đảo cuối tháng", "budget": 6000000}),
    ("tính làm chuyến phượt mộc châu 2 ngày 1 đêm dự toán 1 triệu rưỡi", {"event_name": "phượt mộc châu 2 ngày 1 đêm", "budget": 1500000}),
    ("kế hoạch đi bà nà hills dự chi 1tr5 một người", {"event_name": "đi bà nà hills", "budget": 1500000}),
    ("tính rủ bạn đi phan thiết chơi 2 ngày dự kiến tiêu 1tr2", {"event_name": "đi phan thiết chơi 2 ngày", "budget": 1200000}),
    ("dự tính làm chuyến du lịch đà nẵng hội an 4 củ", {"event_name": "du lịch đà nẵng hội an", "budget": 4000000}),

    # Về quê, lễ tết, thăm gia đình
    ("dự định về quê ăn tết tính tiêu khoảng 10 triệu", {"event_name": "về quê ăn tết", "budget": 10000000}),
    ("tính về quê thăm bố mẹ cuối tháng dự chi 2 triệu", {"event_name": "về quê thăm bố mẹ", "budget": 2000000}),
    ("kế hoạch về quê ăn giỗ tính tiêu tầm 1 củ rưỡi", {"event_name": "về quê ăn giỗ", "budget": 1500000}),
    ("dự tính chi tiêu đợt nghỉ lễ 30/4 khoảng 4 triệu", {"event_name": "nghỉ lễ 30/4", "budget": 4000000}),
    ("tính tiền quà cáp và xe cộ về quê nghỉ tết 7 củ", {"event_name": "quà cáp xe cộ về quê", "budget": 7000000}),

    # Sự kiện, tiệc tùng, sinh nhật
    ("tính tổ chức sinh nhật dự kiến hết 1 củ rưỡi", {"event_name": "tổ chức sinh nhật", "budget": 1500000}),
    ("kế hoạch làm tiệc tất niên cho nhóm bạn dự chi 3 triệu", {"event_name": "làm tiệc tất niên", "budget": 3000000}),
    ("dự định tổ chức party tại nhà kinh phí 2 củ", {"event_name": "tổ chức party tại nhà", "budget": 2000000}),
    ("tính mở tiệc nướng bbq ngoài trời dự toán 1tr5", {"event_name": "tiệc nướng bbq ngoài trời", "budget": 1500000}),
    ("lên kế hoạch mừng thọ ông bà dự chi 5 triệu", {"event_name": "mừng thọ ông bà", "budget": 5000000}),
    ("tính làm bữa tiệc tân gia nhỏ kinh phí 2tr", {"event_name": "tiệc tân gia nhỏ", "budget": 2000000}),
    ("kế hoạch tổ chức sinh nhật cho người yêu ngân sách 2 củ", {"event_name": "tổ chức sinh nhật người yêu", "budget": 2000000}),

    # Mua sắm trang thiết bị & học tập gắn dự trù kinh phí
    ("dự định mua laptop mới ngân sách 15 triệu", {"event_name": "mua laptop mới", "budget": 15000000}),
    ("tính nâng cấp máy tính làm đồ án dự chi 5 củ", {"event_name": "nâng cấp máy tính làm đồ án", "budget": 5000000}),
    ("kế hoạch sắm đồ decor phòng trọ mới tính tiêu tầm 1 triệu", {"event_name": "sắm đồ decor phòng trọ", "budget": 1000000}),
    ("dự tính đăng ký khóa học ielts kinh phí 8 triệu", {"event_name": "đăng ký khóa học ielts", "budget": 8000000}),
    ("tính mua bộ bàn ghế công thái học dự trù 4 củ", {"event_name": "mua bộ bàn ghế công thái học", "budget": 4000000}),
    ("lên kế hoạch sắm quần áo tết ngân sách 2 triệu", {"event_name": "sắm quần áo tết", "budget": 2000000}),
    ("tính học bằng lái xe b2 dự toán 16 triệu", {"event_name": "học bằng lái xe b2", "budget": 16000000}),

    # Chuyển nhà, cải tạo, dự án cá nhân
    ("tính chuyển phòng trọ mới dự trù kinh phí 3 triệu", {"event_name": "chuyển phòng trọ mới", "budget": 3000000}),
    ("kế hoạch dọn sang căn hộ mới tính tiêu cỡ 4 củ", {"event_name": "dọn sang căn hộ mới", "budget": 4000000}),
    ("dự định sơn sửa lại phòng ngủ ngân sách 1tr5", {"event_name": "sơn sửa lại phòng ngủ", "budget": 1500000}),
    ("tính tự làm bàn làm việc gỗ kinh phí 700k", {"event_name": "tự làm bàn làm việc gỗ", "budget": 700000}),

    # Các biến thể khẩu ngữ "tính...", "dự định...", "dự chi..."
    ("tính đi chơi đâu đó cuối tuần dự chi 1 triệu", {"event_name": "đi chơi cuối tuần", "budget": 1000000}),
    ("dự định làm chuyến dã ngoại tính tiêu 800 ngàn", {"event_name": "làm chuyến dã ngoại", "budget": 800000}),
    ("tính đi xem concert âm nhạc dự trù 2 triệu", {"event_name": "đi xem concert âm nhạc", "budget": 2000000}),
    ("kế hoạch đi cổ vũ bóng đá sân vận động tính chi 500k", {"event_name": "đi cổ vũ bóng đá", "budget": 500000}),
    ("tính đi chụp bộ ảnh kỷ yếu dự toán 1 triệu", {"event_name": "chụp bộ ảnh kỷ yếu", "budget": 1000000}),
    ("dự tính đi ăn buffet hải sản với gia đình tầm 2 củ", {"event_name": "đi ăn buffet hải sản", "budget": 2000000}),
    ("tính làm chuyến du lịch ngắn ngày dự trù 3 củ", {"event_name": "du lịch ngắn ngày", "budget": 3000000}),
    ("lên kế hoạch đi phượt bằng xe ga kinh phí 1tr5", {"event_name": "đi phượt bằng xe ga", "budget": 1500000}),
    ("dự định tham gia giải chạy marathon đà nẵng tính tiêu 2 triệu", {"event_name": "tham gia giải chạy marathon", "budget": 2000000}),
    ("tính đi khám sức khỏe tổng quát dự chi 3 triệu", {"event_name": "khám sức khỏe tổng quát", "budget": 3000000}),
    ("kế hoạch đi niềng răng dự toán 30 triệu trả dần", {"event_name": "đi niềng răng", "budget": 30000000}),
    ("tính học thêm khóa lập trình flutter dự chi 3 củ", {"event_name": "học khóa lập trình flutter", "budget": 3000000}),
    ("dự định đi chùa hương đầu năm tính tiêu tầm 1tr", {"event_name": "đi chùa hương đầu năm", "budget": 1000000}),
    ("tính làm chuyến du lịch tam đảo 2 ngày dự trù 1tr8", {"event_name": "du lịch tam đảo", "budget": 1800000}),
    ("kế hoạch đi cát bà nghỉ dưỡng tính tiêu khoảng 4 củ", {"event_name": "đi cát bà nghỉ dưỡng", "budget": 4000000}),
    ("tính đi cắm trại ở ba vì cuối tuần kinh phí 600k", {"event_name": "cắm trại ở ba vì", "budget": 600000}),
    ("dự tính đi du lịch tây ninh leo núi bà đen 1 củ", {"event_name": "leo núi bà đen tây ninh", "budget": 1000000}),
    ("tính đi an giang mùa nước nổi dự toán 2 triệu", {"event_name": "đi an giang mùa nước nổi", "budget": 2000000}),
    ("lên plan đi phượt đảo phú quý 3 ngày tính tiêu 3 củ", {"event_name": "phượt đảo phú quý", "budget": 3000000}),
    ("kế hoạch rủ bạn thân đi cà phê bệt và ăn uống dự chi 300k", {"event_name": "đi cà phê bệt và ăn uống", "budget": 300000}),
    ("tính làm chuyến phượt đèo hải vân dự trù 400 ngàn", {"event_name": "phượt đèo hải vân", "budget": 400000}),
    ("dự định đăng ký thẻ tập gym 1 năm tính tiêu 4 củ", {"event_name": "đăng ký thẻ tập gym", "budget": 4000000}),
    ("tính mua sắm đồ dùng học tập kỳ mới dự toán 800k", {"event_name": "mua đồ dùng học tập", "budget": 800000}),
    ("lập kế hoạch đi xem phim và ăn tối với gấu tính chi 500k", {"event_name": "đi xem phim và ăn tối", "budget": 500000}),
    ("tính đi du lịch lý sơn 3 ngày 2 đêm kinh phí 2tr5", {"event_name": "du lịch lý sơn 3 ngày 2 đêm", "budget": 2500000}),
    ("dự định tự đi làm hộ chiếu và visa tính tiêu khoảng 3 triệu", {"event_name": "làm hộ chiếu và visa", "budget": 3000000}),
    ("tính mở workshop chia sẻ kinh nghiệm kinh phí 1tr", {"event_name": "mở workshop chia sẻ kinh nghiệm", "budget": 1000000}),
    ("kế hoạch tham gia khóa thiền vipassana dự trù 1 triệu", {"event_name": "tham gia khóa thiền", "budget": 1000000}),
]


def main():
    print(f"Adding {len(SAMPLES)} samples for 'cross.plan_expense_task'...")
    new_records = []
    for text, slots in SAMPLES:
        rec = {
            "input": text,
            "target": {
                "intent": "cross.plan_expense_task",
                "confidence": 0.98,
                "route": "REASONING_PATH",
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
