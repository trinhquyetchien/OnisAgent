import 'package:flutter/foundation.dart';

import '../models/models.dart';
import 'api_service.dart';

class AppDataService extends ChangeNotifier {
  static final AppDataService _instance = AppDataService._internal();

  factory AppDataService() => _instance;

  AppDataService._internal() : _apiService = ApiService();

  @visibleForTesting
  AppDataService.forTesting(ApiService apiService) : _apiService = apiService;

  final ApiService _apiService;
  List<TransactionItem> _transactions = [];
  List<TaskItem> _tasks = [];
  List<SavingsGoal> _savingsGoals = [];
  List<Map<String, dynamic>> _debts = [];
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<TransactionItem> get transactions => List.unmodifiable(_transactions);
  List<TaskItem> get tasks => List.unmodifiable(_tasks);
  List<SavingsGoal> get savingsGoals => List.unmodifiable(_savingsGoals);
  List<Map<String, dynamic>> get debts => List.unmodifiable(_debts);
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  double get totalIncome => _transactions
      .where((transaction) => transaction.isIncome)
      .fold(0.0, (total, transaction) => total + transaction.amount);

  double get totalExpense => _transactions
      .where((transaction) => !transaction.isIncome)
      .fold(0.0, (total, transaction) => total + transaction.amount);

  double get balance => totalIncome - totalExpense;

  int get pendingTasksCount => _tasks.where((task) => !task.isCompleted).length;
  int get completedTasksCount =>
      _tasks.where((task) => task.isCompleted).length;

  int get urgentDeadlinesCount => _tasks
      .where(
        (task) =>
            !task.isCompleted &&
            task.deadline != null &&
            task.deadline!.difference(DateTime.now()).inHours <= 24,
      )
      .length;

  double get taskCompletionRate => _tasks.isEmpty
      ? 0
      : (completedTasksCount / _tasks.length).clamp(0.0, 1.0);

  Future<void> refresh() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      _transactions = (await _apiService.listTransactions())
          .map((item) => TransactionItem.fromJson(_asObject(item)))
          .toList();
      _tasks = (await _apiService.listTasks())
          .map((item) => TaskItem.fromJson(_asObject(item)))
          .toList();
      _savingsGoals = (await _apiService.listSavingsGoals())
          .map((item) => SavingsGoal.fromJson(_asObject(item)))
          .toList();
      _debts = (await _apiService.listDebts()).map(_asObject).toList();
    } on Exception catch (error) {
      _errorMessage = error.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> addTransaction(TransactionItem item) async {
    await _perform(() async {
      final result = await _apiService.createTransaction(
        amount: item.amount,
        type: item.type,
        description: item.description,
        category: item.category,
      );
      _transactions.insert(
        0,
        TransactionItem.fromJson(_nestedObject(result, 'transaction')),
      );
      notifyListeners();
    });
  }

  Future<void> updateTransaction(TransactionItem item) async {
    await _perform(() async {
      final result = await _apiService.updateTransaction(
        id: item.id,
        amount: item.amount,
        type: item.type,
        description: item.description,
        category: item.category,
      );
      final updated = TransactionItem.fromJson(
        _nestedObject(result, 'transaction'),
      );
      final index = _transactions.indexWhere(
        (transaction) => transaction.id == item.id,
      );
      if (index >= 0) _transactions[index] = updated;
      notifyListeners();
    });
  }

  Future<void> correctTransactionCategory(
    TransactionItem transaction,
    String correctedCategory,
  ) async {
    await _perform(() async {
      await _apiService.correctTransactionCategory(
        transactionId: transaction.id,
        rawDescription: transaction.description,
        predictedCategory: transaction.category,
        correctedCategory: correctedCategory,
      );
      final index = _transactions.indexWhere(
        (item) => item.id == transaction.id,
      );
      if (index >= 0) {
        _transactions[index] = TransactionItem(
          id: transaction.id,
          description: transaction.description,
          amount: transaction.amount,
          type: transaction.type,
          category: correctedCategory,
          date: transaction.date,
          hasReceipt: transaction.hasReceipt,
        );
      }
      notifyListeners();
    });
  }

  Future<void> deleteTransaction(String id) async {
    await _perform(() async {
      await _apiService.deleteTransaction(id);
      _transactions.removeWhere((transaction) => transaction.id == id);
      notifyListeners();
    });
  }

  Future<void> addTask(TaskItem task) async {
    await _perform(() async {
      final result = await _apiService.createTask(
        title: task.title,
        description: task.description,
        deadline: task.deadline?.toIso8601String(),
        priority: task.priority.name,
        category: task.category,
        isImportant: task.isImportant,
      );
      _tasks.insert(0, TaskItem.fromJson(_nestedObject(result, 'task')));
      notifyListeners();
    });
  }

  Future<void> toggleTask(String id) async {
    final index = _tasks.indexWhere((task) => task.id == id);
    if (index < 0) return;
    final task = _tasks[index];
    await _perform(() async {
      final result = await _apiService.updateTask(
        id: id,
        status: task.isCompleted ? 'pending' : 'completed',
      );
      _tasks[index] = TaskItem.fromJson(_nestedObject(result, 'task'));
      notifyListeners();
    });
  }

  Future<void> deleteTask(String id) async {
    await _perform(() async {
      final result = await _apiService.deleteTask(id);
      if (result['requires_hitl'] == true) {
        _addHitlProposal(
          action: 'task_delete',
          payload: {'task_id': id},
          title: 'Xóa công việc',
          details: 'Xác nhận xóa công việc này?',
        );
        _errorMessage =
            'Yêu cầu xóa đang chờ phê duyệt. Mở tab Trợ lý AI để xác nhận.';
      } else {
        _tasks.removeWhere((task) => task.id == id);
        notifyListeners();
      }
    });
  }

  Future<void> addSavingsGoal(SavingsGoal goal) async {
    await _perform(() async {
      final result = await _apiService.createSavingsGoal(
        title: goal.title,
        targetAmount: goal.targetAmount,
        currentAmount: goal.currentAmount,
        deadlineDate: goal.deadlineDate.toIso8601String(),
      );
      _savingsGoals.add(
        SavingsGoal.fromJson(_nestedObject(result, 'savings_goal')),
      );
      notifyListeners();
    });
  }

  Future<void> addDebt({
    required String person,
    required double amount,
    required String debtType,
    String? note,
  }) async {
    await _perform(() async {
      final result = await _apiService.createDebt(
        person: person,
        amount: amount,
        debtType: debtType,
        note: note,
      );
      _debts.add(_nestedObject(result, 'debt'));
      notifyListeners();
    });
  }

  Future<void> approveHitlProposal(String proposalId) async {
    final proposal = _findProposal(proposalId);
    if (proposal == null) return;
    await _perform(() async {
      await _apiService.approveHitl(
        idempotencyKey: proposal.idempotencyKey,
        action: proposal.actionType,
        payload: proposal.payload,
      );
      proposal.status = HitlStatus.approved;
      if (proposal.actionType == 'task_delete' &&
          proposal.payload['task_id'] != null) {
        _tasks.removeWhere(
          (task) => task.id == proposal.payload['task_id'].toString(),
        );
      } else {
        await _loadRemoteLists();
      }
      notifyListeners();
    });
  }

  void rejectHitlProposal(String proposalId) {
    final proposal = _findProposal(proposalId);
    if (proposal == null) return;
    proposal.status = HitlStatus.rejected;
    notifyListeners();
  }

  void addChatMessage(ChatMessage message) {
    _messages.add(message);
    notifyListeners();
  }

  void addChatHitlProposal({
    required String action,
    required Map<String, dynamic> payload,
    required String title,
    required String details,
    String? idempotencyKey,
  }) {
    _addHitlProposal(
      action: action,
      payload: payload,
      title: title,
      details: details,
      idempotencyKey: idempotencyKey,
    );
  }

  void markHitlProposalStatus(String proposalId, HitlStatus status) {
    final proposal = _findProposal(proposalId);
    if (proposal == null) return;
    proposal.status = status;
    notifyListeners();
  }

  Future<void> _loadRemoteLists() async {
    _transactions = (await _apiService.listTransactions())
        .map((item) => TransactionItem.fromJson(_asObject(item)))
        .toList();
    _tasks = (await _apiService.listTasks())
        .map((item) => TaskItem.fromJson(_asObject(item)))
        .toList();
    _savingsGoals = (await _apiService.listSavingsGoals())
        .map((item) => SavingsGoal.fromJson(_asObject(item)))
        .toList();
    _debts = (await _apiService.listDebts()).map(_asObject).toList();
  }

  Future<void> _perform(Future<void> Function() action) async {
    _errorMessage = null;
    try {
      await action();
    } on Exception catch (error) {
      _errorMessage = error.toString();
    } finally {
      notifyListeners();
    }
  }

  void _addHitlProposal({
    required String action,
    required Map<String, dynamic> payload,
    required String title,
    required String details,
    String? idempotencyKey,
  }) {
    final idempotency =
        idempotencyKey ?? 'hitl_${DateTime.now().microsecondsSinceEpoch}';
    final id = idempotency;
    _messages.add(
      ChatMessage(
        text: 'Cần bạn xác nhận trước khi thực hiện: $title',
        isUser: false,
        time: DateTime.now(),
        pathBadge: 'HITL • Chờ xác nhận',
        hitlProposal: HitlActionProposal(
          id: id,
          idempotencyKey: idempotency,
          actionType: action,
          payload: payload,
          title: title,
          details: details,
          targetName: payload['task_id']?.toString(),
          timestamp: DateTime.now(),
        ),
      ),
    );
    notifyListeners();
  }

  HitlActionProposal? _findProposal(String id) {
    for (final message in _messages) {
      final proposal = message.hitlProposal;
      if (proposal?.id == id) return proposal;
    }
    return null;
  }

  Map<String, dynamic> _nestedObject(Map<String, dynamic> value, String key) =>
      _asObject(value[key]);

  Map<String, dynamic> _asObject(dynamic value) {
    if (value is! Map<String, dynamic>) {
      throw const FormatException('Dữ liệu trả về từ API không hợp lệ.');
    }
    return value;
  }
}
