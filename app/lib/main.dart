import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'screens/auth/auth_gate.dart';
import 'screens/auth/user_profile_dialog.dart';
import 'screens/home_screen.dart';
import 'screens/finance_screen.dart';
import 'screens/tasks_screen.dart';
import 'screens/deadlines_screen.dart';
import 'screens/assistant_screen.dart';
import 'services/auth/auth_state_notifier.dart';
import 'services/app_data_service.dart';
import 'theme/app_theme.dart';

// Global Theme Controller: Mặc định Light Mode, hỗ trợ chuyển đổi tức thì
final ValueNotifier<ThemeMode> appThemeModeNotifier = ValueNotifier<ThemeMode>(
  ThemeMode.light,
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('vi', null);
  runApp(const OnisApp());
}

class OnisApp extends StatelessWidget {
  const OnisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: appThemeModeNotifier,
      builder: (context, themeMode, _) {
        return MaterialApp(
          title: 'OnisAgent | Quản lý Tài chính & Công việc',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: themeMode,
          home: const AuthGate(),
        );
      },
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _selectedIndex = 0;
  late final AppDataService _dataService;

  @override
  void initState() {
    super.initState();
    _dataService = AppDataService();
    unawaited(_dataService.refresh());
  }

  Widget _buildApiErrorBanner(BuildContext context) {
    final message = _dataService.errorMessage;
    if (message == null) return const SizedBox.shrink();
    return MaterialBanner(
      content: Text(message),
      leading: const Icon(Icons.cloud_off_outlined),
      actions: [
        TextButton(
          onPressed: () => unawaited(_dataService.refresh()),
          child: const Text('Thử lại'),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isDesktopOrWeb = MediaQuery.of(context).size.width >= 850;
    final dataService = _dataService;

    final List<Widget> pages = [
      HomeScreen(
        onNavigateToFinance: () => setState(() => _selectedIndex = 1),
        onNavigateToTasks: () => setState(() => _selectedIndex = 2),
        onNavigateToDeadlines: () => setState(() => _selectedIndex = 3),
        onNavigateToAssistant: () => setState(() => _selectedIndex = 4),
      ),
      const FinanceScreen(),
      const TasksScreen(),
      const DeadlinesScreen(),
      const AssistantScreen(),
    ];

    return ListenableBuilder(
      listenable: dataService,
      builder: (context, _) {
        final pendingTasks = dataService.pendingTasksCount;
        final urgentDeadlines = dataService.urgentDeadlinesCount;

        final navigationDestinations = [
          NavigationDestination(
            icon: const Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(
              Icons.dashboard_rounded,
              color: theme.colorScheme.primary,
            ),
            label: 'Tổng quan',
          ),
          NavigationDestination(
            icon: const Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(
              Icons.account_balance_wallet_rounded,
              color: theme.colorScheme.primary,
            ),
            label: 'Tài chính',
          ),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: pendingTasks > 0,
              label: Text('$pendingTasks'),
              backgroundColor: AppColors.warning,
              child: const Icon(Icons.task_alt_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: pendingTasks > 0,
              label: Text('$pendingTasks'),
              backgroundColor: AppColors.warning,
              child: Icon(
                Icons.task_alt_rounded,
                color: theme.colorScheme.primary,
              ),
            ),
            label: 'Công việc',
          ),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: urgentDeadlines > 0,
              label: Text('$urgentDeadlines'),
              backgroundColor: AppColors.expense,
              child: const Icon(Icons.alarm_on_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: urgentDeadlines > 0,
              label: Text('$urgentDeadlines'),
              backgroundColor: AppColors.expense,
              child: Icon(
                Icons.alarm_on_rounded,
                color: theme.colorScheme.primary,
              ),
            ),
            label: 'Deadline',
          ),
          NavigationDestination(
            icon: const Icon(Icons.smart_toy_outlined),
            selectedIcon: Icon(
              Icons.smart_toy_rounded,
              color: theme.colorScheme.primary,
            ),
            label: 'Trợ lý AI',
          ),
        ];

        if (isDesktopOrWeb) {
          // Desktop / Web layout with Sidebar NavigationRail
          return Scaffold(
            body: Row(
              children: [
                Container(
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    border: Border(
                      right: BorderSide(
                        color: theme.colorScheme.outline,
                        width: 1,
                      ),
                    ),
                  ),
                  child: NavigationRail(
                    selectedIndex: _selectedIndex,
                    onDestinationSelected: (index) =>
                        setState(() => _selectedIndex = index),
                    backgroundColor: theme.colorScheme.surface,
                    extended: MediaQuery.of(context).size.width >= 1100,
                    minExtendedWidth: 220,
                    leading: Padding(
                      padding: const EdgeInsets.symmetric(
                        vertical: 24,
                        horizontal: 16,
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.primary,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(
                              Icons.bolt_rounded,
                              color: Colors.white,
                              size: 24,
                            ),
                          ),
                          if (MediaQuery.of(context).size.width >= 1100) ...[
                            const SizedBox(width: 12),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'OnisAgent',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: theme.colorScheme.onSurface,
                                  ),
                                ),
                                Text(
                                  'AI Task & Finance',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: isDark
                                        ? const Color(0xFF94A3B8)
                                        : const Color(0xFF64748B),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                    trailing: Expanded(
                      child: Align(
                        alignment: Alignment.bottomCenter,
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 24),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton.filledTonal(
                                icon: Icon(
                                  isDark
                                      ? Icons.light_mode_rounded
                                      : Icons.dark_mode_rounded,
                                  size: 20,
                                ),
                                tooltip: isDark
                                    ? 'Chuyển sang Giao diện Sáng'
                                    : 'Chuyển sang Giao diện Tối',
                                onPressed: () {
                                  appThemeModeNotifier.value = isDark
                                      ? ThemeMode.light
                                      : ThemeMode.dark;
                                },
                              ),
                              const SizedBox(height: 12),
                              ListenableBuilder(
                                listenable: AuthStateNotifier(),
                                builder: (context, _) {
                                  final user = AuthStateNotifier().currentUser;
                                  final initialChar =
                                      (user != null && user.fullName.isNotEmpty)
                                      ? user.fullName[0].toUpperCase()
                                      : 'U';
                                  return Tooltip(
                                    message:
                                        'Tài khoản: ${user?.fullName ?? ""}',
                                    child: InkWell(
                                      onTap: () =>
                                          UserProfileDialog.show(context),
                                      borderRadius: BorderRadius.circular(20),
                                      child: CircleAvatar(
                                        radius: 16,
                                        backgroundColor: AppColors.primary,
                                        child: Text(
                                          initialChar,
                                          style: const TextStyle(
                                            fontSize: 13,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                          ),
                                        ),
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    destinations: [
                      NavigationRailDestination(
                        icon: const Icon(Icons.dashboard_outlined),
                        selectedIcon: Icon(
                          Icons.dashboard_rounded,
                          color: theme.colorScheme.primary,
                        ),
                        label: const Text('Tổng quan'),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.account_balance_wallet_outlined),
                        selectedIcon: Icon(
                          Icons.account_balance_wallet_rounded,
                          color: theme.colorScheme.primary,
                        ),
                        label: const Text('Tài chính'),
                      ),
                      NavigationRailDestination(
                        icon: Badge(
                          isLabelVisible: pendingTasks > 0,
                          label: Text('$pendingTasks'),
                          backgroundColor: AppColors.warning,
                          child: const Icon(Icons.task_alt_outlined),
                        ),
                        selectedIcon: Badge(
                          isLabelVisible: pendingTasks > 0,
                          label: Text('$pendingTasks'),
                          backgroundColor: AppColors.warning,
                          child: Icon(
                            Icons.task_alt_rounded,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                        label: const Text('Công việc'),
                      ),
                      NavigationRailDestination(
                        icon: Badge(
                          isLabelVisible: urgentDeadlines > 0,
                          label: Text('$urgentDeadlines'),
                          backgroundColor: AppColors.expense,
                          child: const Icon(Icons.alarm_on_outlined),
                        ),
                        selectedIcon: Badge(
                          isLabelVisible: urgentDeadlines > 0,
                          label: Text('$urgentDeadlines'),
                          backgroundColor: AppColors.expense,
                          child: Icon(
                            Icons.alarm_on_rounded,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                        label: const Text('Deadline'),
                      ),
                      NavigationRailDestination(
                        icon: const Icon(Icons.smart_toy_outlined),
                        selectedIcon: Icon(
                          Icons.smart_toy_rounded,
                          color: theme.colorScheme.primary,
                        ),
                        label: const Text('Trợ lý AI'),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    children: [
                      _buildApiErrorBanner(context),
                      Expanded(
                        child: IndexedStack(
                          index: _selectedIndex,
                          children: pages,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        } else {
          // Mobile layout with Bottom Navigation Bar
          return Scaffold(
            appBar: AppBar(
              title: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(
                      Icons.bolt_rounded,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    'OnisAgent',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                ],
              ),
              actions: [
                // Nút chuyển đổi nhanh Light / Dark Mode
                IconButton(
                  icon: Icon(
                    isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
                    color: isDark ? const Color(0xFFFBBF24) : AppColors.primary,
                  ),
                  tooltip: isDark
                      ? 'Chuyển sang Giao diện Sáng'
                      : 'Chuyển sang Giao diện Tối',
                  onPressed: () {
                    appThemeModeNotifier.value = isDark
                        ? ThemeMode.light
                        : ThemeMode.dark;
                  },
                ),
                IconButton(
                  icon: Icon(
                    Icons.smart_toy_rounded,
                    color: theme.colorScheme.primary,
                  ),
                  tooltip: 'Trợ lý AI',
                  onPressed: () => setState(() => _selectedIndex = 4),
                ),
                ListenableBuilder(
                  listenable: AuthStateNotifier(),
                  builder: (context, _) {
                    final user = AuthStateNotifier().currentUser;
                    final initialChar =
                        (user != null && user.fullName.isNotEmpty)
                        ? user.fullName[0].toUpperCase()
                        : 'U';
                    return IconButton(
                      icon: CircleAvatar(
                        radius: 14,
                        backgroundColor: AppColors.primary,
                        child: Text(
                          initialChar,
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      tooltip: 'Tài khoản: ${user?.fullName ?? ""}',
                      onPressed: () => UserProfileDialog.show(context),
                    );
                  },
                ),
                const SizedBox(width: 4),
              ],
            ),
            body: Column(
              children: [
                _buildApiErrorBanner(context),
                Expanded(
                  child: IndexedStack(index: _selectedIndex, children: pages),
                ),
              ],
            ),
            bottomNavigationBar: Container(
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(color: theme.colorScheme.outline, width: 0.8),
                ),
              ),
              child: NavigationBar(
                selectedIndex: _selectedIndex,
                onDestinationSelected: (index) =>
                    setState(() => _selectedIndex = index),
                backgroundColor: theme.colorScheme.surface,
                indicatorColor: theme.colorScheme.primary.withAlpha(
                  isDark ? 40 : 25,
                ),
                destinations: navigationDestinations,
              ),
            ),
          );
        }
      },
    );
  }
}
