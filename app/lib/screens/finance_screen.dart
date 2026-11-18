import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../services/mock_data_service.dart';
import '../theme/app_theme.dart';
import '../models/models.dart';

class FinanceScreen extends StatefulWidget {
  const FinanceScreen({super.key});

  @override
  State<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends State<FinanceScreen> {
  String _selectedFilter = 'Tất cả'; // 'Tất cả', 'Chi tiêu', 'Thu nhập'
  String _selectedCategory = 'Tất cả';
  int _touchedPieIndex = -1;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final dataService = MockDataService();
    final currencyFormatter = NumberFormat.currency(
      locale: 'vi_VN',
      symbol: '₫',
      decimalDigits: 0,
    );

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final filteredTx = dataService.transactions.where((tx) {
          if (_selectedFilter == 'Chi tiêu' && tx.isIncome) return false;
          if (_selectedFilter == 'Thu nhập' && !tx.isIncome) return false;
          if (_selectedCategory != 'Tất cả' && tx.category != _selectedCategory) {
            return false;
          }
          return true;
        }).toList();

        // Calculate Expense by Category for the Chart
        final Map<String, double> expenseByCategory = {};
        for (var tx in dataService.transactions.where((t) => !t.isIncome)) {
          expenseByCategory[tx.category] =
              (expenseByCategory[tx.category] ?? 0.0) + tx.amount;
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header & Add Button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Quản Lý Tài Chính',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: theme.colorScheme.onSurface,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Theo dõi dòng tiền & cân đối ngân sách',
                        style: TextStyle(
                          color: isDark
                              ? const Color(0xFF94A3B8)
                              : const Color(0xFF64748B),
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                  FilledButton.icon(
                    onPressed: () =>
                        _showAddTransactionBottomSheet(context, dataService),
                    icon: const Icon(Icons.add_rounded, size: 18),
                    label: const Text('Thêm giao dịch'),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Overview Cards (Income, Expense, Balance)
              _buildFinancialSummaryCard(
                context,
                dataService,
                currencyFormatter,
              ),
              const SizedBox(height: 20),

              // Expense Breakdown Chart Section
              if (expenseByCategory.isNotEmpty) ...[
                Text(
                  'Cơ cấu chi tiêu tháng',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 12),
                _buildExpenseChartCard(
                  context,
                  expenseByCategory,
                  currencyFormatter,
                  dataService.totalExpense,
                ),
                const SizedBox(height: 24),
              ],

              // Filter SegmentedButton M3
              Row(
                children: [
                  Expanded(
                    child: SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'Tất cả', label: Text('Tất cả')),
                        ButtonSegment(
                          value: 'Chi tiêu',
                          label: Text('Khoản chi'),
                        ),
                        ButtonSegment(
                          value: 'Thu nhập',
                          label: Text('Khoản thu'),
                        ),
                      ],
                      selected: {_selectedFilter},
                      onSelectionChanged: (newSelection) {
                        setState(() {
                          _selectedFilter = newSelection.first;
                        });
                      },
                      style: ButtonStyle(
                        visualDensity: VisualDensity.compact,
                        shape: WidgetStateProperty.all(
                          RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Category Filter Chips
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children:
                      [
                        'Tất cả',
                        'Ăn uống',
                        'Nhà ở & Dịch vụ',
                        'Học tập & Sách',
                        'Đi lại',
                        'Lương',
                        'Thưởng',
                        'Tiết kiệm',
                      ].map((category) {
                        final isSelected = _selectedCategory == category;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(
                              category,
                              style: TextStyle(
                                fontSize: 12,
                                color: isSelected
                                    ? Colors.white
                                    : (isDark
                                          ? const Color(0xFF94A3B8)
                                          : const Color(0xFF475569)),
                              ),
                            ),
                            selected: isSelected,
                            onSelected: (_) =>
                                setState(() => _selectedCategory = category),
                            selectedColor: AppColors.primary,
                            backgroundColor: isDark
                                ? AppColors.surfaceDark
                                : const Color(0xFFF1F5F9),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                              side: BorderSide(
                                color: isSelected
                                    ? AppColors.primary
                                    : theme.colorScheme.outline,
                              ),
                            ),
                            showCheckmark: false,
                          ),
                        );
                      }).toList(),
                ),
              ),
              const SizedBox(height: 16),

              // Transaction List Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Lịch sử giao dịch (${filteredTx.length})',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  if (_selectedCategory != 'Tất cả' ||
                      _selectedFilter != 'Tất cả')
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _selectedCategory = 'Tất cả';
                          _selectedFilter = 'Tất cả';
                        });
                      },
                      child: const Text(
                        'Đặt lại lọc',
                        style: TextStyle(
                          color: AppColors.primary,
                          fontSize: 12,
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),

              // Transaction Items
              if (filteredTx.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: theme.colorScheme.outline),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.receipt_long_outlined,
                        size: 40,
                        color: isDark
                            ? const Color(0xFF64748B)
                            : const Color(0xFF94A3B8),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Không tìm thấy giao dịch nào phù hợp',
                        style: TextStyle(
                          color: isDark
                              ? const Color(0xFF94A3B8)
                              : const Color(0xFF64748B),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                )
              else
                Card(
                  child: ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: filteredTx.length,
                    separatorBuilder: (context, index) =>
                        Divider(color: theme.colorScheme.outline, height: 1),
                    itemBuilder: (context, index) {
                      final tx = filteredTx[index];
                      return ListTile(
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 6,
                        ),
                        leading: CircleAvatar(
                          radius: 20,
                          backgroundColor: tx.isIncome
                              ? AppColors.accent.withAlpha(25)
                              : AppColors.expense.withAlpha(25),
                          child: Icon(
                            tx.categoryIcon,
                            color: tx.isIncome
                                ? AppColors.accent
                                : AppColors.expense,
                            size: 20,
                          ),
                        ),
                        title: Row(
                          children: [
                            Expanded(
                              child: Text(
                                tx.description,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14,
                                  color: theme.colorScheme.onSurface,
                                ),
                              ),
                            ),
                            if (tx.hasReceipt)
                              Container(
                                margin: const EdgeInsets.only(left: 6),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.info.withAlpha(
                                    isDark ? 20 : 15,
                                  ),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(
                                    color: AppColors.info.withAlpha(60),
                                  ),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      Icons.receipt_rounded,
                                      size: 10,
                                      color: AppColors.info,
                                    ),
                                    SizedBox(width: 2),
                                    Text(
                                      'OCR',
                                      style: TextStyle(
                                        color: AppColors.info,
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),
                        subtitle: Text(
                          '${tx.category} • ${DateFormat('dd/MM/yyyy HH:mm', 'vi').format(tx.date)}',
                          style: TextStyle(
                            color: isDark
                                ? const Color(0xFF94A3B8)
                                : const Color(0xFF64748B),
                            fontSize: 12,
                          ),
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              '${tx.isIncome ? '+' : '-'}${currencyFormatter.format(tx.amount)}',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                                color: tx.isIncome
                                    ? AppColors.accent
                                    : AppColors.expense,
                              ),
                            ),
                            IconButton(
                              icon: Icon(
                                Icons.delete_outline_rounded,
                                size: 18,
                                color: isDark
                                    ? const Color(0xFF64748B)
                                    : const Color(0xFF94A3B8),
                              ),
                              onPressed: () => _confirmDeleteTransaction(
                                context,
                                dataService,
                                tx,
                              ),
                            ),
                          ],
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

  Widget _buildFinancialSummaryCard(
    BuildContext context,
    MockDataService dataService,
    NumberFormat currencyFormatter,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Tổng thu tháng',
                      style: TextStyle(
                        color: isDark
                            ? const Color(0xFF94A3B8)
                            : const Color(0xFF64748B),
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '+${currencyFormatter.format(dataService.totalIncome)}',
                      style: const TextStyle(
                        color: AppColors.accent,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Container(
                  height: 36,
                  width: 1,
                  color: theme.colorScheme.outline,
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Tổng chi tháng',
                      style: TextStyle(
                        color: isDark
                            ? const Color(0xFF94A3B8)
                            : const Color(0xFF64748B),
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '-${currencyFormatter.format(dataService.totalExpense)}',
                      style: const TextStyle(
                        color: AppColors.expense,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Container(
                  height: 36,
                  width: 1,
                  color: theme.colorScheme.outline,
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Dòng tiền ròng',
                      style: TextStyle(
                        color: isDark
                            ? const Color(0xFF94A3B8)
                            : const Color(0xFF64748B),
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      currencyFormatter.format(dataService.balance),
                      style: TextStyle(
                        color: dataService.balance >= 0
                            ? AppColors.accent
                            : AppColors.expense,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExpenseChartCard(
    BuildContext context,
    Map<String, double> expenseMap,
    NumberFormat formatter,
    double totalExpense,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final colors = [
      const Color(0xFF6366F1), // Indigo
      const Color(0xFFEC4899), // Pink
      const Color(0xFF10B981), // Emerald
      const Color(0xFFF59E0B), // Amber
      const Color(0xFF3B82F6), // Blue
      const Color(0xFF8B5CF6), // Purple
    ];

    final entries = expenseMap.entries.toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            SizedBox(
              height: 180,
              child: Row(
                children: [
                  Expanded(
                    flex: 5,
                    child: PieChart(
                      PieChartData(
                        pieTouchData: PieTouchData(
                          touchCallback: (event, pieTouchResponse) {
                            setState(() {
                              if (!event.isInterestedForInteractions ||
                                  pieTouchResponse == null ||
                                  pieTouchResponse.touchedSection == null) {
                                _touchedPieIndex = -1;
                                return;
                              }
                              _touchedPieIndex = pieTouchResponse
                                  .touchedSection!
                                  .touchedSectionIndex;
                            });
                          },
                        ),
                        borderData: FlBorderData(show: false),
                        sectionsSpace: 2,
                        centerSpaceRadius: 40,
                        sections: List.generate(entries.length, (i) {
                          final isTouched = i == _touchedPieIndex;
                          final radius = isTouched ? 48.0 : 42.0;
                          final entry = entries[i];
                          final percent = totalExpense > 0
                              ? (entry.value / totalExpense * 100)
                              : 0.0;
                          return PieChartSectionData(
                            color: colors[i % colors.length],
                            value: entry.value,
                            title: '${percent.toInt()}%',
                            radius: radius,
                            titleStyle: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          );
                        }),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    flex: 6,
                    child: ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: entries.length,
                      itemBuilder: (context, index) {
                        final entry = entries[index];
                        final color = colors[index % colors.length];
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            children: [
                              Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  color: color,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  entry.key,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: isDark
                                        ? const Color(0xFFCBD5E1)
                                        : const Color(0xFF334155),
                                  ),
                                ),
                              ),
                              Text(
                                formatter.format(entry.value),
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: theme.colorScheme.onSurface,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDeleteTransaction(
    BuildContext context,
    MockDataService service,
    TransactionItem tx,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Xóa giao dịch?'),
        content: Text(
          'Bạn có chắc chắn muốn xóa "${tx.description}" khỏi sổ quỹ không?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Hủy'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.expense),
            onPressed: () {
              service.deleteTransaction(tx.id);
              Navigator.pop(ctx);
            },
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
  }

  void _showAddTransactionBottomSheet(
    BuildContext context,
    MockDataService service,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    String type = 'expense';
    String category = 'Ăn uống';
    final amountController = TextEditingController();
    final descController = TextEditingController();

    final expenseCategories = [
      'Ăn uống',
      'Nhà ở & Dịch vụ',
      'Học tập & Sách',
      'Đi lại',
      'Mua sắm',
    ];
    final incomeCategories = ['Lương', 'Thưởng', 'Freelance', 'Khác'];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) {
          final categories = type == 'expense'
              ? expenseCategories
              : incomeCategories;

          return Padding(
            padding: EdgeInsets.only(
              left: 20,
              right: 20,
              top: 16,
              bottom: MediaQuery.of(context).viewInsets.bottom + 24,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Thêm giao dịch mới',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 16),

                // Type Toggle M3
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'expense', label: Text('Khoản chi')),
                    ButtonSegment(value: 'income', label: Text('Khoản thu')),
                  ],
                  selected: {type},
                  onSelectionChanged: (val) {
                    setModalState(() {
                      type = val.first;
                      category = type == 'expense'
                          ? expenseCategories.first
                          : incomeCategories.first;
                    });
                  },
                ),
                const SizedBox(height: 16),

                // Amount
                TextField(
                  controller: amountController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Số tiền (VNĐ)',
                    prefixIcon: Icon(
                      Icons.attach_money_rounded,
                      color: AppColors.primary,
                    ),
                    hintText: 'Ví dụ: 45000',
                  ),
                ),
                const SizedBox(height: 12),

                // Description
                TextField(
                  controller: descController,
                  decoration: const InputDecoration(
                    labelText: 'Mô tả giao dịch',
                    prefixIcon: Icon(
                      Icons.description_outlined,
                      color: AppColors.primary,
                    ),
                    hintText: 'Ví dụ: Cơm trưa, Xăng xe, Thưởng dự án...',
                  ),
                ),
                const SizedBox(height: 16),

                // Category Selection
                Text(
                  'Chọn danh mục:',
                  style: TextStyle(
                    fontSize: 13,
                    color: isDark
                        ? const Color(0xFF94A3B8)
                        : const Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: categories.map((cat) {
                    final isSel = category == cat;
                    return ChoiceChip(
                      label: Text(
                        cat,
                        style: TextStyle(
                          color: isSel
                              ? Colors.white
                              : (isDark
                                    ? const Color(0xFF94A3B8)
                                    : const Color(0xFF475569)),
                        ),
                      ),
                      selected: isSel,
                      selectedColor: AppColors.primary,
                      backgroundColor: isDark
                          ? const Color(0xFF0F172A)
                          : const Color(0xFFF1F5F9),
                      onSelected: (_) => setModalState(() => category = cat),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 24),

                // Submit Button
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: () {
                      final amount =
                          double.tryParse(
                            amountController.text.replaceAll(
                              RegExp(r'[^0-9]'),
                              '',
                            ),
                          ) ??
                          0.0;
                      final desc = descController.text.trim();
                      if (amount > 0 && desc.isNotEmpty) {
                        service.addTransaction(
                          TransactionItem(
                            id: 'tx_${DateTime.now().millisecondsSinceEpoch}',
                            description: desc,
                            amount: amount,
                            type: type,
                            category: category,
                            date: DateTime.now(),
                          ),
                        );
                        Navigator.pop(ctx);
                      }
                    },
                    child: const Text('Lưu giao dịch'),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
