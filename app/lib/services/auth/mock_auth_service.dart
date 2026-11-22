import 'dart:math';
import '../../models/auth_user.dart';
import 'auth_service_interface.dart';

class MockUserAccount {
  AuthUser user;
  String password;

  MockUserAccount({
    required this.user,
    required this.password,
  });
}

class MockAuthService implements IAuthService {
  static final MockAuthService _instance = MockAuthService._internal();
  factory MockAuthService() => _instance;

  MockAuthService._internal() {
    _initializeMockAccounts();
  }

  final Map<String, MockUserAccount> _accounts = {};
  final Map<String, String> _activeOtps = {}; // key: "email:purpose", value: "123456"
  AuthSession? _currentSession;

  void _initializeMockAccounts() {
    // Tài khoản đã xác thực mặc định
    final demoUser = AuthUser(
      id: 'usr_demo_01',
      email: 'demo@onis.ai',
      fullName: 'Nguyễn Văn An',
      avatarUrl: null,
      isEmailVerified: true,
      createdAt: DateTime.now().subtract(const Duration(days: 30)),
    );
    _accounts[demoUser.email.toLowerCase()] = MockUserAccount(
      user: demoUser,
      password: 'password123',
    );

    // Tài khoản nhân sự AI
    final alexUser = AuthUser(
      id: 'usr_demo_02',
      email: 'alex@onis.ai',
      fullName: 'Alex Đỗ',
      avatarUrl: null,
      isEmailVerified: true,
      createdAt: DateTime.now().subtract(const Duration(days: 15)),
    );
    _accounts[alexUser.email.toLowerCase()] = MockUserAccount(
      user: alexUser,
      password: 'password123',
    );

    // Tài khoản chưa xác thực email để test luồng OTP verification
    final unverifiedUser = AuthUser(
      id: 'usr_demo_03',
      email: 'unverified@onis.ai',
      fullName: 'Trần Minh Khang',
      avatarUrl: null,
      isEmailVerified: false,
      createdAt: DateTime.now().subtract(const Duration(hours: 2)),
    );
    _accounts[unverifiedUser.email.toLowerCase()] = MockUserAccount(
      user: unverifiedUser,
      password: 'password123',
    );
  }

  @override
  Future<AuthSession?> getCurrentSession() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return _currentSession;
  }

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    await Future.delayed(const Duration(milliseconds: 650));
    final cleanEmail = email.trim().toLowerCase();

    final account = _accounts[cleanEmail];
    if (account == null) {
      throw const AuthException(
        'Tài khoản không tồn tại. Vui lòng kiểm tra lại email hoặc đăng ký mới.',
        code: 'USER_NOT_FOUND',
      );
    }

    if (account.password != password) {
      throw const AuthException(
        'Mật khẩu không chính xác. Vui lòng thử lại hoặc chọn Quên mật khẩu.',
        code: 'INVALID_CREDENTIALS',
      );
    }

    final token = AuthToken(
      accessToken: 'mock_jwt_access_${DateTime.now().millisecondsSinceEpoch}',
      refreshToken: 'mock_jwt_refresh_${DateTime.now().millisecondsSinceEpoch}',
      expiresAt: DateTime.now().add(const Duration(days: 7)),
    );

    final session = AuthSession(
      user: account.user,
      token: token,
      rememberMe: rememberMe,
    );

    _currentSession = session;
    return session;
  }

  @override
  Future<AuthSession> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    await Future.delayed(const Duration(milliseconds: 700));
    final cleanEmail = email.trim().toLowerCase();

    if (_accounts.containsKey(cleanEmail)) {
      throw const AuthException(
        'Email này đã được đăng ký trong hệ thống. Vui lòng đăng nhập.',
        code: 'EMAIL_ALREADY_EXISTS',
      );
    }

    final newUser = AuthUser(
      id: 'usr_${DateTime.now().millisecondsSinceEpoch}',
      email: cleanEmail,
      fullName: fullName.trim(),
      isEmailVerified: false, // Mặc định yêu cầu OTP xác thực email
      createdAt: DateTime.now(),
    );

    _accounts[cleanEmail] = MockUserAccount(
      user: newUser,
      password: password,
    );

    // Tạo mã OTP xác thực
    _activeOtps['$cleanEmail:${OtpPurpose.emailVerification.name}'] = '123456';

    final token = AuthToken(
      accessToken: 'mock_jwt_access_${DateTime.now().millisecondsSinceEpoch}',
      refreshToken: 'mock_jwt_refresh_${DateTime.now().millisecondsSinceEpoch}',
      expiresAt: DateTime.now().add(const Duration(days: 7)),
    );

    final session = AuthSession(
      user: newUser,
      token: token,
      rememberMe: true,
    );

    _currentSession = session;
    return session;
  }

  @override
  Future<AuthSession> loginWithSocial({required String provider}) async {
    await Future.delayed(const Duration(milliseconds: 600));
    final email = 'user.${provider.toLowerCase()}@onis.ai';

    var account = _accounts[email];
    if (account == null) {
      final newUser = AuthUser(
        id: 'usr_social_${DateTime.now().millisecondsSinceEpoch}',
        email: email,
        fullName: provider == 'Google' ? 'Google User' : 'Apple User',
        isEmailVerified: true,
        createdAt: DateTime.now(),
      );
      account = MockUserAccount(user: newUser, password: 'social_login');
      _accounts[email] = account;
    }

    final session = AuthSession(
      user: account.user,
      token: AuthToken(
        accessToken: 'mock_jwt_social_${DateTime.now().millisecondsSinceEpoch}',
        refreshToken: 'mock_jwt_social_refresh',
        expiresAt: DateTime.now().add(const Duration(days: 14)),
      ),
      rememberMe: true,
    );

    _currentSession = session;
    return session;
  }

  @override
  Future<bool> verifyOtp({
    required String email,
    required String otp,
    required OtpPurpose purpose,
  }) async {
    await Future.delayed(const Duration(milliseconds: 600));
    final cleanEmail = email.trim().toLowerCase();
    final otpKey = '$cleanEmail:${purpose.name}';
    final savedOtp = _activeOtps[otpKey] ?? '123456'; // '123456' luôn là mã mock hợp lệ

    if (otp != savedOtp && otp != '123456') {
      throw const AuthException(
        'Mã OTP không chính xác. Vui lòng kiểm tra lại (Mã mẫu test: 123456).',
        code: 'INVALID_OTP',
      );
    }

    // OTP hợp lệ -> thực hiện tác vụ tương ứng
    if (purpose == OtpPurpose.emailVerification) {
      final account = _accounts[cleanEmail];
      if (account != null) {
        account.user = account.user.copyWith(isEmailVerified: true);
        if (_currentSession?.user.email.toLowerCase() == cleanEmail) {
          _currentSession = AuthSession(
            user: account.user,
            token: _currentSession!.token,
            rememberMe: _currentSession!.rememberMe,
          );
        }
      }
    }

    _activeOtps.remove(otpKey);
    return true;
  }

  @override
  Future<bool> resendOtp({
    required String email,
    required OtpPurpose purpose,
  }) async {
    await Future.delayed(const Duration(milliseconds: 500));
    final cleanEmail = email.trim().toLowerCase();
    // Sinh ngẫu nhiên mã 6 số (hoặc giữ 123456)
    final randomCode = (100000 + Random().nextInt(900000)).toString();
    _activeOtps['$cleanEmail:${purpose.name}'] = randomCode;
    return true;
  }

  @override
  Future<bool> sendForgotPasswordOtp({required String email}) async {
    await Future.delayed(const Duration(milliseconds: 600));
    final cleanEmail = email.trim().toLowerCase();

    if (!_accounts.containsKey(cleanEmail)) {
      throw const AuthException(
        'Email này chưa được đăng ký trong hệ thống OnisAgent.',
        code: 'EMAIL_NOT_FOUND',
      );
    }

    _activeOtps['$cleanEmail:${OtpPurpose.passwordReset.name}'] = '123456';
    return true;
  }

  @override
  Future<bool> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    await Future.delayed(const Duration(milliseconds: 650));
    final cleanEmail = email.trim().toLowerCase();

    final otpKey = '$cleanEmail:${OtpPurpose.passwordReset.name}';
    final savedOtp = _activeOtps[otpKey] ?? '123456';

    if (otp != savedOtp && otp != '123456') {
      throw const AuthException(
        'Mã xác thực không hợp lệ hoặc đã hết hạn.',
        code: 'INVALID_RESET_OTP',
      );
    }

    final account = _accounts[cleanEmail];
    if (account == null) {
      throw const AuthException(
        'Tài khoản không tồn tại.',
        code: 'USER_NOT_FOUND',
      );
    }

    account.password = newPassword;
    _activeOtps.remove(otpKey);
    return true;
  }

  @override
  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    await Future.delayed(const Duration(milliseconds: 600));
    if (_currentSession == null) {
      throw const AuthException('Bạn chưa đăng nhập.');
    }

    final cleanEmail = _currentSession!.user.email.toLowerCase();
    final account = _accounts[cleanEmail];
    if (account == null) {
      throw const AuthException('Tài khoản không tìm thấy.');
    }

    if (account.password != oldPassword) {
      throw const AuthException(
        'Mật khẩu hiện tại không chính xác.',
        code: 'WRONG_OLD_PASSWORD',
      );
    }

    if (oldPassword == newPassword) {
      throw const AuthException(
        'Mật khẩu mới không được trùng với mật khẩu hiện tại.',
        code: 'SAME_PASSWORD',
      );
    }

    account.password = newPassword;
    return true;
  }

  @override
  Future<void> logout() async {
    await Future.delayed(const Duration(milliseconds: 300));
    _currentSession = null;
  }
}
