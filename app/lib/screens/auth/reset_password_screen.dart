import 'package:flutter/material.dart';
import '../../services/auth/auth_state_notifier.dart';
import '../../theme/app_theme.dart';
import 'widgets/auth_card.dart';
import 'widgets/auth_text_field.dart';
import 'widgets/otp_input_field.dart';
import 'widgets/password_strength_bar.dart';

class ResetPasswordScreen extends StatefulWidget {
  final String email;

  const ResetPasswordScreen({
    super.key,
    required this.email,
  });

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  String _otp = '';
  String _passwordInput = '';

  @override
  void dispose() {
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleReset() async {
    if (_otp.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Vui lòng nhập đủ 6 chữ số mã OTP'),
          backgroundColor: AppColors.warning,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    if (!_formKey.currentState!.validate()) return;

    final authNotifier = AuthStateNotifier();
    final success = await authNotifier.resetPassword(
      email: widget.email,
      otp: _otp,
      newPassword: _newPasswordController.text,
    );

    if (!mounted) return;

    if (!success && authNotifier.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(authNotifier.errorMessage!),
          backgroundColor: AppColors.expense,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else if (success) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (dialogCtx) => AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          icon: const Icon(
            Icons.check_circle_rounded,
            color: AppColors.accent,
            size: 48,
          ),
          title: const Text(
            'Thành công!',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          content: const Text(
            'Mật khẩu của bạn đã được cập nhật thành công. Vui lòng đăng nhập lại với mật khẩu mới.',
            textAlign: TextAlign.center,
          ),
          actionsAlignment: MainAxisAlignment.center,
          actions: [
            FilledButton(
              onPressed: () {
                Navigator.of(dialogCtx).pop();
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: const Text('Đến trang Đăng nhập'),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final authNotifier = AuthStateNotifier();

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(
            Icons.arrow_back_ios_new_rounded,
            size: 20,
            color: theme.colorScheme.onSurface,
          ),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: AuthCard(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withAlpha(isDark ? 40 : 25),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: AppColors.primary.withAlpha(80),
                      ),
                    ),
                    child: const Icon(
                      Icons.password_rounded,
                      color: AppColors.primary,
                      size: 34,
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  'Đặt lại mật khẩu 🔐',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Nhập mã OTP 6 số và thiết lập mật khẩu mới cho:\n${widget.email}',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 13,
                    color: isDark
                        ? const Color(0xFF94A3B8)
                        : const Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 18),

                // Mock Banner
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withAlpha(isDark ? 30 : 20),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: AppColors.accent.withAlpha(isDark ? 80 : 60),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.info_outline_rounded,
                        color: AppColors.accent,
                        size: 16,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Mã OTP thử nghiệm: 123456',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: isDark
                                ? const Color(0xFFA7F3D0)
                                : const Color(0xFF065F46),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // OTP
                Text(
                  'Mã xác thực OTP',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isDark
                        ? const Color(0xFFE2E8F0)
                        : const Color(0xFF334155),
                  ),
                ),
                const SizedBox(height: 8),
                OtpInputField(
                  length: 6,
                  onChanged: (val) => setState(() => _otp = val),
                ),
                const SizedBox(height: 20),

                // New Password
                AuthTextField(
                  controller: _newPasswordController,
                  label: 'Mật khẩu mới',
                  hint: 'Tối thiểu 8 ký tự',
                  prefixIcon: Icons.lock_outline_rounded,
                  isPassword: true,
                  onChanged: (val) => setState(() => _passwordInput = val),
                  validator: (val) {
                    if (val == null || val.isEmpty) {
                      return 'Vui lòng nhập mật khẩu mới';
                    }
                    if (val.length < 8) {
                      return 'Mật khẩu tối thiểu 8 ký tự';
                    }
                    return null;
                  },
                ),
                PasswordStrengthBar(password: _passwordInput),
                const SizedBox(height: 16),

                // Confirm Password
                AuthTextField(
                  controller: _confirmPasswordController,
                  label: 'Xác nhận mật khẩu mới',
                  hint: 'Nhập lại mật khẩu mới',
                  prefixIcon: Icons.lock_reset_rounded,
                  isPassword: true,
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _handleReset(),
                  validator: (val) {
                    if (val == null || val.isEmpty) {
                      return 'Vui lòng xác nhận mật khẩu';
                    }
                    if (val != _newPasswordController.text) {
                      return 'Mật khẩu xác nhận không khớp';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Submit Button
                ListenableBuilder(
                  listenable: authNotifier,
                  builder: (context, _) {
                    final isLoading = authNotifier.isLoading;
                    return FilledButton(
                      onPressed: isLoading ? null : _handleReset,
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.2,
                                color: Colors.white,
                              ),
                            )
                          : const Text(
                              'Cập nhật mật khẩu mới',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.bold,
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
    );
  }
}
