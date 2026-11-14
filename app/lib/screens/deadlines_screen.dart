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
        final tasksWithDeadlines = dataService.tasks
            .where((t) => t.deadline != null)
            .toList()
          ..sort((a, b) => a.deadline!.compareTo(b.deadline!));

        final urgentDeadlines = tasksWithDeadlines
            .where((t) => !t.isCompleted && t.deadline!.difference(DateTime.now()).inHours <= 24)
            .toList();

        final upcomingDeadlines = tasksWithDeadlines
            .where((t) => !t.isCompleted && t.deadline!.difference(DateTime.now()).inHours > 24)
            .toList();

        final completedDeadlines = tasksWithDeadlines.where((t) => t.isCompleted).toList();

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Quản Lý Deadline & Mốc Thời Gian',
                    style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Đếm ngược thời gian, cảnh báo hạn chót và theo dõi tiến độ',
                    style: TextStyle(color: Colors.grey, fontSize: 14),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Urgent Deadlines Banner
              if (urgentDeadlines.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.expense.withAlpha(20),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.expense.withAlpha(80)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: AppColors.expense, size: 28),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Cảnh báo: Có deadline cần hoàn tất trong 24 giờ tới!',
                              style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.expense, fontSize: 15),
                            ),
                            Text(
                              'Hãy tập trung giải quyết ${urgentDeadlines.length} công việc này trước để tránh trễ hạn.',
                              style: TextStyle(color: Colors.grey[300], fontSize: 13),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                const Text('🔥 Cần hoàn tất gấp (< 24 giờ)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: urgentDeadlines.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) => _buildDeadlineCard(urgentDeadlines[index], dataService, isUrgent: true),
                ),
                const SizedBox(height: 32),
              ],

              // Upcoming Deadlines
              const Text('📅 Sắp tới', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              if (upcomingDeadlines.isEmpty)
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceDark,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Center(
                    child: Text('Không có hạn chót sắp tới.', style: TextStyle(color: Colors.grey)),
                  ),
                )
              else
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: upcomingDeadlines.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) => _buildDeadlineCard(upcomingDeadlines[index], dataService),
                ),

              const SizedBox(height: 32),

              // Completed Deadlines
              if (completedDeadlines.isNotEmpty) ...[
                const Text('✅ Đã hoàn thành đúng hạn', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: completedDeadlines.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) => _buildDeadlineCard(completedDeadlines[index], dataService),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildDeadlineCard(TaskItem task, MockDataService dataService, {bool isUrgent = false}) {
    final diff = task.deadline!.difference(DateTime.now());
    String countdown;
    if (task.isCompleted) {
      countdown = 'Đã xong';
    } else if (diff.isNegative) {
      countdown = 'Quá hạn';
    } else if (diff.inDays > 0) {
      countdown = 'Còn ${diff.inDays} ngày ${diff.inHours % 24} giờ';
    } else if (diff.inHours > 0) {
      countdown = 'Còn ${diff.inHours} giờ ${diff.inMinutes % 60} phút';
    } else {
      countdown = 'Còn ${diff.inMinutes} phút';
    }

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isUrgent && !task.isCompleted ? AppColors.expense.withAlpha(120) : const Color(0xFF334155),
        ),
      ),
      child: Row(
        children: [
          Checkbox(
            value: task.isCompleted,
            activeColor: AppColors.accent,
            onChanged: (_) => dataService.toggleTask(task.id),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    decoration: task.isCompleted ? TextDecoration.lineThrough : null,
                    color: task.isCompleted ? Colors.grey : Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(Icons.calendar_today_rounded, size: 13, color: Colors.grey),
                    const SizedBox(width: 4),
                    Text(
                      DateFormat('HH:mm - dd/MM/yyyy').format(task.deadline!),
                      style: TextStyle(color: Colors.grey[400], fontSize: 13),
                    ),
                    const SizedBox(width: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.cardDark,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(task.category, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: task.isCompleted
                  ? AppColors.accent.withAlpha(20)
                  : isUrgent
                      ? AppColors.expense.withAlpha(30)
                      : AppColors.warning.withAlpha(30),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              countdown,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 13,
                color: task.isCompleted
                    ? AppColors.accent
                    : isUrgent
                        ? AppColors.expense
                        : AppColors.warning,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
