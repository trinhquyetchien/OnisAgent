import 'package:flutter/material.dart';
import '../models/models.dart';

class MockDataService extends ChangeNotifier {
  static final MockDataService _instance = MockDataService._internal();
  factory MockDataService() => _instance;
  MockDataService._internal();

  final List<TransactionItem> _transactions = [
    TransactionItem(
      id: 'tx1',
      description: 'Lương thực tập & trợ cấp tháng 11',
      amount: 12000000,
      type: 'income',
      category: 'Lương',
      date: DateTime.now().subtract(const Duration(days: 3)),
    ),
    TransactionItem(
      id: 'tx2',
      description: 'Tiền thuê căn hộ & điện nước internet',
      amount: 3200000,
      type: 'expense',
      category: 'Nhà ở & Dịch vụ',
      date: DateTime.now().subtract(const Duration(days: 2)),
      hasReceipt: true,
    ),
    TransactionItem(
      id: 'tx3',
      description: 'Thưởng xuất sắc vòng nộp hồ sơ AI4Life',
      amount: 3000000,
      type: 'income',
      category: 'Thưởng',
      date: DateTime.now().subtract(const Duration(days: 1)),
    ),
    TransactionItem(
      id: 'tx4',
      description: 'Mua sách Machine Learning & AI Agent',
      amount: 350000,
      type: 'expense',
      category: 'Học tập & Sách',
      date: DateTime.now().subtract(const Duration(days: 1)),
      hasReceipt: true,
    ),
    TransactionItem(
      id: 'tx5',
      description: 'Ăn trưa & cà phê thảo luận cùng nhóm dự án',
      amount: 85000,
      type: 'expense',
      category: 'Ăn uống',
      date: DateTime.now().subtract(const Duration(hours: 4)),
    ),
    TransactionItem(
      id: 'tx6',
      description: 'Tiền xăng xe & gửi xe tháng',
      amount: 150000,
      type: 'expense',
      category: 'Đi lại',
      date: DateTime.now().subtract(const Duration(hours: 2)),
    ),
  ];

  final List<TaskItem> _tasks = [
    TaskItem(
      id: 't1',
      title: 'Hoàn thiện slide thuyết trình vòng sơ loại AI4Life',
      description: 'Chuẩn bị 15 slide về OnisAgent, kiến trúc Dual-Path và demo mobile UI',
      deadline: DateTime.now().add(const Duration(hours: 6)),
      priority: Priority.urgent,
      isCompleted: false,
      category: 'Cuộc thi',
      isImportant: true,
    ),
    TaskItem(
      id: 't2',
      title: 'Tối ưu hoá Kev Decision Router (~5-12ms)',
      description: 'Hiệu chỉnh softmax temperature T=2.35 và kiểm tra độ trễ Fast Path',
      deadline: DateTime.now().add(const Duration(hours: 20)),
      priority: Priority.high,
      isCompleted: false,
      category: 'Kỹ thuật',
      isImportant: true,
    ),
    TaskItem(
      id: 't3',
      title: 'Đóng tiền điện & nước phòng trọ',
      description: 'Hạn cuối chuyển khoản cho chủ nhà trước ngày 20',
      deadline: DateTime.now().add(const Duration(days: 2)),
      priority: Priority.high,
      isCompleted: false,
      category: 'Tài chính',
      isImportant: true,
    ),
    TaskItem(
      id: 't4',
      title: 'Nộp báo cáo tiến độ đồ án tốt nghiệp VKU',
      description: 'In ấn và xin chữ ký giảng viên hướng dẫn',
      deadline: DateTime.now().add(const Duration(days: 4)),
      priority: Priority.medium,
      isCompleted: false,
      category: 'Học tập',
      isImportant: true,
    ),
    TaskItem(
      id: 't5',
      title: 'Đăng ký thi thử chứng chỉ AWS Cloud Practitioner',
      description: 'Kiểm tra kiến thức về DynamoDB, Lambda, S3 và Bedrock',
      deadline: DateTime.now().add(const Duration(days: 6)),
      priority: Priority.medium,
      isCompleted: false,
      category: 'Học tập',
      isImportant: false,
    ),
    TaskItem(
      id: 't6',
      title: 'Mua quà sinh nhật bạn thân',
      description: 'Ghé nhà sách hoặc cửa hàng lưu niệm',
      deadline: DateTime.now().add(const Duration(days: 7)),
      priority: Priority.low,
      isCompleted: true,
      category: 'Cá nhân',
      isImportant: false,
    ),
  ];

  final List<SavingsGoal> _savingsGoals = [
    SavingsGoal(
      id: 'sg1',
      title: 'Quỹ Dự phòng Khẩn cấp',
      targetAmount: 10000000,
      currentAmount: 6800000,
      deadlineDate: DateTime.now().add(const Duration(days: 60)),
      icon: Icons.shield_rounded,
    ),
    SavingsGoal(
      id: 'sg2',
      title: 'Đổi Laptop chạy Local AI Model (RTX GPU)',
      targetAmount: 25000000,
      currentAmount: 17500000,
      deadlineDate: DateTime.now().add(const Duration(days: 120)),
      icon: Icons.laptop_chromebook_rounded,
    ),
    SavingsGoal(
      id: 'sg3',
      title: 'Lệ phí thi chứng chỉ AWS & AI',
      targetAmount: 4000000,
      currentAmount: 3200000,
      deadlineDate: DateTime.now().add(const Duration(days: 30)),
      icon: Icons.workspace_premium_rounded,
    ),
  ];

  final List<ChatMessage> _messages = [
    ChatMessage(
      id: 'msg_1',
      text: 'Chào bạn! Mình là Onis AI – Trợ lý quản lý tài chính và công việc cá nhân. Bạn có thể ra lệnh bằng giọng nói hoặc văn bản để ghi thu chi, tạo việc cần làm hoặc nhờ phân tích ngân sách.',
      isUser: false,
      time: DateTime.now().subtract(const Duration(minutes: 15)),
      fastPathTag: 'System 1 • Kev Model Ready',
    ),
    ChatMessage(
      id: 'msg_2',
      text: 'Ghi lại tiền ăn trưa bún bò 45k vừa nãy nhé',
      isUser: true,
      time: DateTime.now().subtract(const Duration(minutes: 14)),
    ),
    ChatMessage(
      id: 'msg_3',
      text: 'Đã ghi nhận khoản chi: "Ăn uống" - 45.000 ₫ vào sổ quỹ. Số dư khả dụng của bạn đã được cập nhật chính xác với Python Decimal.',
      isUser: false,
      time: DateTime.now().subtract(const Duration(minutes: 14)),
      fastPathTag: 'Fast Path (~7ms) • 0 Token',
    ),
    ChatMessage(
      id: 'msg_4',
      text: 'Trích 500k từ tài khoản chuyển vào quỹ Đổi Laptop AI giúp mình',
      isUser: true,
      time: DateTime.now().subtract(const Duration(minutes: 5)),
    ),
    ChatMessage(
      id: 'msg_5',
      text: 'OnisAgent đã chuẩn bị kế hoạch chuyển tiền vào mục tiêu tiết kiệm. Theo nguyên tắc an toàn Human-in-the-Loop (ADR-0004), xin vui lòng xác nhận trước khi thực hiện:',
      isUser: false,
      time: DateTime.now().subtract(const Duration(minutes: 5)),
      fastPathTag: 'Reasoning Path • HITL Gate',
      hitlProposal: HitlActionProposal(
        id: 'hitl_1',
        actionType: 'transfer_savings',
        title: 'Trích ngân sách vào mục tiêu tiết kiệm',
        details: 'Chuyển 500.000 ₫ từ Số dư khả dụng sang Quỹ "Đổi Laptop chạy Local AI Model".',
        amount: 500000,
        targetName: 'Đổi Laptop chạy Local AI Model (RTX GPU)',
        status: HitlStatus.pending,
        timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      ),
    ),
  ];

  // Getters
  List<TransactionItem> get transactions => List.unmodifiable(_transactions);
  List<TaskItem> get tasks => List.unmodifiable(_tasks);
  List<SavingsGoal> get savingsGoals => List.unmodifiable(_savingsGoals);
  List<ChatMessage> get messages => List.unmodifiable(_messages);

  double get totalIncome => _transactions
      .where((t) => t.isIncome)
      .fold(0.0, (sum, t) => sum + t.amount);

  double get totalExpense => _transactions
      .where((t) => !t.isIncome)
      .fold(0.0, (sum, t) => sum + t.amount);

  double get balance => totalIncome - totalExpense;

  int get pendingTasksCount => _tasks.where((t) => !t.isCompleted).length;
  int get completedTasksCount => _tasks.where((t) => t.isCompleted).length;

  int get urgentDeadlinesCount => _tasks
      .where((t) => !t.isCompleted && t.deadline != null && t.deadline!.difference(DateTime.now()).inHours <= 24)
      .length;

  double get taskCompletionRate {
    if (_tasks.isEmpty) return 0.0;
    return (completedTasksCount / _tasks.length).clamp(0.0, 1.0);
  }

  // Transaction Actions
  void addTransaction(TransactionItem item) {
    _transactions.insert(0, item);
    notifyListeners();
  }

  void deleteTransaction(String id) {
    _transactions.removeWhere((t) => t.id == id);
    notifyListeners();
  }

  // Task Actions
  void addTask(TaskItem task) {
    _tasks.insert(0, task);
    notifyListeners();
  }

  void toggleTask(String id) {
    final idx = _tasks.indexWhere((t) => t.id == id);
    if (idx != -1) {
      _tasks[idx].isCompleted = !_tasks[idx].isCompleted;
      notifyListeners();
    }
  }

  void deleteTask(String id) {
    _tasks.removeWhere((t) => t.id == id);
    notifyListeners();
  }

  // Savings Goal Actions
  void addSavingsGoal(SavingsGoal goal) {
    _savingsGoals.add(goal);
    notifyListeners();
  }

  void depositToSavings(String goalId, double amount) {
    final idx = _savingsGoals.indexWhere((g) => g.id == goalId);
    if (idx != -1) {
      _savingsGoals[idx].currentAmount += amount;
      // Add transaction
      _transactions.insert(
        0,
        TransactionItem(
          id: 'tx_${DateTime.now().millisecondsSinceEpoch}',
          description: 'Trích tiết kiệm: ${_savingsGoals[idx].title}',
          amount: amount,
          type: 'expense',
          category: 'Tiết kiệm',
          date: DateTime.now(),
        ),
      );
      notifyListeners();
    }
  }

  // Human-in-the-loop actions
  void approveHitlProposal(String proposalId) {
    for (var msg in _messages) {
      if (msg.hitlProposal != null && msg.hitlProposal!.id == proposalId) {
        msg.hitlProposal!.status = HitlStatus.approved;
        final proposal = msg.hitlProposal!;
        if (proposal.actionType == 'transfer_savings' && proposal.amount != null) {
          final target = _savingsGoals.firstWhere(
            (g) => g.title == proposal.targetName,
            orElse: () => _savingsGoals.first,
          );
          depositToSavings(target.id, proposal.amount!);
        }
        _messages.add(
          ChatMessage(
            id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
            text: '✅ Đã thực hiện thành công giao dịch theo phê duyệt của bạn! Số dư và quỹ tiết kiệm đã được cập nhật.',
            isUser: false,
            time: DateTime.now(),
            fastPathTag: 'Fast Path Executed',
          ),
        );
        notifyListeners();
        return;
      }
    }
  }

  void rejectHitlProposal(String proposalId) {
    for (var msg in _messages) {
      if (msg.hitlProposal != null && msg.hitlProposal!.id == proposalId) {
        msg.hitlProposal!.status = HitlStatus.rejected;
        _messages.add(
          ChatMessage(
            id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
            text: '❌ Đã hủy bỏ thao tác theo lệnh của bạn. Không có thay đổi nào đối với số dư tài khoản.',
            isUser: false,
            time: DateTime.now(),
            fastPathTag: 'Action Cancelled',
          ),
        );
        notifyListeners();
        return;
      }
    }
  }

  // Chat Actions
  void addChatMessage(ChatMessage msg) {
    _messages.add(msg);
    notifyListeners();
  }
}
