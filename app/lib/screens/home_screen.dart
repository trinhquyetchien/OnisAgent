import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/mock_data_service.dart';
import '../theme/app_theme.dart';
import '../models/models.dart';

class HomeScreen extends StatelessWidget {
  final VoidCallback onNavigateToFinance;
  final VoidCallback onNavigateToTasks;
  final VoidCallback onNavigateToDeadlines;

  const HomeScreen({
    super.key,
    required this.onNavigateToFinance,
    required this.onNavigateToTasks,
    required this.onNavigateToDeadlines,
  });

  @override
  Widget build(BuildContext context) {
    final dataService = MockDataService();
    final currencyFormatter = NumberFormat.currency(locale: 'vi_VN', symbol: '₫', decimalDigits: 0);

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final upcomingDeadlines = dataService.tasks
            .where((t) => !t.isCompleted && t.deadline != null)
            .toList()
          ..sort((a, b) => a.deadline!.compareTo(b.deadline!));

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header & Greeting
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Xin chào, Bạn! 👋',
                        style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Hôm nay là ${DateFormat('EEEE, dd/MM/yyyy', 'vi').format(DateTime.now())}',
                        style: TextStyle(color: Colors.grey[400], fontSize: 14),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withAlpha(40),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.primary.withAlpha(80)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.auto_awesome, color: AppColors.primaryLight, size: 18),
                        SizedBox(width: 8),
                        Text(
                          'Onis AI Sẵn sàng',
                          style: TextStyle(color: AppColors.primaryLight, fontWeight: FontWeight.w600, fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Overview Cards (Metrics)
              LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth > 800;
                  return GridView.count(
                    crossAxisCount: isWide ? 4 : 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    childAspectRatio: isWide ? 1.8 : 1.3,
                    children: [
                      _buildMetricCard(
                        title: 'Số dư khả dụng',
                        value: currencyFormatter.format(dataService.balance),
                        icon: Icons.account_balance_wallet_rounded,
                        color: AppColors.primary,
                        onTap: onNavigateToFinance,
                      ),
                      _buildMetricCard(
                        title: 'Tổng thu tháng',
                        value: '+${currencyFormatter.format(dataService.totalIncome)}',
                        icon: Icons.trending_up_rounded,
                        color: AppColors.accent,
                        onTap: onNavigateToFinance,
                      ),
                      _buildMetricCard(
                        title: 'Tổng chi tháng',
                        value: '-${currencyFormatter.format(dataService.totalExpense)}',
                        icon: Icons.trending_down_rounded,
                        color: AppColors.expense,
                        onTap: onNavigateToFinance,
                      ),
                      _buildMetricCard(
                        title: 'Việc cần làm',
                        value: '${dataService.tasks.where((t) => !t.isCompleted).length} việc',
                        icon: Icons.check_circle_outline_rounded,
                        color: AppColors.warning,
                        onTap: onNavigateToTasks,
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 32),

              // Split Sections: Upcoming Deadlines & Recent Transactions
              LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth > 900;
                  if (isWide) {
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _buildDeadlinesSection(upcomingDeadlines)),
                        const SizedBox(width: 24),
                        Expanded(child: _buildRecentTransactionsSection(dataService, currencyFormatter)),
                      ],
                    );
                  } else {
                    return Column(
                      children: [
                        _buildDeadlinesSection(upcomingDeadlines),
                        const SizedBox(height: 24),
                        _buildRecentTransactionsSection(dataService, currencyFormatter),
                      ],
                    );
                  }
                },
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
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: AppColors.surfaceDark,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF334155)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(title, style: TextStyle(color: Colors.grey[400], fontSize: 13, fontWeight: FontWeight.w500)),
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withAlpha(30),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: color, size: 20),
                ),
              ],
            ),
            Text(
              value,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDeadlinesSection(List<TaskItem> upcomingDeadlines) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.alarm_on_rounded, color: AppColors.warning, size: 22),
                  SizedBox(width: 8),
                  Text(
                    'Deadline Sắp Tới',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              TextButton(
                onPressed: onNavigateToDeadlines,
                child: const Text('Xem tất cả', style: TextStyle(color: AppColors.primaryLight)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (upcomingDeadlines.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: Text('Không có hạn chót nào trong thời gian tới 🎉', style: TextStyle(color: Colors.grey)),
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: upcomingDeadlines.take(3).length,
              separatorBuilder: (context, index) => const Divider(color: Color(0xFF334155), height: 16),
              itemBuilder: (context, index) {
                final task = upcomingDeadlines[index];
                final timeLeft = task.deadline!.difference(DateTime.now());
                final isUrgent = timeLeft.inHours <= 24;

                return Row(
                  children: [
                    Container(
                      width: 8,
                      height: 40,
                      decoration: BoxDecoration(
                        color: isUrgent ? AppColors.expense : AppColors.warning,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(task.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                          Text(
                            DateFormat('HH:mm - dd/MM/yyyy').format(task.deadline!),
                            style: TextStyle(color: Colors.grey[400], fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: (isUrgent ? AppColors.expense : AppColors.warning).withAlpha(30),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        timeLeft.inHours > 0 ? 'Còn ${timeLeft.inHours}h' : 'Còn ${timeLeft.inMinutes}p',
                        style: TextStyle(
                          color: isUrgent ? AppColors.expense : AppColors.warning,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildRecentTransactionsSection(MockDataService dataService, NumberFormat currencyFormatter) {
    final recent = dataService.transactions.take(3).toList();
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.receipt_long_rounded, color: AppColors.accent, size: 22),
                  SizedBox(width: 8),
                  Text(
                    'Biến Động Dòng Tiền Gần Đây',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              TextButton(
                onPressed: onNavigateToFinance,
                child: const Text('Chi tiết', style: TextStyle(color: AppColors.primaryLight)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: recent.length,
            separatorBuilder: (context, index) => const Divider(color: Color(0xFF334155), height: 16),
            itemBuilder: (context, index) {
              final tx = recent[index];
              return ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(
                  backgroundColor: tx.isIncome ? AppColors.accent.withAlpha(30) : AppColors.expense.withAlpha(30),
                  child: Icon(
                    tx.isIncome ? Icons.south_west_rounded : Icons.north_east_rounded,
                    color: tx.isIncome ? AppColors.accent : AppColors.expense,
                    size: 18,
                  ),
                ),
                title: Text(tx.description, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                subtitle: Text('${tx.category} • ${DateFormat('dd/MM').format(tx.date)}', style: TextStyle(color: Colors.grey[400], fontSize: 12)),
                trailing: Text(
                  '${tx.isIncome ? "+" : "-"}${currencyFormatter.format(tx.amount)}',
                  style: TextStyle(
                    color: tx.isIncome ? AppColors.accent : AppColors.expense,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
