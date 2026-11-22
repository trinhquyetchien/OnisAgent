import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart'
    show TargetPlatform, defaultTargetPlatform, kIsWeb;
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../models/auth_user.dart';
import '../api_service.dart';
import 'auth_service_interface.dart';

/// Triển khai thực tế IAuthService kết nối tới Backend API.
/// Khi Backend được đưa vào hoạt động, chỉ cần truyền [baseUrl] tương ứng.
class ApiAuthService implements IAuthService {
  static const _googleClientId = String.fromEnvironment(
    'GOOGLE_APP_CLIENT_ID',
    defaultValue: String.fromEnvironment('GOOGLE_WEB_CLIENT_ID'),
  );
  static final GoogleSignIn _googleSignIn = GoogleSignIn(
    clientId: kIsWeb ? _googleClientId : null,
    serverClientId: kIsWeb ? null : _googleClientId,
  );

  final String baseUrl;
  final http.Client _client;
  final FlutterSecureStorage _storage;
  AuthSession? _cachedSession;
  String? _accessToken;
  String? _refreshToken;
  static const _refreshStorageKey = 'onis_refresh_token';

  ApiAuthService({
    String? baseUrl,
    http.Client? client,
    FlutterSecureStorage? storage,
  }) : baseUrl = baseUrl ?? ApiService.defaultBaseUrl,
       _client = client ?? http.Client(),
       _storage = storage ?? const FlutterSecureStorage();

  static Stream<GoogleSignInAccount?> get googleSignInEvents =>
      _googleSignIn.onCurrentUserChanged;

  static Future<void> initializeWebGoogleSignIn() async {
    if (!kIsWeb) return;
    if (_googleClientId.isEmpty) {
      throw const AuthException(
        'Chưa cấu hình GOOGLE_APP_CLIENT_ID cho Google Sign-In.',
      );
    }
    await _googleSignIn.isSignedIn();
  }

  Map<String, String> get _headers {
    final accessToken = _accessToken ?? _cachedSession?.token.accessToken;
    return {
      'Content-Type': 'application/json',
      if (accessToken?.isNotEmpty ?? false)
        'Authorization': 'Bearer $accessToken',
    };
  }

  @override
  Future<AuthSession?> getCurrentSession() async {
    if (_cachedSession != null && !_cachedSession!.token.isExpired) {
      return _cachedSession;
    }
    final refreshToken = await _storage.read(key: _refreshStorageKey);
    if (refreshToken == null || refreshToken.isEmpty) {
      return null;
    }
    final response = await _request(
      () => _client.post(
        _uri('/api/v1/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      ),
    );
    if (response.statusCode == 401) {
      await _clearSession();
      return null;
    }
    if (response.statusCode != 200) {
      throw _responseError(response, 'Không thể khôi phục phiên đăng nhập.');
    }
    final data = _decodeObject(response);
    final session = _sessionFromAuthResponse(data);
    await _persistRefreshToken(data, rememberMe: true);
    return session;
  }

  AuthSession _sessionFromAuthResponse(
    Map<String, dynamic> data, {
    bool rememberMe = true,
  }) {
    final userData = data['user'];
    if (userData is! Map<String, dynamic>) {
      throw const AuthException('Dữ liệu tài khoản từ máy chủ không hợp lệ.');
    }
    final accessToken = data['access_token'];
    if (accessToken is! String || accessToken.isEmpty) {
      throw const AuthException('Máy chủ không trả access token hợp lệ.');
    }
    final user = AuthUser.fromJson(userData);
    final refreshToken = data['refresh_token'] as String?;
    final expiresIn =
        (data['expires_in'] as num?)?.toInt() ??
        const Duration(minutes: 15).inSeconds;
    final token = AuthToken(
      accessToken: accessToken,
      refreshToken: refreshToken ?? '',
      expiresAt: DateTime.now().add(Duration(seconds: expiresIn)),
    );
    final session = AuthSession(
      user: user,
      token: token,
      rememberMe: rememberMe,
    );
    _cachedSession = session;
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    ApiService.authToken = accessToken;
    return session;
  }

  Future<void> _persistRefreshToken(
    Map<String, dynamic> data, {
    bool rememberMe = true,
  }) async {
    final refreshToken = data['refresh_token'] as String?;
    _refreshToken = refreshToken;
    if (rememberMe && refreshToken != null && refreshToken.isNotEmpty) {
      await _storage.write(key: _refreshStorageKey, value: refreshToken);
    } else {
      await _storage.delete(key: _refreshStorageKey);
    }
  }

  Future<http.Response> _request(
    Future<http.Response> Function() request,
  ) async {
    try {
      return await request().timeout(const Duration(seconds: 15));
    } on http.ClientException catch (error) {
      throw AuthException('Không thể kết nối máy chủ: ${error.message}');
    } on TimeoutException {
      throw const AuthException('Kết nối máy chủ quá thời gian chờ.');
    }
  }

  Map<String, dynamic> _decodeObject(http.Response response) {
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const AuthException('Dữ liệu trả về từ máy chủ không hợp lệ.');
    }
    return decoded;
  }

  AuthException _responseError(http.Response response, String fallback) {
    var message = fallback;
    try {
      final payload = _decodeObject(response);
      message = payload['detail']?.toString() ?? fallback;
    } on FormatException {
      message = fallback;
    } on AuthException {
      message = fallback;
    }
    return AuthException(message, code: response.statusCode.toString());
  }

  Future<void> _clearSession() async {
    await _storage.delete(key: _refreshStorageKey);
    _accessToken = null;
    _refreshToken = null;
    _cachedSession = null;
    ApiService.authToken = null;
  }

  Uri _uri(String path) {
    final normalizedBase = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    return Uri.parse('$normalizedBase$path');
  }

  Future<Map<String, dynamic>> _postJson(
    String path,
    Map<String, dynamic> body, {
    bool authenticated = false,
  }) async {
    final response = await _request(
      () => _client.post(
        _uri(path),
        headers: authenticated
            ? _headers
            : {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      ),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw _responseError(response, 'Yêu cầu không thành công.');
    }
    return _decodeObject(response);
  }

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    final data = await _postJson('/api/v1/auth/login', {
      'email': email,
      'password': password,
      'remember_me': rememberMe,
    });
    await _persistRefreshToken(data, rememberMe: rememberMe);
    return _sessionFromAuthResponse(data, rememberMe: rememberMe);
  }

  @override
  Future<AuthSession> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    final data = await _postJson('/api/v1/auth/register', {
      'display_name': fullName,
      'email': email,
      'password': password,
    });
    await _persistRefreshToken(data);
    return _sessionFromAuthResponse(data);
  }

  @override
  Future<AuthSession> loginWithSocial({required String provider}) async {
    if (provider.toLowerCase() != 'google') {
      throw const AuthException('Chỉ hỗ trợ đăng nhập Google.');
    }
    if (!kIsWeb &&
        !const {
          TargetPlatform.android,
          TargetPlatform.iOS,
          TargetPlatform.macOS,
        }.contains(defaultTargetPlatform)) {
      throw const AuthException(
        'Google Sign-In không hỗ trợ trên Windows/Linux. Hãy chạy app trên '
        'Chrome hoặc Android/iOS/macOS.',
      );
    }
    if (_googleClientId.isEmpty) {
      throw const AuthException(
        'Chưa cấu hình GOOGLE_APP_CLIENT_ID cho Google Sign-In.',
      );
    }
    final googleUser = kIsWeb
        ? _googleSignIn.currentUser
        : await _googleSignIn.signIn();
    if (googleUser == null) {
      throw AuthException(
        kIsWeb
            ? 'Hoàn tất đăng nhập bằng nút Google trên màn hình trước.'
            : 'Người dùng đã hủy đăng nhập Google.',
      );
    }
    final googleAuth = await googleUser.authentication;
    final idToken = googleAuth.idToken;
    if (idToken == null || idToken.isEmpty) {
      throw const AuthException('Không lấy được Google ID Token.');
    }

    final data = await _postJson('/api/v1/auth/google', {'id_token': idToken});
    await _persistRefreshToken(data);
    return _sessionFromAuthResponse(data);
  }

  @override
  Future<bool> verifyOtp({
    required String email,
    required String otp,
    required OtpPurpose purpose,
  }) async {
    final path = purpose == OtpPurpose.emailVerification
        ? '/api/v1/auth/verify-email'
        : '/api/v1/auth/verify-reset-token';
    final data = await _postJson(path, {'email': email, 'token': otp});
    return data['ok'] == true;
  }

  @override
  Future<bool> resendOtp({
    required String email,
    required OtpPurpose purpose,
  }) async {
    final path = purpose == OtpPurpose.emailVerification
        ? '/api/v1/auth/resend-verification'
        : '/api/v1/auth/forgot-password';
    final data = await _postJson(path, {'email': email});
    return data['ok'] == true;
  }

  @override
  Future<bool> sendForgotPasswordOtp({required String email}) async {
    final data = await _postJson('/api/v1/auth/forgot-password', {
      'email': email,
    });
    return data['ok'] == true;
  }

  @override
  Future<bool> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    final data = await _postJson('/api/v1/auth/reset-password', {
      'email': email,
      'token': otp,
      'new_password': newPassword,
    });
    return data['ok'] == true;
  }

  @override
  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    final data = await _postJson('/api/v1/auth/change-password', {
      'old_password': oldPassword,
      'new_password': newPassword,
    }, authenticated: true);
    return data['ok'] == true;
  }

  @override
  Future<void> logout() async {
    try {
      final refreshToken =
          _refreshToken ?? await _storage.read(key: _refreshStorageKey);
      if (_accessToken != null && refreshToken != null) {
        final response = await _request(
          () => _client.post(
            _uri('/api/v1/auth/logout'),
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer $_accessToken',
            },
            body: jsonEncode({'refresh_token': refreshToken}),
          ),
        );
        if (response.statusCode != 200 && response.statusCode != 401) {
          throw _responseError(response, 'Không thể đăng xuất khỏi máy chủ.');
        }
      }
    } finally {
      await _clearSession();
    }
  }
}
