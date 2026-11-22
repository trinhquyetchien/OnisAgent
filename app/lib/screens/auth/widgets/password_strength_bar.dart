import 'package:flutter/material.dart';
import '../../../models/auth_user.dart';

class PasswordStrengthBar extends StatelessWidget {
  final String password;

  const PasswordStrengthBar({
    super.key,
    required this.password,
  });

  @override
  Widget build(BuildContext context) {
    if (password.isEmpty) return const SizedBox.shrink();

    final strength = PasswordStrengthExtension.calculate(password);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final hasMinLength = password.length >= 8;
    final hasUpperLower = RegExp(r'[A-Z]').hasMatch(password) && RegExp(r'[a-z]').hasMatch(password);
    final hasNumberOrSpecial = RegExp(r'[0-9]').hasMatch(password) || RegExp(r'[!@#$&*~_.]').hasMatch(password);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: strength.fraction,
                  backgroundColor: isDark ? const Color(0xFF334155) : const Color(0xFFE2E8F0),
                  color: strength.color,
                  minHeight: 5,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Text(
              'Độ mạnh: ${strength.label}',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: strength.color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 12,
          runSpacing: 4,
          children: [
            _buildCriteriaItem(context, 'Tối thiểu 8 ký tự', hasMinLength),
            _buildCriteriaItem(context, 'Chữ hoa & thường', hasUpperLower),
            _buildCriteriaItem(context, 'Chữ số / Ký tự đặc biệt', hasNumberOrSpecial),
          ],
        ),
      ],
    );
  }

  Widget _buildCriteriaItem(BuildContext context, String text, bool satisfied) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          satisfied ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
          size: 13,
          color: satisfied
              ? const Color(0xFF10B981)
              : (isDark ? const Color(0xFF64748B) : const Color(0xFF94A3B8)),
        ),
        const SizedBox(width: 4),
        Text(
          text,
          style: TextStyle(
            fontSize: 11,
            fontWeight: satisfied ? FontWeight.w600 : FontWeight.normal,
            color: satisfied
                ? (isDark ? const Color(0xFFE2E8F0) : const Color(0xFF1E293B))
                : (isDark ? const Color(0xFF64748B) : const Color(0xFF94A3B8)),
          ),
        ),
      ],
    );
  }
}
