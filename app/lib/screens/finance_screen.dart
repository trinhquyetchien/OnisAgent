import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/mock_data_service.dart';
import '../theme/app_theme.dart';
import '../models/models.dart';

class FinanceScreen extends StatefulWidget {
  const FinanceScreen({super.key});

  @override
  State<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends State<FinanceScreen> {
  String _selectedFilter = 'Tất cả';

  @override
  Widget build(BuildContext context) {
    final dataService = MockDataService();
    final currencyFormatter = NumberFormat.currency(locale: 'vi_VN', symbol: '₫', decimalDigits: 0);

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final filteredTx = dataService.transactions.where((tx) {
          if (_selectedFilter == 'Thu nhập') return tx.isIncome;
          if (_selectedFilter == 'Chi tiêu') return !tx.isIncome;
          return true;
        }).toList();

        // Calculate Category breakdown for Expenses
        final expenseByCategory = <String, double>{};
        for (var tx in dataService.transactions.where((t) => !t.isIncome)) {
          expenseByCategory[tx.category] = (expenseByCategory[tx.category] ?? 0) + tx.amount;
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Quản Lý Tài Chính',
                        style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Theo dõi dòng tiền, thu chi và cân đối ngân sách',
                        style: TextStyle(color: Colors.grey, fontSize: 14),
                      ),
                    ],
                  ),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () => _showAddTransactionDialog(context),
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Thêm giao dịch'),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Summary Stats & Pie Chart
              LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth > 800;
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        flex: isWide ? 3 : 1,
                        child: _buildFinancialOverviewCard(dataService, currencyFormatter),
                      ),
                      if (isWide) ...[
                        const SizedBox(width: 24),
                        Expanded(
                          flex: 2,
                          child: _buildCategoryPieChart(expenseByCategory, currencyFormatter),
                        ),
                      ],
                    ],
                  );
                },
              ),
              const SizedBox(height: 32),

              // Filter Tabs
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: ['Tất cả', 'Chi tiêu', 'Thu nhập'].map((filter) {
                      final isSelected = _selectedFilter == filter;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(filter),
                          selected: isSelected,
                          onSelected: (_) => setState(() => _selectedFilter = filter),
                          selectedColor: AppColors.primary,
                          labelStyle: TextStyle(
                            color: isSelected ? Colors.white : Colors.grey[400],
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          ),
                          backgroundColor: AppColors.surfaceDark,
                        ),
                      );
                    }).toList(),
                  ),
                  Text(
                    '${filteredTx.length} giao dịch',
                    style: const TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Transactions List
              Container(
                decoration: BoxDecoration(
                  color: AppColors.surfaceDark,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: filteredTx.length,
                  separatorBuilder: (context, index) => const Divider(color: Color(0xFF334155), height: 1),
                  itemBuilder: (context, index) {
                    final tx = filteredTx[index];
                    return ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      leading: CircleAvatar(
                        radius: 20,
                        backgroundColor: tx.isIncome ? AppColors.accent.withAlpha(30) : AppColors.expense.withAlpha(30),
                        child: Icon(
                          tx.isIncome ? Icons.arrow_downward_rounded : Icons.arrow_upward_rounded,
                          color: tx.isIncome ? AppColors.accent : AppColors.expense,
                          size: 18,
                        ),
                      ),
                      title: Text(tx.description, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                      subtitle: Text(
                        '${tx.category} • ${DateFormat('dd/MM/yyyy HH:mm').format(tx.date)}',
                        style: TextStyle(color: Colors.grey[400], fontSize: 12),
                      ),
                      trailing: Text(
                        '${tx.isIncome ? "+" : "-"}${currencyFormatter.format(tx.amount)}',
                        style: TextStyle(
                          color: tx.isIncome ? AppColors.accent : AppColors.expense,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
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

  Widget _buildFinancialOverviewCard(MockDataService dataService, NumberFormat currencyFormatter) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Số dư khả dụng hiện tại', style: TextStyle(color: Colors.grey, fontSize: 14)),
          const SizedBox(height: 8),
          Text(
            currencyFormatter.format(dataService.balance),
            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withAlpha(20),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.arrow_downward, color: AppColors.accent, size: 16),
                          SizedBox(width: 4),
                          Text('Tổng Thu', style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w600)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        currencyFormatter.format(dataService.totalIncome),
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.expense.withAlpha(20),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.arrow_upward, color: AppColors.expense, size: 16),
                          SizedBox(width: 4),
                          Text('Tổng Chi', style: TextStyle(color: AppColors.expense, fontSize: 12, fontWeight: FontWeight.w600)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        currencyFormatter.format(dataService.totalExpense),
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryPieChart(Map<String, double> expenseByCategory, NumberFormat currencyFormatter) {
    final colors = [
      AppColors.primary,
      AppColors.expense,
      AppColors.warning,
      AppColors.info,
      Colors.purple,
    ];

    final entries = expenseByCategory.entries.toList();
    final totalExpense = entries.fold(0.0, (sum, e) => sum + e.value);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Cơ cấu chi tiêu', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          SizedBox(
            height: 140,
            child: totalExpense == 0
                ? const Center(child: Text('Chưa có dữ liệu chi tiêu', style: TextStyle(color: Colors.grey)))
                : PieChart(
                    PieChartData(
                      sectionsSpace: 2,
                      centerSpaceRadius: 36,
                      sections: entries.asMap().entries.map((entry) {
                        final idx = entry.key;
                        final item = entry.value;
                        final percent = (item.value / totalExpense) * 100;
                        return PieChartSectionData(
                          color: colors[idx % colors.length],
                          value: item.value,
                          title: '${percent.toStringAsFixed(0)}%',
                          radius: 30,
                          titleStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white),
                        );
                      }).toList(),
                    ),
                  ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: entries.asMap().entries.map((entry) {
              final color = colors[entry.key % colors.length];
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                  const SizedBox(width: 6),
                  Text(entry.value.key, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  void _showAddTransactionDialog(BuildContext context) {
    final descController = TextEditingController();
    final amountController = TextEditingController();
    String type = 'expense';
    String category = 'Ăn uống';

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setModalState) => AlertDialog(
          backgroundColor: AppColors.surfaceDark,
          title: const Text('Thêm Giao Dịch Mới'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'expense', label: Text('Chi tiêu')),
                    ButtonSegment(value: 'income', label: Text('Thu nhập')),
                  ],
                  selected: {type},
                  onSelectionChanged: (set) => setModalState(() => type = set.first),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: descController,
                  decoration: const InputDecoration(
                    labelText: 'Mô tả / Tên khoản',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: amountController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Số tiền (VNĐ)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: category,
                  decoration: const InputDecoration(
                    labelText: 'Danh mục',
                    border: OutlineInputBorder(),
                  ),
                  items: ['Ăn uống', 'Nhà ở', 'Di chuyển', 'Mua sắm', 'Lương', 'Thưởng', 'Đầu tư', 'Khác']
                      .map((cat) => DropdownMenuItem(value: cat, child: Text(cat)))
                      .toList(),
                  onChanged: (val) => setModalState(() => category = val ?? 'Khác'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogCtx),
              child: const Text('Hủy', style: TextStyle(color: Colors.grey)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
              onPressed: () {
                final amount = double.tryParse(amountController.text.replaceAll(',', '')) ?? 0;
                if (descController.text.isNotEmpty && amount > 0) {
                  MockDataService().addTransaction(
                    TransactionItem(
                      id: DateTime.now().millisecondsSinceEpoch.toString(),
                      description: descController.text,
                      amount: amount,
                      type: type,
                      category: category,
                      date: DateTime.now(),
                    ),
                  );
                  Navigator.pop(dialogCtx);
                }
              },
              child: const Text('Lưu giao dịch', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }
}
