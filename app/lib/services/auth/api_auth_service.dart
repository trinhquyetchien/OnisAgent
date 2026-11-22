import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../models/auth_user.dart';
import 'auth_service_interface.dart';

/// Triển khai thực tế IAuthService kết nối tới Backend API.
/// Khi Backend được đưa vào hoạt động, chỉ cần truyền [baseUrl] tương ứng.
class ApiAuthService implements IAuthService {
  final String baseUrl;
  final http.Client _client;
  final FlutterSecureStorage _storage;
  AuthSession? _cachedSession;
  String? _accessToken;
  String? _refreshToken;
  static const _refreshStorageKey = 'onis_refresh_token';

  ApiAuthService({
    this.baseUrl = 'http://127.0.0.1:8000',
    http.Client? client,
    FlutterSecureStorage? storage,
  }) : _client = client ?? http.Client(),
       _storage = storage ?? const FlutterSecureStorage();

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_cachedSession != null)
      'Authorization': 'Bearer ${_cachedSession!.token.accessToken}',
  };

  @override
  Future<AuthSession?> getCurrentSession() async {
    if (_cachedSession != null && !_cachedSession!.token.isExpired) {
      return _cachedSession;
    }
    final refreshToken = await _storage.read(key: _refreshStorageKey);
    if (refreshToken == null || refreshToken.isEmpty) {
      return null;
    }
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/api/v1/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      );
      if (response.statusCode != 200) {
        await _storage.delete(key: _refreshStorageKey);
        return null;
      }
      final data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final session = _sessionFromAuthResponse(data);
      await _storage.write(
        key: _refreshStorageKey,
        value: data['refresh_token'] as String,
      );
      _refreshToken = data['refresh_token'] as String;
      return session;
    } catch (_) {
      return null;
    }
  }

  AuthSession _sessionFromAuthResponse(Map<String, dynamic> data) {
    final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
    final accessToken = data['access_token'] as String;
    final refreshToken = data['refresh_token'] as String?;
    final token = AuthToken(
      accessToken: accessToken,
      refreshToken: refreshToken ?? '',
      expiresAt: DateTime.now().add(const Duration(minutes: 15)),
    );
    final session = AuthSession(user: user, token: token, rememberMe: true);
    _cachedSession = session;
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    return session;
  }

  Future<void> _persistRefreshToken(Map<String, dynamic> data) async {
    final refreshToken = data['refresh_token'] as String?;
    if (refreshToken == null) return;
    _refreshToken = refreshToken;
    await _storage.write(key: _refreshStorageKey, value: refreshToken);
  }

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'remember_me': rememberMe,
      }),
    );

    if (response.statusCode == 200) {
      final data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      await _persistRefreshToken(data);
      final session = _sessionFromAuthResponse(data);
      return AuthSession(
        user: session.user,
        token: session.token,
        rememberMe: rememberMe,
      );
    } else {
      final error =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>?;
      throw AuthException(
        error?['detail'] as String? ??
            'Đăng nhập thất bại. Mã lỗi: ${response.statusCode}',
      );
    }
  }

  @override
  Future<AuthSession> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': fullName,
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      await _persistRefreshToken(data);
      return _sessionFromAuthResponse(data);
    } else {
      final error =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>?;
      throw AuthException(
        error?['detail'] as String? ??
            'Đăng ký thất bại: ${response.statusCode}',
      );
    }
  }

  @override
  Future<AuthSession> loginWithSocial({required String provider}) async {
    if (provider.toLowerCase() != 'google') {
      throw const AuthException('Chỉ hỗ trợ đăng nhập Google.');
    }
    const webClientId = String.fromEnvironment(
      'GOOGLE_WEB_CLIENT_ID',
      defaultValue: '',
    );
    if (webClientId.isEmpty) {
      throw const AuthException(
        'Chưa cấu hình GOOGLE_WEB_CLIENT_ID cho Google Sign-In.',
      );
    }
    final googleSignIn = GoogleSignIn(serverClientId: webClientId);
    final googleUser = await googleSignIn.signIn();
    if (googleUser == null) {
      throw const AuthException('Người dùng đã hủy đăng nhập Google.');
    }
    final googleAuth = await googleUser.authentication;
    final idToken = googleAuth.idToken;
    if (idToken == null || idToken.isEmpty) {
      throw const AuthException('Không lấy được Google ID Token.');
    }

    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/google'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'id_token': idToken}),
    );
    if (response.statusCode != 200) {
      final error =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>?;
      throw AuthException(
        error?['detail'] as String? ?? 'Đăng nhập Google thất bại.',
      );
    }
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    await _persistRefreshToken(data);
    return _sessionFromAuthResponse(data);
  }

  @override
  Future<bool> verifyOtp({
    required String email,
    required String otp,
    required OtpPurpose purpose,
  }) async {
    if (purpose == OtpPurpose.passwordReset) {
      return true;
    }
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/verify-email'),
      headers: _headers,
      body: jsonEncode({'token': otp}),
    );
    return response.statusCode == 200;
  }

  @override
  Future<bool> resendOtp({
    required String email,
    required OtpPurpose purpose,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/forgot-password'),
      headers: _headers,
      body: jsonEncode({'email': email}),
    );
    return response.statusCode == 200;
  }

  @override
  Future<bool> sendForgotPasswordOtp({required String email}) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/forgot-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    return response.statusCode == 200;
  }

  @override
  Future<bool> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/reset-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'token': otp, 'new_password': newPassword}),
    );
    return response.statusCode == 200;
  }

  @override
  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/change-password'),
      headers: _headers,
      body: jsonEncode({
        'old_password': oldPassword,
        'new_password': newPassword,
      }),
    );
    return response.statusCode == 200;
  }

  @override
  Future<void> logout() async {
    final refreshToken =
        _refreshToken ?? await _storage.read(key: _refreshStorageKey);
    if (_accessToken != null && refreshToken != null) {
      await _client.post(
        Uri.parse('$baseUrl/api/v1/auth/logout'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_accessToken',
        },
        body: jsonEncode({'refresh_token': refreshToken}),
      );
    }
    await _storage.delete(key: _refreshStorageKey);
    _accessToken = null;
    _refreshToken = null;
    _cachedSession = null;
  }
}
