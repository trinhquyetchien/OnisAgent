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

  // Eisenhower Matrix quadrants
  bool get isUrgentQuadrant => priority == Priority.urgent || priority == Priority.high;
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

  double get progress => (currentAmount / targetAmount).clamp(0.0, 1.0);
  bool get isCompleted => currentAmount >= targetAmount;
}

enum HitlStatus { pending, approved, rejected }

class HitlActionProposal {
  final String id;
  final String actionType; // 'transfer_savings', 'pay_bill', 'create_urgent_task'
  final String title;
  final String details;
  final double? amount;
  final String? targetName;
  HitlStatus status;
  final DateTime timestamp;

  HitlActionProposal({
    required this.id,
    required this.actionType,
    required this.title,
    required this.details,
    this.amount,
    this.targetName,
    this.status = HitlStatus.pending,
    required this.timestamp,
  });
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
  })  : id = id ?? 'msg_${DateTime.now().millisecondsSinceEpoch}',
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
