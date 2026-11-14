class TransactionItem {
  final String id;
  final String description;
  final double amount;
  final String type; // 'income' or 'expense'
  final String category;
  final DateTime date;

  TransactionItem({
    required this.id,
    required this.description,
    required this.amount,
    required this.type,
    required this.category,
    required this.date,
  });

  bool get isIncome => type.toLowerCase() == 'income';
}

enum Priority { low, medium, high, urgent }

class TaskItem {
  final String id;
  final String title;
  final String? description;
  final DateTime? deadline;
  final Priority priority;
  bool isCompleted;
  final String category;

  TaskItem({
    required this.id,
    required this.title,
    this.description,
    this.deadline,
    this.priority = Priority.medium,
    this.isCompleted = false,
    this.category = 'Chung',
  });
}
