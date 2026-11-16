import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/mock_data_service.dart';
import '../theme/app_theme.dart';
import '../models/models.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback onNavigateToFinance;
  final VoidCallback onNavigateToTasks;
  final VoidCallback onNavigateToDeadlines;
  final VoidCallback? onNavigateToAssistant;

  const HomeScreen({
    super.key,
    required this.onNavigateToFinance,
    required this.onNavigateToTasks,
    required this.onNavigateToDeadlines,
    this.onNavigateToAssistant,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _hideBalance = false;

  @override
  Widget build(BuildContext context) {
    final dataService = MockDataService();
    final currencyFormatter = NumberFormat.currency(locale: 'vi_VN', symbol: '₫', decimalDigits: 0);

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final urgentTasks = dataService.tasks
            .where((t) => !t.isCompleted && t.deadline != null && t.deadline!.difference(DateTime.now()).inHours <= 24)
            .toList()
          ..sort((a, b) => a.deadline!.compareTo(b.deadline!));

        final nextUrgentTask = urgentTasks.isNotEmpty ? urgentTasks.first : null;

        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header & AI Status
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Xin chào, Bạn! 👋',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          DateFormat('EEEE, dd/MM/yyyy', 'vi').format(DateTime.now()),
                          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withAlpha(30),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.primary.withAlpha(80)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.bolt_rounded, color: AppColors.primaryLight, size: 16),
                        SizedBox(width: 6),
                        Text(
                          'Fast Path Ready',
                          style: TextStyle(
                            color: AppColors.primaryLight,
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Primary Balance Card (Subtle Monochromatic Indigo Gradient)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF3730A3), Color(0xFF1E1B4B)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFF4F46E5).withAlpha(120)),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withAlpha(30),
                      blurRadius: 16,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.account_balance_wallet_rounded, color: AppColors.primaryLight, size: 18),
                            SizedBox(width: 8),
                            Text(
                              'Số dư khả dụng (Decimal Safe)',
                              style: TextStyle(color: Color(0xFFC7D2FE), fontSize: 13, fontWeight: FontWeight.w500),
                            ),
                          ],
                        ),
                        IconButton(
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                          icon: Icon(
                            _hideBalance ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                            color: const Color(0xFFC7D2FE),
                            size: 20,
                          ),
                          onPressed: () => setState(() => _hideBalance = !_hideBalance),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _hideBalance ? '•••••••• ₫' : currencyFormatter.format(dataService.balance),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Divider(color: Color(0xFF4338CA), height: 1),
                    const SizedBox(height: 14),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                color: AppColors.accent.withAlpha(40),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.arrow_downward_rounded, color: AppColors.accent, size: 14),
                            ),
                            const SizedBox(width: 8),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Thu tháng', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
                                Text(
                                  '+${currencyFormatter.format(dataService.totalIncome)}',
                                  style: const TextStyle(color: AppColors.accent, fontSize: 13, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                          ],
                        ),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                color: AppColors.expense.withAlpha(40),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.arrow_upward_rounded, color: AppColors.expense, size: 14),
                            ),
                            const SizedBox(width: 8),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Chi tháng', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
                                Text(
                                  '-${currencyFormatter.format(dataService.totalExpense)}',
                                  style: const TextStyle(color: AppColors.expense, fontSize: 13, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Urgent Deadline Alert Banner (if any task is due < 24h)
              if (nextUrgentTask != null) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.expense.withAlpha(25),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.expense.withAlpha(70)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.expense.withAlpha(50),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.timer_outlined, color: AppColors.expense, size: 20),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Hạn chót khẩn cấp (< 24 giờ)',
                              style: TextStyle(color: AppColors.expense, fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              nextUrgentTask.title,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                            ),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: widget.onNavigateToDeadlines,
                        style: TextButton.styleFrom(
                          foregroundColor: AppColors.expense,
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          visualDensity: VisualDensity.compact,
                        ),
                        child: const Text('Xem ngay', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],

              // Metric Cards Grid
              LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth > 900;
                  return GridView.count(
                    crossAxisCount: isWide ? 4 : 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: isWide ? 1.6 : 1.35,
                    children: [
                      _buildMetricCard(
                        title: 'Việc cần làm',
                        value: '${dataService.pendingTasksCount} việc',
                        subtitle: '${dataService.completedTasksCount} đã xong',
                        icon: Icons.checklist_rounded,
                        color: AppColors.warning,
                        onTap: widget.onNavigateToTasks,
                      ),
                      _buildMetricCard(
                        title: 'Mục tiêu tiết kiệm',
                        value: '${dataService.savingsGoals.length} mục tiêu',
                        subtitle: 'Tổng quỹ ${currencyFormatter.format(dataService.savingsGoals.fold(0.0, (s, g) => s + g.currentAmount))}',
                        icon: Icons.savings_outlined,
                        color: AppColors.accent,
                        onTap: widget.onNavigateToFinance,
                      ),
                      _buildMetricCard(
                        title: 'Hạn chót sắp tới',
                        value: '${urgentTasks.length} việc gấp',
                        subtitle: 'Hạn trong 24h',
                        icon: Icons.alarm_rounded,
                        color: AppColors.expense,
                        onTap: widget.onNavigateToDeadlines,
                      ),
                      _buildMetricCard(
                        title: 'Tiến độ chung',
                        value: '${(dataService.taskCompletionRate * 100).toInt()}%',
                        subtitle: 'Tỉ lệ hoàn thành',
                        icon: Icons.pie_chart_outline_rounded,
                        color: AppColors.info,
                        onTap: widget.onNavigateToTasks,
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 24),

              // Quick Actions
              const Text(
                'Thao tác nhanh',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: AppColors.borderDark),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      onPressed: widget.onNavigateToFinance,
                      icon: const Icon(Icons.add_circle_outline, size: 18, color: AppColors.primaryLight),
                      label: const Text('Ghi thu/chi', style: TextStyle(fontSize: 13)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: AppColors.borderDark),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      onPressed: widget.onNavigateToTasks,
                      icon: const Icon(Icons.add_task_rounded, size: 18, color: AppColors.accent),
                      label: const Text('Thêm task', style: TextStyle(fontSize: 13)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 28),

              // Savings Goals Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Mục tiêu tiết kiệm trọng điểm',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  TextButton(
                    onPressed: widget.onNavigateToFinance,
                    child: const Text('Xem tất cả', style: TextStyle(color: AppColors.primaryLight, fontSize: 13)),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              ...dataService.savingsGoals.take(2).map((goal) => _buildSavingsGoalCard(goal, currencyFormatter)),
              const SizedBox(height: 24),

              // Recent Activities Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Hoạt động gần đây',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  TextButton(
                    onPressed: widget.onNavigateToFinance,
                    child: const Text('Lịch sử', style: TextStyle(color: AppColors.primaryLight, fontSize: 13)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Card(
                child: ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: dataService.transactions.take(3).length,
                  separatorBuilder: (context, index) => const Divider(color: AppColors.borderDark, height: 1),
                  itemBuilder: (context, index) {
                    final tx = dataService.transactions[index];
                    return ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                      leading: CircleAvatar(
                        radius: 18,
                        backgroundColor: tx.isIncome ? AppColors.accent.withAlpha(30) : AppColors.expense.withAlpha(30),
                        child: Icon(
                          tx.categoryIcon,
                          color: tx.isIncome ? AppColors.accent : AppColors.expense,
                          size: 18,
                        ),
                      ),
                      title: Text(
                        tx.description,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                      ),
                      subtitle: Text(
                        '${tx.category} • ${DateFormat('dd/MM HH:mm').format(tx.date)}',
                        style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                      ),
                      trailing: Text(
                        '${tx.isIncome ? '+' : '-'}${currencyFormatter.format(tx.amount)}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          color: tx.isIncome ? AppColors.accent : AppColors.expense,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12, fontWeight: FontWeight.w500),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: color.withAlpha(25),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(icon, color: color, size: 16),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: TextStyle(color: Colors.grey[400], fontSize: 11),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSavingsGoalCard(SavingsGoal goal, NumberFormat formatter) {
    final percent = (goal.progress * 100).toInt();
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withAlpha(30),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(goal.icon, color: AppColors.primaryLight, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        goal.title,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Đã tích luỹ: ${formatter.format(goal.currentAmount)} / ${formatter.format(goal.targetAmount)}',
                        style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withAlpha(20),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '$percent%',
                    style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: goal.progress,
                minHeight: 6,
                backgroundColor: const Color(0xFF334155),
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
