import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'screens/home_screen.dart';
import 'screens/finance_screen.dart';
import 'screens/tasks_screen.dart';
import 'screens/deadlines_screen.dart';
import 'screens/assistant_screen.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('vi', null);
  runApp(const OnisApp());
}

class OnisApp extends StatelessWidget {
  const OnisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'OnisAgent | Quản lý Tài chính & Công việc',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const MainNavigationShell(),
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

  @override
  Widget build(BuildContext context) {
    final isDesktopOrWeb = MediaQuery.of(context).size.width >= 850;

    final List<Widget> pages = [
      HomeScreen(
        onNavigateToFinance: () => setState(() => _selectedIndex = 1),
        onNavigateToTasks: () => setState(() => _selectedIndex = 2),
        onNavigateToDeadlines: () => setState(() => _selectedIndex = 3),
      ),
      const FinanceScreen(),
      const TasksScreen(),
      const DeadlinesScreen(),
      const AssistantScreen(),
    ];

    final navigationDestinations = const [
      NavigationDestination(
        icon: Icon(Icons.dashboard_outlined),
        selectedIcon: Icon(Icons.dashboard_rounded, color: AppColors.primaryLight),
        label: 'Tổng quan',
      ),
      NavigationDestination(
        icon: Icon(Icons.account_balance_wallet_outlined),
        selectedIcon: Icon(Icons.account_balance_wallet_rounded, color: AppColors.primaryLight),
        label: 'Tài chính',
      ),
      NavigationDestination(
        icon: Icon(Icons.task_alt_outlined),
        selectedIcon: Icon(Icons.task_alt_rounded, color: AppColors.primaryLight),
        label: 'Công việc',
      ),
      NavigationDestination(
        icon: Icon(Icons.alarm_on_outlined),
        selectedIcon: Icon(Icons.alarm_on_rounded, color: AppColors.primaryLight),
        label: 'Deadline',
      ),
      NavigationDestination(
        icon: Icon(Icons.smart_toy_outlined),
        selectedIcon: Icon(Icons.smart_toy_rounded, color: AppColors.primaryLight),
        label: 'Trợ lý AI',
      ),
    ];

    if (isDesktopOrWeb) {
      // Desktop / Web layout with Sidebar NavigationRail
      return Scaffold(
        body: Row(
          children: [
            Container(
              decoration: const BoxDecoration(
                color: AppColors.surfaceDark,
                border: Border(right: BorderSide(color: Color(0xFF334155), width: 1)),
              ),
              child: NavigationRail(
                selectedIndex: _selectedIndex,
                onDestinationSelected: (index) => setState(() => _selectedIndex = index),
                backgroundColor: AppColors.surfaceDark,
                extended: MediaQuery.of(context).size.width >= 1100,
                minExtendedWidth: 220,
                leading: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.bolt_rounded, color: Colors.white, size: 24),
                      ),
                      if (MediaQuery.of(context).size.width >= 1100) ...[
                        const SizedBox(width: 12),
                        const Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'OnisAgent',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                            ),
                            Text(
                              'AI Task & Finance',
                              style: TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
                destinations: const [
                  NavigationRailDestination(
                    icon: Icon(Icons.dashboard_outlined),
                    selectedIcon: Icon(Icons.dashboard_rounded, color: AppColors.primaryLight),
                    label: Text('Tổng quan'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.account_balance_wallet_outlined),
                    selectedIcon: Icon(Icons.account_balance_wallet_rounded, color: AppColors.primaryLight),
                    label: Text('Tài chính'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.task_alt_outlined),
                    selectedIcon: Icon(Icons.task_alt_rounded, color: AppColors.primaryLight),
                    label: Text('Công việc'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.alarm_on_outlined),
                    selectedIcon: Icon(Icons.alarm_on_rounded, color: AppColors.primaryLight),
                    label: Text('Deadline'),
                  ),
                  NavigationRailDestination(
                    icon: Icon(Icons.smart_toy_outlined),
                    selectedIcon: Icon(Icons.smart_toy_rounded, color: AppColors.primaryLight),
                    label: Text('Trợ lý AI'),
                  ),
                ],
              ),
            ),
            Expanded(child: pages[_selectedIndex]),
          ],
        ),
      );
    } else {
      // Mobile layout with Bottom Navigation Bar
      return Scaffold(
        appBar: AppBar(
          title: const Text('OnisAgent', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        body: pages[_selectedIndex],
        bottomNavigationBar: NavigationBar(
          selectedIndex: _selectedIndex,
          onDestinationSelected: (index) => setState(() => _selectedIndex = index),
          backgroundColor: AppColors.surfaceDark,
          indicatorColor: AppColors.primary.withAlpha(50),
          destinations: navigationDestinations,
        ),
      );
    }
  }
}
