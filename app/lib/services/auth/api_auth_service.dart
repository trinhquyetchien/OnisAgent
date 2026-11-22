import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../models/auth_user.dart';
import '../api_service.dart';
import 'auth_service_interface.dart';

/// Triển khai thực tế IAuthService kết nối tới Backend API.
/// Khi Backend được đưa vào hoạt động, chỉ cần truyền [baseUrl] tương ứng.
class ApiAuthService implements IAuthService {
  static const String defaultBaseUrl = 'http://127.0.0.1:8000';
  static const String configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: defaultBaseUrl,
  );
  final String baseUrl;
  final http.Client _client;
  AuthSession? _cachedSession;

  ApiAuthService({
    this.baseUrl = configuredBaseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

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
    final prefs = await SharedPreferences.getInstance();
    final storedToken = prefs.getString('onis_access_token');
    if (storedToken == null || storedToken.isEmpty) return null;
    final response = await _client.get(
      Uri.parse('$baseUrl/api/v1/auth/me'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $storedToken',
      },
    );
    if (response.statusCode != 200) {
      await prefs.remove('onis_access_token');
      return null;
    }
    final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
    _cachedSession = AuthSession(
      user: user,
      token: AuthToken(
        accessToken: storedToken,
        refreshToken: '',
        expiresAt: DateTime.now().add(const Duration(hours: 24)),
      ),
    );
    ApiService.authToken = storedToken;
    return _cachedSession;
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
      final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
      final token = _tokenFromResponse(data);
      final session = AuthSession(user: user, token: token, rememberMe: rememberMe);
      _cachedSession = session;
      await _persist(session);
      return session;
    } else {
      final error = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>?;
      throw AuthException(
        error?['detail'] as String? ?? 'Đăng nhập thất bại. Mã lỗi: ${response.statusCode}',
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
      final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
      final token = _tokenFromResponse(data);
      final session = AuthSession(user: user, token: token, rememberMe: true);
      _cachedSession = session;
      await _persist(session);
      return session;
    } else {
      final error = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>?;
      throw AuthException(
        error?['detail'] as String? ?? 'Đăng ký thất bại: ${response.statusCode}',
      );
    }
  }

  @override
  Future<AuthSession> loginWithSocial({required String provider}) async {
    throw UnimplementedError('Social login requires OAuth flow');
  }

  @override
  Future<bool> verifyOtp({
    required String email,
    required String otp,
    required OtpPurpose purpose,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/verify-otp'),
      headers: _headers,
      body: jsonEncode({
        'email': email,
        'otp': otp,
        'purpose': purpose.name,
      }),
    );
    return response.statusCode == 200;
  }

  @override
  Future<bool> resendOtp({
    required String email,
    required OtpPurpose purpose,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/auth/resend-otp'),
      headers: _headers,
      body: jsonEncode({'email': email, 'purpose': purpose.name}),
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
      body: jsonEncode({
        'email': email,
        'otp': otp,
        'new_password': newPassword,
      }),
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
    if (_cachedSession != null) {
      await _client.post(Uri.parse('$baseUrl/api/v1/auth/logout'), headers: _headers);
    }
    _cachedSession = null;
    ApiService.authToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('onis_access_token');
  }

  AuthToken _tokenFromResponse(Map<String, dynamic> data) {
    final nested = data['token'];
    if (nested is Map<String, dynamic>) return AuthToken.fromJson(nested);
    final accessToken = data['access_token'] as String?;
    if (accessToken == null || accessToken.isEmpty) {
      throw const AuthException('Backend không trả về access token.');
    }
    return AuthToken(
      accessToken: accessToken,
      refreshToken: '',
      expiresAt: DateTime.now().add(const Duration(hours: 24)),
    );
  }

  Future<void> _persist(AuthSession session) async {
    ApiService.authToken = session.token.accessToken;
    if (session.rememberMe) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('onis_access_token', session.token.accessToken);
    }
  }
}
