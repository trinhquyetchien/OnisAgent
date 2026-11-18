import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/mock_data_service.dart';
import '../theme/app_theme.dart';
import '../models/models.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  String _viewMode = 'list'; // 'list' | 'matrix'
  String _statusFilter = 'all'; // 'all' | 'pending' | 'completed'

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final dataService = MockDataService();

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final allTasks = dataService.tasks;

        final filteredTasks = allTasks.where((task) {
          if (_statusFilter == 'pending') return !task.isCompleted;
          if (_statusFilter == 'completed') return task.isCompleted;
          return true;
        }).toList();

        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header & Add Task Button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Quản Lý Công Việc',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: theme.colorScheme.onSurface,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${dataService.pendingTasksCount} việc cần làm • ${dataService.completedTasksCount} đã xong',
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
                        _showAddTaskBottomSheet(context, dataService),
                    icon: const Icon(Icons.add_task_rounded, size: 18),
                    label: const Text('Tạo task'),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // View Mode Selector (List vs Eisenhower Matrix)
              Row(
                children: [
                  Expanded(
                    child: SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(
                          value: 'list',
                          icon: Icon(Icons.list_alt_rounded, size: 18),
                          label: Text('Danh sách'),
                        ),
                        ButtonSegment(
                          value: 'matrix',
                          icon: Icon(Icons.grid_view_rounded, size: 18),
                          label: Text('Ma trận Eisenhower'),
                        ),
                      ],
                      selected: {_viewMode},
                      onSelectionChanged: (val) =>
                          setState(() => _viewMode = val.first),
                      style: ButtonStyle(
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
              const SizedBox(height: 16),

              // Content based on View Mode
              if (_viewMode == 'matrix')
                _buildEisenhowerMatrixView(context, allTasks, dataService)
              else ...[
                // Filter chips for List View
                Row(
                  children: [
                    _buildFilterChip(
                      context,
                      'Tất cả (${allTasks.length})',
                      'all',
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      context,
                      'Chưa xong (${dataService.pendingTasksCount})',
                      'pending',
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      context,
                      'Đã xong (${dataService.completedTasksCount})',
                      'completed',
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Task List Items
                if (filteredTasks.isEmpty)
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
                          Icons.check_circle_outline_rounded,
                          size: 40,
                          color: isDark
                              ? const Color(0xFF64748B)
                              : const Color(0xFF94A3B8),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Không có công việc nào',
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
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: filteredTasks.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final task = filteredTasks[index];
                      return _buildTaskCard(context, task, dataService);
                    },
                  ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildFilterChip(BuildContext context, String label, String value) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isSelected = _statusFilter == value;

    return FilterChip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: isSelected
              ? Colors.white
              : (isDark ? const Color(0xFF94A3B8) : const Color(0xFF475569)),
        ),
      ),
      selected: isSelected,
      onSelected: (_) => setState(() => _statusFilter = value),
      selectedColor: AppColors.primary,
      backgroundColor: isDark ? AppColors.surfaceDark : const Color(0xFFF1F5F9),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: isSelected ? AppColors.primary : theme.colorScheme.outline,
        ),
      ),
      showCheckmark: false,
    );
  }

  Widget _buildTaskCard(
    BuildContext context,
    TaskItem task,
    MockDataService service,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Checkbox(
              value: task.isCompleted,
              activeColor: AppColors.accent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(6),
              ),
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
                      color: task.isCompleted
                          ? (isDark
                                ? const Color(0xFF64748B)
                                : const Color(0xFF94A3B8))
                          : theme.colorScheme.onSurface,
                      decoration: task.isCompleted
                          ? TextDecoration.lineThrough
                          : null,
                    ),
                  ),
                  if (task.description != null &&
                      task.description!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      task.description!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: task.isCompleted
                            ? (isDark
                                  ? const Color(0xFF475569)
                                  : const Color(0xFF94A3B8))
                            : (isDark
                                  ? const Color(0xFF94A3B8)
                                  : const Color(0xFF64748B)),
                      ),
                    ),
                  ],
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      // Priority Badge
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: task.priority.color.withAlpha(
                            isDark ? 25 : 20,
                          ),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: task.priority.color.withAlpha(
                              isDark ? 70 : 50,
                            ),
                          ),
                        ),
                        child: Text(
                          task.priority.label,
                          style: TextStyle(
                            color: task.priority.color,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Category Tag
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: isDark
                              ? const Color(0xFF334155)
                              : const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          task.category,
                          style: TextStyle(
                            color: isDark
                                ? const Color(0xFFCBD5E1)
                                : const Color(0xFF475569),
                            fontSize: 11,
                          ),
                        ),
                      ),
                      if (task.deadline != null) ...[
                        const Spacer(),
                        Icon(
                          Icons.schedule_rounded,
                          size: 13,
                          color: task.isCompleted
                              ? const Color(0xFF94A3B8)
                              : AppColors.warning,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          DateFormat('dd/MM HH:mm').format(task.deadline!),
                          style: TextStyle(
                            fontSize: 11,
                            color: task.isCompleted
                                ? const Color(0xFF94A3B8)
                                : AppColors.warning,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            IconButton(
              icon: Icon(
                Icons.close_rounded,
                size: 16,
                color: isDark
                    ? const Color(0xFF64748B)
                    : const Color(0xFF94A3B8),
              ),
              onPressed: () => service.deleteTask(task.id),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEisenhowerMatrixView(
    BuildContext context,
    List<TaskItem> allTasks,
    MockDataService service,
  ) {
    // 4 Quadrants
    final q1 = allTasks
        .where((t) => t.isUrgentQuadrant && t.isImportant)
        .toList();
    final q2 = allTasks
        .where((t) => !t.isUrgentQuadrant && t.isImportant)
        .toList();
    final q3 = allTasks
        .where((t) => t.isUrgentQuadrant && !t.isImportant)
        .toList();
    final q4 = allTasks
        .where((t) => !t.isUrgentQuadrant && !t.isImportant)
        .toList();

    return Column(
      children: [
        _buildMatrixQuadrant(
          context: context,
          title: '🔥 Khẩn cấp & Quan trọng (Làm ngay)',
          subtitle: 'Nhiệm vụ quyết định, áp lực hạn chót',
          tasks: q1,
          badgeColor: AppColors.expense,
          service: service,
        ),
        const SizedBox(height: 12),
        _buildMatrixQuadrant(
          context: context,
          title: '🎯 Quan trọng & Không khẩn cấp (Lập kế hoạch)',
          subtitle: 'Mục tiêu chiến lược, phát triển bản thân',
          tasks: q2,
          badgeColor: AppColors.info,
          service: service,
        ),
        const SizedBox(height: 12),
        _buildMatrixQuadrant(
          context: context,
          title: '⚡ Khẩn cấp & Ít quan trọng (Ủy quyền / Tối ưu)',
          subtitle: 'Việc gián đoạn, thao tác nhanh',
          tasks: q3,
          badgeColor: AppColors.warning,
          service: service,
        ),
        const SizedBox(height: 12),
        _buildMatrixQuadrant(
          context: context,
          title: '💤 Không khẩn cấp & Không quan trọng (Hạn chế)',
          subtitle: 'Việc gây xao nhãng, có thể dời lại',
          tasks: q4,
          badgeColor: const Color(0xFF64748B),
          service: service,
        ),
      ],
    );
  }

  Widget _buildMatrixQuadrant({
    required BuildContext context,
    required String title,
    required String subtitle,
    required List<TaskItem> tasks,
    required Color badgeColor,
    required MockDataService service,
  }) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: badgeColor.withAlpha(isDark ? 80 : 50),
          width: 1.2,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          color: badgeColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      Text(
                        subtitle,
                        style: TextStyle(
                          color: isDark
                              ? const Color(0xFF94A3B8)
                              : const Color(0xFF64748B),
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: badgeColor.withAlpha(isDark ? 30 : 20),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${tasks.where((t) => !t.isCompleted).length} việc',
                    style: TextStyle(
                      color: badgeColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (tasks.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  'Không có nhiệm vụ nào trong nhóm này',
                  style: TextStyle(
                    color: isDark
                        ? const Color(0xFF64748B)
                        : const Color(0xFF94A3B8),
                    fontSize: 12,
                  ),
                ),
              )
            else
              ...tasks.map(
                (task) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 24,
                        height: 24,
                        child: Checkbox(
                          value: task.isCompleted,
                          activeColor: AppColors.accent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4),
                          ),
                          onChanged: (_) => service.toggleTask(task.id),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          task.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 13,
                            color: task.isCompleted
                                ? (isDark
                                      ? const Color(0xFF64748B)
                                      : const Color(0xFF94A3B8))
                                : theme.colorScheme.onSurface,
                            decoration: task.isCompleted
                                ? TextDecoration.lineThrough
                                : null,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  void _showAddTaskBottomSheet(BuildContext context, MockDataService service) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final titleController = TextEditingController();
    final descController = TextEditingController();
    Priority priority = Priority.high;
    bool isImportant = true;
    DateTime? selectedDeadline = DateTime.now().add(const Duration(hours: 12));
    String category = 'Cuộc thi';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) {
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
                  'Tạo công việc mới',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 16),

                // Title
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(
                    labelText: 'Tiêu đề công việc',
                    prefixIcon: Icon(
                      Icons.task_alt_rounded,
                      color: AppColors.primary,
                    ),
                    hintText: 'Ví dụ: Hoàn tất slide thuyết trình',
                  ),
                ),
                const SizedBox(height: 12),

                // Description
                TextField(
                  controller: descController,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Mô tả chi tiết (tùy chọn)',
                    prefixIcon: Icon(
                      Icons.notes_rounded,
                      color: AppColors.primary,
                    ),
                    hintText: 'Ghi chú thêm về yêu cầu, checklist...',
                  ),
                ),
                const SizedBox(height: 16),

                // Priority Selector M3
                Text(
                  'Mức độ ưu tiên:',
                  style: TextStyle(
                    fontSize: 13,
                    color: isDark
                        ? const Color(0xFF94A3B8)
                        : const Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: Priority.values.map((p) {
                    final isSel = priority == p;
                    return Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: ChoiceChip(
                        label: Text(
                          p.label,
                          style: TextStyle(
                            fontSize: 11,
                            color: isSel
                                ? Colors.white
                                : (isDark
                                      ? const Color(0xFF94A3B8)
                                      : const Color(0xFF475569)),
                          ),
                        ),
                        selected: isSel,
                        selectedColor: p.color,
                        backgroundColor: isDark
                            ? const Color(0xFF0F172A)
                            : const Color(0xFFF1F5F9),
                        onSelected: (_) => setModalState(() => priority = p),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),

                // Importance switch (Eisenhower)
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    'Tính chất Quan trọng (Eisenhower)',
                    style: TextStyle(
                      fontSize: 13,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  subtitle: Text(
                    'Đánh dấu việc có tác động dài hạn',
                    style: TextStyle(
                      fontSize: 11,
                      color: isDark
                          ? const Color(0xFF94A3B8)
                          : const Color(0xFF64748B),
                    ),
                  ),
                  value: isImportant,
                  thumbColor: const WidgetStatePropertyAll(AppColors.primary),
                  onChanged: (val) => setModalState(() => isImportant = val),
                ),
                const SizedBox(height: 8),

                // Deadline Picker Button
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(
                    Icons.calendar_month_rounded,
                    color: AppColors.warning,
                  ),
                  title: Text(
                    selectedDeadline != null
                        ? 'Hạn chót: ${DateFormat('dd/MM/yyyy HH:mm', 'vi').format(selectedDeadline!)}'
                        : 'Chưa đặt hạn chót',
                    style: TextStyle(
                      fontSize: 13,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  trailing: TextButton(
                    onPressed: () async {
                      final pickedDate = await showDatePicker(
                        context: context,
                        initialDate: selectedDeadline ?? DateTime.now(),
                        firstDate: DateTime.now().subtract(
                          const Duration(days: 1),
                        ),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (pickedDate != null) {
                        setModalState(() {
                          selectedDeadline = DateTime(
                            pickedDate.year,
                            pickedDate.month,
                            pickedDate.day,
                            18,
                            0,
                          );
                        });
                      }
                    },
                    child: const Text(
                      'Chọn ngày',
                      style: TextStyle(color: AppColors.primary),
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Submit Button
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: () {
                      final title = titleController.text.trim();
                      if (title.isNotEmpty) {
                        service.addTask(
                          TaskItem(
                            id: 't_${DateTime.now().millisecondsSinceEpoch}',
                            title: title,
                            description: descController.text.trim().isEmpty
                                ? null
                                : descController.text.trim(),
                            deadline: selectedDeadline,
                            priority: priority,
                            isImportant: isImportant,
                            category: category,
                          ),
                        );
                        Navigator.pop(ctx);
                      }
                    },
                    child: const Text('Lưu công việc'),
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
