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
  String _selectedFilter = 'Tất cả';

  @override
  Widget build(BuildContext context) {
    final dataService = MockDataService();

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final filteredTasks = dataService.tasks.where((task) {
          if (_selectedFilter == 'Chưa xong') return !task.isCompleted;
          if (_selectedFilter == 'Đã hoàn thành') return task.isCompleted;
          return true;
        }).toList();

        final pendingCount = dataService.tasks.where((t) => !t.isCompleted).length;
        final completedCount = dataService.tasks.where((t) => t.isCompleted).length;

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Quản Lý Công Việc',
                        style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '$pendingCount việc cần làm • $completedCount việc đã hoàn thành',
                        style: const TextStyle(color: Colors.grey, fontSize: 14),
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
                    onPressed: () => _showAddTaskDialog(context),
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Tạo công việc'),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Filter Chips
              Row(
                children: ['Tất cả', 'Chưa xong', 'Đã hoàn thành'].map((filter) {
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
              const SizedBox(height: 20),

              // Task List
              if (filteredTasks.isEmpty)
                Container(
                  padding: const EdgeInsets.all(40),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.surfaceDark,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF334155)),
                  ),
                  child: const Column(
                    children: [
                      Icon(Icons.task_alt_rounded, size: 48, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('Không có công việc nào', style: TextStyle(color: Colors.grey, fontSize: 16)),
                    ],
                  ),
                )
              else
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: filteredTasks.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final task = filteredTasks[index];
                    return _buildTaskCard(task, dataService);
                  },
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTaskCard(TaskItem task, MockDataService dataService) {
    Color priorityColor;
    String priorityText;
    switch (task.priority) {
      case Priority.urgent:
        priorityColor = AppColors.expense;
        priorityText = 'Khẩn cấp';
        break;
      case Priority.high:
        priorityColor = AppColors.warning;
        priorityText = 'Ưu tiên cao';
        break;
      case Priority.medium:
        priorityColor = AppColors.info;
        priorityText = 'Bình thường';
        break;
      case Priority.low:
        priorityColor = Colors.grey;
        priorityText = 'Thấp';
        break;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: task.isCompleted ? const Color(0xFF1E293B) : const Color(0xFF334155),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Checkbox(
            value: task.isCompleted,
            activeColor: AppColors.accent,
            onChanged: (_) => dataService.toggleTask(task.id),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: priorityColor.withAlpha(30),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        priorityText,
                        style: TextStyle(color: priorityColor, fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.cardDark,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        task.category,
                        style: const TextStyle(color: Colors.grey, fontSize: 11),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  task.title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    decoration: task.isCompleted ? TextDecoration.lineThrough : null,
                    color: task.isCompleted ? Colors.grey : Colors.white,
                  ),
                ),
                if (task.description != null && task.description!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    task.description!,
                    style: TextStyle(
                      color: Colors.grey[400],
                      fontSize: 13,
                      decoration: task.isCompleted ? TextDecoration.lineThrough : null,
                    ),
                  ),
                ],
                if (task.deadline != null) ...[
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      const Icon(Icons.schedule_rounded, size: 14, color: AppColors.warning),
                      const SizedBox(width: 4),
                      Text(
                        DateFormat('HH:mm - dd/MM/yyyy').format(task.deadline!),
                        style: const TextStyle(color: AppColors.warning, fontSize: 12, fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.grey, size: 20),
            onPressed: () => dataService.deleteTask(task.id),
          ),
        ],
      ),
    );
  }

  void _showAddTaskDialog(BuildContext context) {
    final titleController = TextEditingController();
    final descController = TextEditingController();
    Priority priority = Priority.medium;
    DateTime? selectedDate = DateTime.now().add(const Duration(days: 1));

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setModalState) => AlertDialog(
          backgroundColor: AppColors.surfaceDark,
          title: const Text('Tạo Công Việc Mới'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(
                    labelText: 'Tiêu đề công việc *',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: descController,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Mô tả chi tiết',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<Priority>(
                  initialValue: priority,
                  decoration: const InputDecoration(
                    labelText: 'Mức độ ưu tiên',
                    border: OutlineInputBorder(),
                  ),
                  items: const [
                    DropdownMenuItem(value: Priority.low, child: Text('Thấp')),
                    DropdownMenuItem(value: Priority.medium, child: Text('Bình thường')),
                    DropdownMenuItem(value: Priority.high, child: Text('Ưu tiên cao')),
                    DropdownMenuItem(value: Priority.urgent, child: Text('Khẩn cấp')),
                  ],
                  onChanged: (p) => setModalState(() => priority = p ?? Priority.medium),
                ),
                const SizedBox(height: 16),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.calendar_month_rounded, color: AppColors.primaryLight),
                  title: Text(
                    selectedDate != null
                        ? 'Hạn chót: ${DateFormat('dd/MM/yyyy').format(selectedDate!)}'
                        : 'Chọn hạn chót',
                  ),
                  trailing: TextButton(
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: selectedDate ?? DateTime.now(),
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (picked != null) {
                        setModalState(() => selectedDate = picked);
                      }
                    },
                    child: const Text('Thay đổi'),
                  ),
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
                if (titleController.text.isNotEmpty) {
                  MockDataService().addTask(
                    TaskItem(
                      id: DateTime.now().millisecondsSinceEpoch.toString(),
                      title: titleController.text,
                      description: descController.text,
                      deadline: selectedDate,
                      priority: priority,
                    ),
                  );
                  Navigator.pop(dialogCtx);
                }
              },
              child: const Text('Tạo', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }
}
