import 'package:flutter/material.dart';

enum OtpPurpose { emailVerification, passwordReset }

enum PasswordStrength { empty, weak, medium, strong }

extension PasswordStrengthExtension on PasswordStrength {
  String get label {
    switch (this) {
      case PasswordStrength.empty:
        return '';
      case PasswordStrength.weak:
        return 'Yếu';
      case PasswordStrength.medium:
        return 'Trung bình';
      case PasswordStrength.strong:
        return 'Mạnh';
    }
  }

  Color get color {
    switch (this) {
      case PasswordStrength.empty:
        return Colors.transparent;
      case PasswordStrength.weak:
        return const Color(0xFFEF4444); // Red
      case PasswordStrength.medium:
        return const Color(0xFFF59E0B); // Amber
      case PasswordStrength.strong:
        return const Color(0xFF10B981); // Emerald
    }
  }

  double get fraction {
    switch (this) {
      case PasswordStrength.empty:
        return 0.0;
      case PasswordStrength.weak:
        return 0.33;
      case PasswordStrength.medium:
        return 0.66;
      case PasswordStrength.strong:
        return 1.0;
    }
  }

  static PasswordStrength calculate(String password) {
    if (password.isEmpty) return PasswordStrength.empty;
    int score = 0;
    if (password.length >= 8) score++;
    if (RegExp(r'[A-Z]').hasMatch(password) &&
        RegExp(r'[a-z]').hasMatch(password)) {
      score++;
    }
    if (RegExp(r'[0-9]').hasMatch(password) ||
        RegExp(r'[!@#$&*~_.]').hasMatch(password)) {
      score++;
    }

    if (score <= 1) return PasswordStrength.weak;
    if (score == 2) return PasswordStrength.medium;
    return PasswordStrength.strong;
  }
}

class AuthUser {
  final String id;
  final String email;
  final String fullName;
  final String? avatarUrl;
  final bool isEmailVerified;
  final DateTime createdAt;

  const AuthUser({
    required this.id,
    required this.email,
    required this.fullName,
    this.avatarUrl,
    this.isEmailVerified = true,
    required this.createdAt,
  });

  AuthUser copyWith({
    String? id,
    String? email,
    String? fullName,
    String? avatarUrl,
    bool? isEmailVerified,
    DateTime? createdAt,
  }) {
    return AuthUser(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      isEmailVerified: isEmailVerified ?? this.isEmailVerified,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName:
          json['full_name'] as String? ??
          json['display_name'] as String? ??
          json['name'] as String? ??
          json['fullName'] as String? ??
          '',
      avatarUrl: json['avatar_url'] as String? ?? json['avatarUrl'] as String?,
      isEmailVerified:
          json['is_email_verified'] as bool? ??
          json['isEmailVerified'] as bool? ??
          false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'avatar_url': avatarUrl,
      'is_email_verified': isEmailVerified,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class AuthToken {
  final String accessToken;
  final String refreshToken;
  final DateTime expiresAt;

  const AuthToken({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresAt,
  });

  bool get isExpired => DateTime.now().isAfter(expiresAt);

  factory AuthToken.fromJson(Map<String, dynamic> json) {
    return AuthToken(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String? ?? '',
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'] as String)
          : DateTime.now().add(const Duration(hours: 24)),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'expires_at': expiresAt.toIso8601String(),
    };
  }
}

class AuthSession {
  final AuthUser user;
  final AuthToken token;
  final bool rememberMe;

  const AuthSession({
    required this.user,
    required this.token,
    this.rememberMe = true,
  });
}

class AuthException implements Exception {
  final String message;
  final String? code;

  const AuthException(this.message, {this.code});

  @override
  String toString() => message;
}
