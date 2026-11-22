import 'package:flutter/material.dart';

enum Priority { low, medium, high, urgent }

extension PriorityExtension on Priority {
  String get label {
    switch (this) {
      case Priority.urgent:
        return 'Khẩn cấp';
      case Priority.high:
        return 'Cao';
      case Priority.medium:
        return 'Trung bình';
      case Priority.low:
        return 'Thấp';
    }
  }

  Color get color {
    switch (this) {
      case Priority.urgent:
        return const Color(0xFFEF4444); // Red
      case Priority.high:
        return const Color(0xFFF97316); // Orange
      case Priority.medium:
        return const Color(0xFF3B82F6); // Blue
      case Priority.low:
        return const Color(0xFF64748B); // Slate
    }
  }
}

class TransactionItem {
  final String id;
  final String description;
  final double amount;
  final String type; // 'income' or 'expense'
  final String category;
  final DateTime date;
  final bool hasReceipt;

  TransactionItem({
    required this.id,
    required this.description,
    required this.amount,
    required this.type,
    required this.category,
    required this.date,
    this.hasReceipt = false,
  });

  factory TransactionItem.fromJson(Map<String, dynamic> json) {
    return TransactionItem(
      id: json['id']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      amount: double.tryParse(json['amount']?.toString() ?? '0') ?? 0.0,
      type: json['type']?.toString() ?? 'expense',
      category: json['category']?.toString() ?? 'Khác',
      date: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : (json['date'] != null
                ? DateTime.tryParse(json['date'].toString()) ?? DateTime.now()
                : DateTime.now()),
      hasReceipt: json['has_receipt'] == true,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'description': description,
    'amount': amount,
    'type': type,
    'category': category,
    'created_at': date.toIso8601String(),
    'has_receipt': hasReceipt,
  };

  bool get isIncome => type.toLowerCase() == 'income';

  IconData get categoryIcon {
    switch (category) {
      case 'Ăn uống':
        return Icons.restaurant_rounded;
      case 'Nhà ở':
      case 'Nhà ở & Dịch vụ':
        return Icons.home_rounded;
      case 'Học tập':
      case 'Học tập & Sách':
        return Icons.school_rounded;
      case 'Đi lại':
        return Icons.directions_subway_rounded;
      case 'Mua sắm':
        return Icons.shopping_bag_rounded;
      case 'Lương':
        return Icons.payments_rounded;
      case 'Thưởng':
        return Icons.workspace_premium_rounded;
      case 'Tiết kiệm':
        return Icons.savings_rounded;
      default:
        return Icons.category_rounded;
    }
  }
}

class TaskItem {
  final String id;
  final String title;
  final String? description;
  final DateTime? deadline;
  final Priority priority;
  bool isCompleted;
  final String category;
  final bool isImportant;

  TaskItem({
    required this.id,
    required this.title,
    this.description,
    this.deadline,
    this.priority = Priority.medium,
    this.isCompleted = false,
    this.category = 'Chung',
    this.isImportant = false,
  });

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    final priorityStr = json['priority']?.toString().toLowerCase() ?? 'medium';
    Priority priority = Priority.medium;
    if (priorityStr == 'urgent') {
      priority = Priority.urgent;
    } else if (priorityStr == 'high') {
      priority = Priority.high;
    } else if (priorityStr == 'low') {
      priority = Priority.low;
    }

    final statusStr = json['status']?.toString().toLowerCase();
    final isDone = json['is_completed'] == true || statusStr == 'completed';

    return TaskItem(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString(),
      deadline: json['deadline'] != null
          ? DateTime.tryParse(json['deadline'].toString())
          : null,
      priority: priority,
      isCompleted: isDone,
      category: json['category']?.toString() ?? 'Chung',
      isImportant: json['is_important'] == true,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'description': description,
    'deadline': deadline?.toIso8601String(),
    'priority': priority.name,
    'status': isCompleted ? 'completed' : 'pending',
    'category': category,
    'is_important': isImportant,
  };

  // Eisenhower Matrix quadrants
  bool get isUrgentQuadrant =>
      priority == Priority.urgent || priority == Priority.high;
}

class SavingsGoal {
  final String id;
  final String title;
  final double targetAmount;
  double currentAmount;
  final DateTime deadlineDate;
  final IconData icon;

  SavingsGoal({
    required this.id,
    required this.title,
    required this.targetAmount,
    required this.currentAmount,
    required this.deadlineDate,
    this.icon = Icons.savings_rounded,
  });

  factory SavingsGoal.fromJson(Map<String, dynamic> json) {
    return SavingsGoal(
      id: json['id']?.toString() ?? '',
      title:
          json['title']?.toString() ??
          json['goal_name']?.toString() ??
          'Mục tiêu tiết kiệm',
      targetAmount:
          double.tryParse(json['target_amount']?.toString() ?? '0') ?? 0.0,
      currentAmount:
          double.tryParse(json['current_amount']?.toString() ?? '0') ?? 0.0,
      deadlineDate: json['deadline_date'] != null
          ? DateTime.tryParse(json['deadline_date'].toString()) ??
                DateTime.now().add(const Duration(days: 90))
          : DateTime.now().add(const Duration(days: 90)),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'target_amount': targetAmount,
    'current_amount': currentAmount,
    'deadline_date': deadlineDate.toIso8601String(),
  };

  double get progress => (currentAmount / targetAmount).clamp(0.0, 1.0);
  bool get isCompleted => currentAmount >= targetAmount;
}

enum HitlStatus { pending, approved, rejected }

class HitlActionProposal {
  final String id;
  final String idempotencyKey;
  final String actionType;
  final Map<String, dynamic> payload;
  final String title;
  final String details;
  final double? amount;
  final String? targetName;
  HitlStatus status;
  final DateTime timestamp;

  HitlActionProposal({
    required this.id,
    required this.actionType,
    String? idempotencyKey,
    Map<String, dynamic>? payload,
    required this.title,
    required this.details,
    this.amount,
    this.targetName,
    this.status = HitlStatus.pending,
    required this.timestamp,
  }) : idempotencyKey = idempotencyKey ?? id,
       payload = payload ?? const {};
}

class ChatMessage {
  final String id;
  final String text;
  final bool isUser;
  final DateTime time;
  final String? fastPathTag;
  final HitlActionProposal? hitlProposal;
  final String? pathBadge;
  final String? intentTag;
  final double? confidence;
  final double? latencyMs;
  final List<String> quickReplies;
  final String? status;

  ChatMessage({
    String? id,
    required this.text,
    required this.isUser,
    required this.time,
    this.fastPathTag,
    this.hitlProposal,
    this.pathBadge,
    this.intentTag,
    this.confidence,
    this.latencyMs,
    List<String>? quickReplies,
    List<String>? quickChips,
    this.status,
  }) : id = id ?? 'msg_${DateTime.now().millisecondsSinceEpoch}',
       quickReplies = quickReplies ?? quickChips ?? const [];

  List<String> get quickChips => quickReplies;

  String? get effectivePathBadge => pathBadge ?? fastPathTag;
}

class LoanScheduleItem {
  final int month;
  final double payment;
  final double principal;
  final double interest;
  final double remainingBalance;

  LoanScheduleItem({
    required this.month,
    required this.payment,
    required this.principal,
    required this.interest,
    required this.remainingBalance,
  });
}

class LoanCalculationResult {
  final double principal;
  final double annualRatePercent;
  final int months;
  final double monthlyPayment;
  final double totalPayment;
  final double totalInterest;
  final List<LoanScheduleItem> schedule;

  LoanCalculationResult({
    required this.principal,
    required this.annualRatePercent,
    required this.months,
    required this.monthlyPayment,
    required this.totalPayment,
    required this.totalInterest,
    required this.schedule,
  });
}
