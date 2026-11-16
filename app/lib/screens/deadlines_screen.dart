import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/mock_data_service.dart';
import '../theme/app_theme.dart';
import '../models/models.dart';

class DeadlinesScreen extends StatelessWidget {
  const DeadlinesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final dataService = MockDataService();

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final now = DateTime.now();
        final tasksWithDeadlines = dataService.tasks
            .where((t) => t.deadline != null)
            .toList()
          ..sort((a, b) => a.deadline!.compareTo(b.deadline!));

        // Grouping
        final overdue = tasksWithDeadlines.where((t) => !t.isCompleted && t.deadline!.isBefore(now)).toList();
        final dueWithin24h = tasksWithDeadlines
            .where((t) => !t.isCompleted && !t.deadline!.isBefore(now) && t.deadline!.difference(now).inHours <= 24)
            .toList();
        final dueThisWeek = tasksWithDeadlines
            .where((t) => !t.isCompleted && t.deadline!.difference(now).inHours > 24 && t.deadline!.difference(now).inDays <= 7)
            .toList();
        final dueLater = tasksWithDeadlines
            .where((t) => !t.isCompleted && t.deadline!.difference(now).inDays > 7)
            .toList();
        final completed = tasksWithDeadlines.where((t) => t.isCompleted).toList();

        final totalTracked = tasksWithDeadlines.length;
        final completionRate = totalTracked > 0 ? (completed.length / totalTracked) : 0.0;

        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              const Text(
                'Quản Lý Deadline & Mốc Thời Gian',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 4),
              const Text(
                'Theo dõi thời gian thực, đếm ngược và kiểm soát hạn chót',
                style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
              ),
              const SizedBox(height: 20),

              // Progress Overview Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.track_changes_rounded, color: AppColors.primaryLight, size: 20),
                              SizedBox(width: 8),
                              Text('Tiến độ giải quyết hạn chót', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            ],
                          ),
                          Text(
                            '${(completionRate * 100).toInt()}%',
                            style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: LinearProgressIndicator(
                          value: completionRate,
                          minHeight: 8,
                          backgroundColor: const Color(0xFF334155),
                          valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '${completed.length}/$totalTracked mốc đã hoàn tất',
                            style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                          ),
                          Text(
                            dueWithin24h.isNotEmpty ? '🔥 ${dueWithin24h.length} hạn chót trong 24h' : 'Không có việc khẩn',
                            style: TextStyle(
                              color: dueWithin24h.isNotEmpty ? AppColors.expense : AppColors.accent,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // 1. Overdue Section (if any)
              if (overdue.isNotEmpty) ...[
                _buildSectionHeader('🚨 Đã quá hạn', overdue.length, AppColors.expense),
                const SizedBox(height: 8),
                ...overdue.map((t) => _buildDeadlineItem(t, dataService, now, isOverdue: true)),
                const SizedBox(height: 24),
              ],

              // 2. Due within 24 hours (Urgent)
              if (dueWithin24h.isNotEmpty) ...[
                _buildSectionHeader('🔥 Cần xong gấp (< 24 giờ)', dueWithin24h.length, AppColors.expense),
                const SizedBox(height: 8),
                ...dueWithin24h.map((t) => _buildDeadlineItem(t, dataService, now, isUrgent: true)),
                const SizedBox(height: 24),
              ],

              // 3. Due this week
              if (dueThisWeek.isNotEmpty) ...[
                _buildSectionHeader('📅 Trong tuần này', dueThisWeek.length, AppColors.warning),
                const SizedBox(height: 8),
                ...dueThisWeek.map((t) => _buildDeadlineItem(t, dataService, now)),
                const SizedBox(height: 24),
              ],

              // 4. Due later
              if (dueLater.isNotEmpty) ...[
                _buildSectionHeader('🗓️ Các tuần tiếp theo', dueLater.length, AppColors.info),
                const SizedBox(height: 8),
                ...dueLater.map((t) => _buildDeadlineItem(t, dataService, now)),
                const SizedBox(height: 24),
              ],

              // 5. Completed Deadlines
              if (completed.isNotEmpty) ...[
                _buildSectionHeader('✅ Đã hoàn thành', completed.length, AppColors.accent),
                const SizedBox(height: 8),
                ...completed.map((t) => _buildDeadlineItem(t, dataService, now, isCompleted: true)),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildSectionHeader(String title, int count, Color color) {
    return Row(
      children: [
        Text(title, style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
          decoration: BoxDecoration(
            color: color.withAlpha(25),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            '$count',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
          ),
        ),
      ],
    );
  }

  Widget _buildDeadlineItem(
    TaskItem task,
    MockDataService service,
    DateTime now, {
    bool isUrgent = false,
    bool isOverdue = false,
    bool isCompleted = false,
  }) {
    final diff = task.deadline!.difference(now);
    String countdownText;
    Color countdownColor;

    if (isCompleted) {
      countdownText = 'Đã xong';
      countdownColor = AppColors.accent;
    } else if (isOverdue) {
      final hoursAgo = (-diff.inHours);
      countdownText = hoursAgo < 24 ? 'Quá hạn ${hoursAgo}h' : 'Quá hạn ${(-diff.inDays)} ngày';
      countdownColor = AppColors.expense;
    } else if (diff.inHours <= 1) {
      countdownText = 'Còn ${diff.inMinutes} phút';
      countdownColor = AppColors.expense;
    } else if (diff.inHours <= 24) {
      countdownText = 'Còn ${diff.inHours} giờ';
      countdownColor = AppColors.expense;
    } else {
      countdownText = 'Còn ${diff.inDays} ngày';
      countdownColor = isUrgent ? AppColors.expense : AppColors.warning;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: isUrgent ? AppColors.expense.withAlpha(80) : AppColors.borderDark,
          width: isUrgent ? 1.2 : 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Checkbox(
              value: task.isCompleted,
              activeColor: AppColors.accent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
              onChanged: (_) => service.toggleTask(task.id),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    task.title,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: isCompleted ? const Color(0xFF64748B) : Colors.white,
                      decoration: isCompleted ? TextDecoration.lineThrough : null,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF334155),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          task.category,
                          style: const TextStyle(fontSize: 10, color: Color(0xFFCBD5E1)),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        DateFormat('dd/MM/yyyy HH:mm', 'vi').format(task.deadline!),
                        style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: countdownColor.withAlpha(25),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: countdownColor.withAlpha(70)),
              ),
              child: Text(
                countdownText,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: countdownColor,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
