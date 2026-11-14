import 'package:flutter/material.dart';
import '../models/models.dart';

class MockDataService extends ChangeNotifier {
  static final MockDataService _instance = MockDataService._internal();
  factory MockDataService() => _instance;
  MockDataService._internal();

  final List<TransactionItem> _transactions = [
    TransactionItem(
      id: 'tx1',
      description: 'Lương tháng 11',
      amount: 25000000,
      type: 'income',
      category: 'Lương',
      date: DateTime.now().subtract(const Duration(days: 4)),
    ),
    TransactionItem(
      id: 'tx2',
      description: 'Tiền thuê căn hộ & dịch vụ',
      amount: 4500000,
      type: 'expense',
      category: 'Nhà ở',
      date: DateTime.now().subtract(const Duration(days: 3)),
    ),
    TransactionItem(
      id: 'tx3',
      description: 'Cà phê & ăn trưa đối tác',
      amount: 185000,
      type: 'expense',
      category: 'Ăn uống',
      date: DateTime.now().subtract(const Duration(days: 1)),
    ),
    TransactionItem(
      id: 'tx4',
      description: 'Thưởng dự án AI4Life',
      amount: 5000000,
      type: 'income',
      category: 'Thưởng',
      date: DateTime.now().subtract(const Duration(days: 1)),
    ),
    TransactionItem(
      id: 'tx5',
      description: 'Đi siêu thị thực phẩm tuần',
      amount: 850000,
      type: 'expense',
      category: 'Ăn uống',
      date: DateTime.now(),
    ),
  ];

  final List<TaskItem> _tasks = [
    TaskItem(
      id: 't1',
      title: 'Hoàn thiện slide thuyết trình vòng loại AI4Life',
      description: 'Chuẩn bị 15 slide về OnisAgent và kiến trúc Dual-Path',
      deadline: DateTime.now().add(const Duration(hours: 18)),
      priority: Priority.urgent,
      isCompleted: false,
      category: 'Cuộc thi',
    ),
    TaskItem(
      id: 't2',
      title: 'Tối ưu hoá Kev Decision Router (~5-12ms)',
      description: 'Hiệu chỉnh softmax temperature T=2.35',
      deadline: DateTime.now().add(const Duration(days: 1, hours: 4)),
      priority: Priority.high,
      isCompleted: false,
      category: 'Kỹ thuật',
    ),
    TaskItem(
      id: 't3',
      title: 'Nộp báo cáo tài chính tháng 10',
      description: 'Tổng kết doanh thu và biên lai',
      deadline: DateTime.now().add(const Duration(days: 3)),
      priority: Priority.medium,
      isCompleted: true,
      category: 'Tài chính',
    ),
    TaskItem(
      id: 't4',
      title: 'Review PR kết nối DynamoDB & Bedrock',
      description: 'Check lambda adapter và decimal calculator',
      deadline: DateTime.now().add(const Duration(days: 5)),
      priority: Priority.low,
      isCompleted: false,
      category: 'Kỹ thuật',
    ),
  ];

  List<TransactionItem> get transactions => List.unmodifiable(_transactions);
  List<TaskItem> get tasks => List.unmodifiable(_tasks);

  double get totalIncome => _transactions
      .where((t) => t.isIncome)
      .fold(0.0, (sum, t) => sum + t.amount);

  double get totalExpense => _transactions
      .where((t) => !t.isIncome)
      .fold(0.0, (sum, t) => sum + t.amount);

  double get balance => totalIncome - totalExpense;

  void addTransaction(TransactionItem item) {
    _transactions.insert(0, item);
    notifyListeners();
  }

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
}
