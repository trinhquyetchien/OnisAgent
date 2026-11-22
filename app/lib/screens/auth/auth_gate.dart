import 'package:flutter/material.dart';
import '../../services/auth/auth_state_notifier.dart';
import '../../theme/app_theme.dart';
import '../auth/login_screen.dart';
import '../auth/email_verification_screen.dart';
import '../../main.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  final _authNotifier = AuthStateNotifier();

  @override
  void initState() {
    super.initState();
    // Khởi chạy kiểm tra trạng thái phiên khi app khởi động
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _authNotifier.checkAuth();
    });
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _authNotifier,
      builder: (context, _) {
        switch (_authNotifier.status) {
          case AuthStatus.initial:
            return const _AuthSplashScreen();
          case AuthStatus.authenticated:
            return const MainNavigationShell();
          case AuthStatus.unverified:
            return EmailVerificationScreen(
              email: _authNotifier.pendingVerificationEmail ?? '',
            );
          case AuthStatus.unauthenticated:
            return const LoginScreen();
        }
      },
    );
  }
}

class _AuthSplashScreen extends StatelessWidget {
  const _AuthSplashScreen();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withAlpha(isDark ? 80 : 100),
                    blurRadius: 24,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: const Icon(
                Icons.bolt_rounded,
                color: Colors.white,
                size: 48,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'OnisAgent',
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
                letterSpacing: -0.5,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Hệ thống quản lý Tài chính & Công việc thông minh',
              style: TextStyle(
                fontSize: 13,
                color: isDark
                    ? const Color(0xFF94A3B8)
                    : const Color(0xFF64748B),
              ),
            ),
            const SizedBox(height: 36),
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                color: AppColors.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
