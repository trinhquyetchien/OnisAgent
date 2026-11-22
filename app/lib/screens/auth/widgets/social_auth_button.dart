import 'package:flutter/material.dart';

class SocialAuthButton extends StatelessWidget {
  final String provider; // 'Google' | 'Apple'
  final VoidCallback? onPressed;
  final bool isLoading;

  const SocialAuthButton({
    super.key,
    required this.provider,
    this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isGoogle = provider.toLowerCase() == 'google';

    return OutlinedButton(
      onPressed: isLoading ? null : onPressed,
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        side: BorderSide(
          color: theme.colorScheme.outline,
          width: 1,
        ),
        backgroundColor: isDark ? const Color(0xFF1E293B) : Colors.white,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            isGoogle ? Icons.g_mobiledata_rounded : Icons.apple_rounded,
            size: isGoogle ? 24 : 22,
            color: isGoogle
                ? const Color(0xFFEA4335)
                : (isDark ? Colors.white : Colors.black),
          ),
          const SizedBox(width: 8),
          Text(
            provider,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.white : const Color(0xFF0F172A),
            ),
          ),
        ],
      ),
    );
  }
}
