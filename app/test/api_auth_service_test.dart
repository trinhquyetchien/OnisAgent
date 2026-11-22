import 'dart:convert';

import 'package:app/models/auth_user.dart';
import 'package:app/services/auth/api_auth_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _MemorySecureStorage extends FlutterSecureStorage {
  final Map<String, String> values = {};

  @override
  Future<String?> read({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async => values[key];

  @override
  Future<void> write({
    required String key,
    required String? value,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (value == null) {
      values.remove(key);
    } else {
      values[key] = value;
    }
  }

  @override
  Future<void> delete({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    values.remove(key);
  }
}

void main() {
  test('Google sign-in reports unsupported Windows desktop', () async {
    debugDefaultTargetPlatformOverride = TargetPlatform.windows;
    addTearDown(() => debugDefaultTargetPlatformOverride = null);

    final service = ApiAuthService(storage: _MemorySecureStorage());

    await expectLater(
      service.loginWithSocial(provider: 'Google'),
      throwsA(
        isA<AuthException>().having(
          (error) => error.message,
          'message',
          contains('Windows/Linux'),
        ),
      ),
    );
  });

  test('register accepts 201 and persists refresh token', () async {
    late http.Request capturedRequest;
    final storage = _MemorySecureStorage();
    final service = ApiAuthService(
      baseUrl: 'https://api.example.test/',
      storage: storage,
      client: MockClient((request) async {
        capturedRequest = request;
        return http.Response(
          jsonEncode({
            'user': {
              'id': 'user-1',
              'email': 'new@example.test',
              'display_name': 'New User',
              'is_verified': false,
              'created_at': '2026-01-01T00:00:00Z',
            },
            'access_token': 'access-1',
            'refresh_token': 'refresh-1',
            'expires_in': 600,
          }),
          201,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    final session = await service.register(
      fullName: 'New User',
      email: 'new@example.test',
      password: 'StrongPass123!',
    );

    expect(capturedRequest.url.path, '/api/v1/auth/register');
    expect(jsonDecode(capturedRequest.body)['display_name'], 'New User');
    expect(session.user.fullName, 'New User');
    expect(session.token.expiresAt.difference(DateTime.now()).inMinutes, 9);
    expect(storage.values['onis_refresh_token'], 'refresh-1');
  });

  test('email verification and reset send matching email with OTP', () async {
    final requests = <http.Request>[];
    final service = ApiAuthService(
      baseUrl: 'https://api.example.test',
      storage: _MemorySecureStorage(),
      client: MockClient((request) async {
        requests.add(request);
        return http.Response('{"ok":true}', 200);
      }),
    );

    await service.verifyOtp(
      email: 'user@example.test',
      otp: '012345',
      purpose: OtpPurpose.emailVerification,
    );
    await service.resetPassword(
      email: 'user@example.test',
      otp: '012345',
      newPassword: 'NewStrong123!',
    );

    expect(requests[0].url.path, '/api/v1/auth/verify-email');
    expect(jsonDecode(requests[0].body), {
      'email': 'user@example.test',
      'token': '012345',
    });
    expect(requests[1].url.path, '/api/v1/auth/reset-password');
    expect(jsonDecode(requests[1].body), {
      'email': 'user@example.test',
      'token': '012345',
      'new_password': 'NewStrong123!',
    });
  });

  test('login without remember-me does not persist refresh token', () async {
    final storage = _MemorySecureStorage();
    storage.values['onis_refresh_token'] = 'old-refresh';
    final service = ApiAuthService(
      storage: storage,
      client: MockClient(
        (_) async => http.Response(
          jsonEncode({
            'user': {
              'id': 'user-1',
              'email': 'user@example.test',
              'full_name': 'User',
              'is_email_verified': true,
            },
            'access_token': 'access-1',
            'refresh_token': 'refresh-1',
            'expires_in': 900,
          }),
          200,
          headers: {'content-type': 'application/json'},
        ),
      ),
    );

    final session = await service.login(
      email: 'user@example.test',
      password: 'StrongPass123!',
      rememberMe: false,
    );

    expect(session.rememberMe, isFalse);
    expect(storage.values, isEmpty);
  });
}
