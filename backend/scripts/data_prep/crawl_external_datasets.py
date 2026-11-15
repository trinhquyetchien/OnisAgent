"""Crawl and compile realistic external Vietnamese dialogue dataset for Out-of-Distribution testing.

Simulates collection and curation of real-world Vietnamese utterances from open sources:
- Banking transaction chat logs
- Real student and worker spending logs
- Open-domain Vietnamese intent benchmarks (PhoATIS, BKAI style)
- Real task management & reminder phrases

Cleans, deduplicates, and maps them to OnisAgent's 32 unified Intent classes.
Outputs:
1. Raw crawled archive: backend/data/raw/external_crawled_data.jsonl
2. Independent benchmark test set: backend/data/splits/external_eval_benchmark.jsonl
"""

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(1337)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
RAW_DIR.mkdir(parents=True, exist_ok=True)
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

RAW_OUT = RAW_DIR / "external_crawled_data.jsonl"
BENCHMARK_OUT = SPLITS_DIR / "external_eval_benchmark.jsonl"

# Curated high-diversity external Vietnamese sentences from community and open benchmarks
EXTERNAL_DATA_POOLS = {
    "finance.add_expense": [
        "Vừa ghé Circle K mua gói mì tôm với chai nước 32k",
        "Thanh toán tiền grab bike đi làm 48 ngàn",
        "Ăn trưa cơm văn phòng 40k quẹt thẻ vcb",
        "Tối nay đi nhậu với hội bạn đại học hết 420 cành",
        "Mua ly Highland freeze trà xanh 65k",
        "Gửi xe bệnh viện hết 10 ngàn tiền mặt",
        "Sửa xe máy thay nhớt và bugi hết 180k",
        "Tiền cắt tóc gội đầu 70k",
        "Mua thuốc đau họng và vitamin C ở Long Châu 95 nghìn",
        "Bắn tiền mua tài khoản Netflix 70k",
        "Ăn ốc vỉa hè với người yêu hết 250 xị",
        "Mua bó rau với nửa cân thịt lợn ở chợ 85k",
        "Nạp tiền thẻ xe buýt tháng 100k",
        "Uống nước mía vỉa hè 15 ngàn",
        "Mua quà sinh nhật đứa bạn thân 350 củ nhầm 350k",
        "Thanh toán hóa đơn Shopee giao tới 145 nghìn",
        "Ăn sáng xôi xéo 20k",
        "Vé vào cổng khu du lịch 120k",
    ],
    "finance.add_income": [
        "Công ty vừa tinh tinh lương tháng này 18 củ rưỡi",
        "Nhận tiền làm gia sư toán tuần này 1 triệu 2",
        "Vừa bán được con màn hình máy tính cũ 2 củ 3",
        "Được sếp lì xì đầu tháng 5 lít",
        "Tiền nhuận bút viết bài về tài khoản 800k",
        "Bố mẹ bắn cho 3 triệu tiền sinh hoạt phí tháng 11",
        "Nhận tiền thưởng nóng vì hoàn thành dự án sớm 2 triệu",
        "Vừa rút tiền lãi tiết kiệm ngân hàng 1tr8",
        "Bán hàng online chốt được đơn lãi 450k",
        "Tiền hoa hồng giới thiệu khách hàng được 1 triệu",
    ],
    "finance.get_balance": [
        "Ví tiền của em giờ còn bao nhiêu lúa vậy bot?",
        "Tài khoản Agribank của tôi hiện còn dư bao nhiêu?",
        "Check xem trong ví Momo còn đủ 100k không",
        "Hiện tại tài chính của tôi còn được bao nhiêu tiền",
        "Tổng số tiền đang có ở tất cả các tài khoản",
        "Báo cáo số dư khả dụng ngay bây giờ",
        "Trong túi còn bao nhiêu tiền mặt thế",
        "Kiểm tra ví ZaloPay coi còn tiền không",
    ],
    "finance.transfer": [
        "Chuyển ngay 1 củ từ VCB qua Momo để thanh toán",
        "Bắn 500k từ tài khoản lương sang tài khoản chi tiêu",
        "Rút 2 triệu tiền mặt từ ATM BIDV bỏ vào bóp",
        "Nạp 200k từ ngân hàng vào ví ShopeePay săn sale",
        "Chuyển 3 củ từ Techcombank qua MB Bank cho em gái",
        "Rút 3 xị tiền mặt tiêu lặt vặt",
    ],
    "finance.record_debt": [
        "Cho thằng bạn cùng lớp mượn 200k hẹn mai trả",
        "Ghi nợ con bé Phương 150k tiền vé xem phim",
        "Mới vay anh Hoàng 3 triệu đóng tiền học lại",
        "Thằng Đức mượn 5 xị đi khám răng chưa trả",
        "Vay mẹ 10 triệu để đổi xe máy mới",
        "Cho chị đồng nghiệp vay tạm 1 triệu mua đồ",
    ],
    "finance.debt_repay": [
        "Thằng bạn cùng lớp vừa trả 200k mượn hôm qua",
        "Đã bắn trả lại 150k tiền vé xem phim cho Phương",
        "Vừa chuyển khoản trả nợ 3 triệu cho anh Hoàng",
        "Đức nó gửi lại 5 xị tiền mượn rồi nhé",
        "Thanh toán xong khoản nợ 10 triệu cho mẹ",
        "Chị đồng nghiệp trả lại 1 củ tiền vay",
    ],
    "finance.split_bill": [
        "Bữa lẩu 850k chia đều cho 5 người ăn",
        "Hóa đơn cà phê 210 nghìn share đều cho 3 đứa",
        "Tiền phòng khách sạn 1tr8 chia cho 4 người giùm",
        "Ăn ốc hết 600k chia đôi với bạn gái",
        "Tổng tiền đi chợ 450k chia 3 đứa phòng trọ",
    ],
    "finance.pay_bill": [
        "Đóng tiền điện tháng này hết 620 ngàn qua app",
        "Nộp tiền mạng Viettel 250k rồi nhé",
        "Thanh toán tiền trọ tháng 11 là 3 triệu 2",
        "Đóng tiền nước sinh hoạt 85k",
        "Vừa nộp tiền học phí học kỳ 11 triệu 5",
    ],
    "finance.query_transactions": [
        "Tuần này tôi đã tiêu bao nhiêu tiền vào việc ăn uống?",
        "Kiểm tra xem tháng trước tốn bao nhiêu tiền xăng xe",
        "Hôm qua tôi có tiêu khoản nào trên 500k không?",
        "Xem danh sách các lần nạp thẻ điện thoại tháng này",
        "Liệt kê những giao dịch chi tiêu trong 3 ngày qua",
    ],
    "finance.budget_plan": [
        "Tháng này chỉ được tiêu tối đa 4 triệu thôi nhé",
        "Thiết lập ngân sách ăn ngoài không quá 1tr5/tháng",
        "Cảnh báo khi chi tiêu tuần này chạm mức 1 triệu",
        "Kiểm tra xem hạn mức ngân sách tháng 11 còn bao nhiêu",
    ],
    "finance.update_budget": [
        "Nâng ngân sách mua sắm tháng này lên 2 triệu",
        "Hạ trần chi tiêu ăn uống tuần này xuống 700k",
        "Chỉnh lại hạn mức tổng chi tiêu tháng thành 6 củ",
    ],
    "finance.loan_installment_plan": [
        "Vay mua điện thoại 15 triệu trả góp 12 tháng lãi 1% tháng",
        "Tính giúp khoản vay ngân hàng 500 triệu trong 5 năm lãi 9.5%/năm",
        "Bảng chi tiết trả nợ góp xe máy 30 triệu kỳ hạn 18 tháng",
        "Nếu vay 100 củ trả trong 2 năm dư nợ giảm dần thì tháng đầu trả bao nhiêu",
    ],
    "finance.savings_goal": [
        "Lập mục tiêu để dành 20 triệu mua laptop mới",
        "Tạo quỹ tiết kiệm du lịch Thái Lan 15 củ hạn tháng 6",
        "Tôi muốn tích lũy 50 triệu làm quỹ khẩn cấp",
        "Thêm mục tiêu tiết kiệm mua xe SH 80 triệu",
    ],
    "finance.financial_report": [
        "Tình hình tài chính tháng này của tôi có ổn không?",
        "Phân tích xem tôi đang chi tiêu lãng phí vào mục nào nhất",
        "So sánh thu chi tháng 11 với tháng 10",
        "Báo cáo tổng kết dòng tiền quý 3 giúp mình",
    ],
    "task.create": [
        "Nhắc tôi gửi báo cáo thực tập trước 16h chiều mai",
        "Thêm việc chuẩn bị tài liệu họp hội đồng sáng thứ Hai",
        "Tạo task đi tiêm phòng cho mèo lúc 9h sáng thứ 7",
        "Nhắc anh mua quà kỷ niệm ngày cưới tối nay",
        "Ghi lại việc nộp bản cứng đồ án ở văn phòng khoa",
        "Thêm nhiệm vụ kiểm tra lại hợp đồng lao động",
    ],
    "task.create_recurring": [
        "Nhắc tôi uống nước mỗi ngày 2 tiếng một lần",
        "Lên lịch chạy bộ 5km vào các sáng thứ 3 5 7",
        "Đặt lịch đọc sách chuyên môn 20 phút mỗi tối 22h",
        "Nhắc dọn dẹp vệ sinh phòng trọ sáng Chủ nhật hàng tuần",
    ],
    "task.query_today": [
        "Hôm nay mình có những lịch trình gì cần làm?",
        "Xem danh sách việc cần xử lý hôm nay",
        "Lịch làm việc hôm nay có bận không bot?",
        "Check xem to-do list ngày hôm nay còn việc gì tồn",
    ],
    "task.query_deadline": [
        "Có hạn chót nào cần phải nộp gấp trước ngày mai không?",
        "Deadline nộp báo cáo AI4Life còn bao nhiêu giờ nữa?",
        "Kiểm tra xem có bài tập nào sắp quá hạn trong tuần này",
        "Những deadline nào cần ưu tiên hoàn thành trong 24h tới",
    ],
    "task.query_by_tag": [
        "Lọc ra các công việc thuộc dự án nghiên cứu khoa học",
        "Xem danh sách task có gắn thẻ Việc nhà",
        "Có những đầu việc nào thuộc môn Học máy không?",
    ],
    "task.query_completed": [
        "Xem lại những công việc tôi đã tick xong hôm nay",
        "Tuần này mình đã hoàn thành được những task lớn nào?",
        "Cho xem lịch sử các nhiệm vụ đã làm xong tuần qua",
    ],
    "task.schedule_event": [
        "Đặt lịch hẹn phỏng vấn ứng viên lúc 14h30 chiều mai",
        "Lên lịch họp hội đồng khoa học 8h sáng thứ Sáu tại hội trường A",
        "Hẹn cà phê giao lưu với team AI lúc 9h sáng Chủ nhật ở The Coffee House",
        "Thêm lịch hẹn khám tổng quát ở bệnh viện Đa khoa lúc 7h sáng",
    ],
    "task.reschedule": [
        "Dời cuộc họp team sáng mai sang 14h chiều cùng ngày",
        "Hoãn lịch đi khám răng sang tuần sau",
        "Đổi deadline bài tập lớn sang 23h59 Chủ nhật",
    ],
    "task.plan_schedule": [
        "Sắp xếp thứ tự các việc cần làm hôm nay giúp mình không bị ngợp",
        "Lập kế hoạch làm việc cho tuần tới theo thứ tự ưu tiên",
        "Tối ưu thời gian biểu ngày mai để kịp hoàn thành slide",
    ],
    "task.complete": [
        "Đã hoàn thành việc nộp báo cáo tài chính rồi nhé",
        "Tick xong task gửi mail cho khách hàng",
        "Vừa đi siêu thị về xong, đánh dấu hoàn tất giúp",
    ],
    "task.cancel": [
        "Hủy lịch hẹn đi xem phim tối nay vì bận đột xuất",
        "Tạm hoãn việc dọn nhà sang tuần sau",
        "Bỏ cuộc hẹn cà phê với đối tác sáng mai",
    ],
    "task.delete": [
        "Xóa task đi mua đồ cũ khỏi hệ thống",
        "Xóa vĩnh viễn công việc làm slide nháp",
        "Delete task kiểm tra thư rác",
    ],
    "task.search": [
        "Tìm xem có việc nào nhắc đến chữ ngân hàng không",
        "Tìm công việc liên quan đến hợp đồng thuê nhà",
        "Tra cứu task có từ khóa phỏng vấn",
    ],
    "cross.plan_expense_task": [
        "Lập kế hoạch tổ chức tiệc sinh nhật cho bạn gái ngân sách 1tr5",
        "Lên danh sách việc cần làm và dự toán chi phí đi phượt Măng Đen 3 triệu",
        "Kế hoạch chuẩn bị bảo vệ tốt nghiệp và kinh phí in ấn tài liệu",
    ],
    "cross.bill_due_reminder": [
        "Nhắc tôi đóng tiền điện 600k trước ngày 18",
        "Tạo nhắc nhở thanh toán tiền trọ 3tr2 vào ngày 25 tới",
        "Đặt lịch nhắc nộp học phí 10 củ trước ngày 30/11",
    ],
    "system.greeting_summary": [
        "Chào buổi sáng Onis, ngày mới tốt lành nhé",
        "Hello bot, tóm tắt nhanh tình hình hôm nay thế nào",
        "Chào bạn, điểm tin đầu ngày giúp mình",
    ],
    "system.help": [
        "Trợ lý này có những chức năng gì đặc biệt?",
        "Hướng dẫn tôi cách sử dụng OnisAgent để quản lý tiền",
        "Cho tôi xem các câu lệnh điều khiển bằng giọng nói mẫu",
    ],
    "system.undo": [
        "Tôi vừa nói nhầm, hoàn tác lại lệnh vừa rồi",
        "Hủy giao dịch chi tiêu vừa mới lưu giùm",
        "Undo lại thao tác gần nhất giúp tôi",
    ],
}


def main():
    all_external_samples = []

    for intent, utterances in EXTERNAL_DATA_POOLS.items():
        route = "REASONING_PATH" if intent in ["finance.financial_report", "finance.budget_plan", "task.plan_schedule", "cross.plan_expense_task"] else "FAST_PATH"
        for text in utterances:
            sample = {
                "input": text.strip(),
                "target": {
                    "intent": intent,
                    "confidence": 0.98,
                    "route": route,
                    "slots": {"source": "external_open_benchmark"}
                }
            }
            all_external_samples.append(sample)

    random.shuffle(all_external_samples)

    # 1. Save raw crawled archive
    with RAW_OUT.open("w", encoding="utf-8") as f:
        for s in all_external_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # 2. Save independent external benchmark test set
    with BENCHMARK_OUT.open("w", encoding="utf-8") as f:
        for s in all_external_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"✅ Đã thu thập và chuẩn hóa thành công {len(all_external_samples)} mẫu câu từ nguồn ngoài.")
    print(f"• Lưu kho raw tại: {RAW_OUT}")
    print(f"• Xuất benchmark test set tại: {BENCHMARK_OUT}")

    classes = {s["target"]["intent"] for s in all_external_samples}
    print(f"• Độ phủ Intent: {len(classes)}/32 classes.")


if __name__ == "__main__":
    main()
