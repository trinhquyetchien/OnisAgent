import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/models/auth_user.dart';
import 'package:app/services/auth/mock_auth_service.dart';
import 'package:app/services/auth/auth_state_notifier.dart';
import 'package:app/screens/auth/login_screen.dart';
import 'package:app/screens/auth/register_screen.dart';
import 'package:app/screens/auth/email_verification_screen.dart';
import 'package:app/screens/auth/forgot_password_screen.dart';
import 'package:app/screens/auth/reset_password_screen.dart';
import 'package:app/theme/app_theme.dart';

void main() {
  group('MockAuthService Unit Tests', () {
    late MockAuthService authService;

    setUp(() {
      authService = MockAuthService();
    });

    test('Login with valid demo credentials succeeds', () async {
      final session = await authService.login(
        email: 'demo@onis.ai',
        password: 'password123',
      );
      expect(session.user.email, 'demo@onis.ai');
      expect(session.user.isEmailVerified, isTrue);
      expect(session.token.accessToken, isNotEmpty);
    });

    test('Login with wrong password throws AuthException', () async {
      expect(
        () => authService.login(
          email: 'demo@onis.ai',
          password: 'wrong_password',
        ),
        throwsA(isA<AuthException>()),
      );
    });

    test(
      'Login with unverified account returns isEmailVerified false',
      () async {
        final session = await authService.login(
          email: 'unverified@onis.ai',
          password: 'password123',
        );
        expect(session.user.isEmailVerified, isFalse);
      },
    );

    test(
      'Registering new account creates unverified user and generates OTP',
      () async {
        final testEmail =
            'newuser_${DateTime.now().millisecondsSinceEpoch}@onis.ai';
        final session = await authService.register(
          fullName: 'Nguyễn Văn Mới',
          email: testEmail,
          password: 'password123',
        );

        expect(session.user.email, testEmail);
        expect(session.user.isEmailVerified, isFalse);

        // Verify OTP with default mock code 123456
        final verified = await authService.verifyOtp(
          email: testEmail,
          otp: '123456',
          purpose: OtpPurpose.emailVerification,
        );
        expect(verified, isTrue);
      },
    );

    test('Forgot password and reset password flow works', () async {
      const email = 'demo@onis.ai';
      final sent = await authService.sendForgotPasswordOtp(email: email);
      expect(sent, isTrue);

      final resetSuccess = await authService.resetPassword(
        email: email,
        otp: '123456',
        newPassword: 'newPassword456',
      );
      expect(resetSuccess, isTrue);

      // Login with new password
      final session = await authService.login(
        email: email,
        password: 'newPassword456',
      );
      expect(session.user.email, email);

      // Restore original password
      await authService.changePassword(
        oldPassword: 'newPassword456',
        newPassword: 'password123',
      );
    });

    test('Change password enforces old password check', () async {
      await authService.login(email: 'demo@onis.ai', password: 'password123');
      expect(
        () => authService.changePassword(
          oldPassword: 'wrong_old_password',
          newPassword: 'newPassword456',
        ),
        throwsA(isA<AuthException>()),
      );
    });
  });

  group('Password Strength Calculation', () {
    test('Calculates weak, medium, and strong correctly', () {
      expect(PasswordStrengthExtension.calculate(''), PasswordStrength.empty);
      expect(PasswordStrengthExtension.calculate('123'), PasswordStrength.weak);
      expect(
        PasswordStrengthExtension.calculate('onlylower'),
        PasswordStrength.weak,
      );
      expect(
        PasswordStrengthExtension.calculate('shortA1'),
        PasswordStrength.medium,
      );
      expect(
        PasswordStrengthExtension.calculate('Password123'),
        PasswordStrength.strong,
      );
    });
  });

  group('AuthStateNotifier Tests', () {
    test('Login and logout update status correctly', () async {
      final notifier = AuthStateNotifier();
      notifier.setAuthService(MockAuthService());

      final success = await notifier.login(
        email: 'demo@onis.ai',
        password: 'password123',
      );
      expect(success, isTrue);
      expect(notifier.status, AuthStatus.authenticated);
      expect(notifier.currentUser?.fullName, 'Nguyễn Văn An');

      await notifier.logout();
      expect(notifier.status, AuthStatus.unauthenticated);
      expect(notifier.currentUser, isNull);
    });

    test('Login with unverified user sets status to unverified', () async {
      final notifier = AuthStateNotifier();
      notifier.setAuthService(MockAuthService());

      final success = await notifier.login(
        email: 'unverified@onis.ai',
        password: 'password123',
      );
      expect(success, isTrue);
      expect(notifier.status, AuthStatus.unverified);
      expect(notifier.pendingVerificationEmail, 'unverified@onis.ai');

      await notifier.logout();
    });
  });

  group('Authentication UI Widget Tests', () {
    Widget buildTestableWidget(Widget child) {
      return MaterialApp(
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        home: child,
      );
    }

    testWidgets('LoginScreen renders fields without demo account shortcuts', (
      tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const LoginScreen()));
      await tester.pump();

      expect(find.textContaining('Chào mừng trở lại'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Mật khẩu'), findsOneWidget);
      expect(find.text('Đăng nhập'), findsWidgets);
      expect(find.text('Ghi nhớ đăng nhập'), findsOneWidget);
      expect(find.text('Quên mật khẩu?'), findsOneWidget);
      expect(find.text('Google'), findsOneWidget);
      expect(find.text('Apple'), findsNothing);
      expect(find.text('Tài khoản Demo thử nghiệm:'), findsNothing);
      expect(find.text('Demo (Đã verify)'), findsNothing);
    });

    testWidgets(
      'RegisterScreen renders fields and password strength indicator',
      (tester) async {
        await tester.pumpWidget(buildTestableWidget(const RegisterScreen()));
        await tester.pump();

        expect(find.textContaining('Tạo tài khoản mới'), findsOneWidget);
        expect(find.text('Họ và tên'), findsOneWidget);
        expect(find.text('Email'), findsOneWidget);
        expect(find.text('Mật khẩu'), findsOneWidget);
        expect(find.text('Xác nhận mật khẩu'), findsOneWidget);
        expect(find.text('Đăng ký tài khoản'), findsOneWidget);

        // Enter password and verify strength meter reacts
        await tester.enterText(
          find.widgetWithText(TextFormField, '').first,
          'Nguyễn An',
        );
        await tester.pump();
      },
    );

    testWidgets('EmailVerificationScreen renders OTP fields and countdown', (
      tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(
          const EmailVerificationScreen(email: 'test@onis.ai'),
        ),
      );
      await tester.pump();

      expect(find.textContaining('Xác thực Email'), findsOneWidget);
      expect(find.text('test@onis.ai'), findsOneWidget);
      expect(find.textContaining('Mã xác nhận 6 chữ số'), findsOneWidget);
      expect(find.textContaining('Gửi lại mã sau'), findsOneWidget);
      expect(find.text('Xác thực & Kích hoạt'), findsOneWidget);

      // Clean up widget to cancel periodic timer
      await tester.pumpWidget(const SizedBox());
    });

    testWidgets('ForgotPasswordScreen renders email field', (tester) async {
      await tester.pumpWidget(
        buildTestableWidget(
          const ForgotPasswordScreen(initialEmail: 'demo@onis.ai'),
        ),
      );
      await tester.pump();

      expect(find.textContaining('Quên mật khẩu'), findsOneWidget);
      expect(find.text('Gửi mã xác thực OTP'), findsOneWidget);
    });

    testWidgets('ResetPasswordScreen renders OTP and new password fields', (
      tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(const ResetPasswordScreen(email: 'demo@onis.ai')),
      );
      await tester.pump();

      expect(find.textContaining('Đặt lại mật khẩu'), findsOneWidget);
      expect(find.text('Mã xác thực OTP'), findsOneWidget);
      expect(find.text('Mật khẩu mới'), findsOneWidget);
      expect(find.text('Cập nhật mật khẩu mới'), findsOneWidget);
    });
  });
}
