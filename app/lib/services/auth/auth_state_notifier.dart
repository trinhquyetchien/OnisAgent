import 'package:flutter/material.dart';
import '../../models/auth_user.dart';
import 'auth_service_interface.dart';
import 'api_auth_service.dart';

enum AuthStatus { initial, authenticated, unverified, unauthenticated }

class AuthStateNotifier extends ChangeNotifier {
  static final AuthStateNotifier _instance = AuthStateNotifier._internal(
    authService: ApiAuthService(),
  );
  factory AuthStateNotifier() => _instance;

  IAuthService _authService;
  AuthStateNotifier._internal({required IAuthService authService})
    : _authService = authService;

  AuthStatus _status = AuthStatus.initial;
  AuthUser? _currentUser;
  String? _pendingVerificationEmail;
  bool _isLoading = false;
  String? _errorMessage;

  AuthStatus get status => _status;
  AuthUser? get currentUser => _currentUser;
  String? get pendingVerificationEmail => _pendingVerificationEmail;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated =>
      _status == AuthStatus.authenticated && _currentUser != null;

  /// Cho phép hoán đổi giữa MockAuthService và ApiAuthService
  void setAuthService(IAuthService service) {
    _authService = service;
    notifyListeners();
  }

  void clearError() {
    if (_errorMessage != null) {
      _errorMessage = null;
      notifyListeners();
    }
  }

  /// Kiểm tra trạng thái phiên khởi đầu của app
  Future<void> checkAuth() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final session = await _authService.getCurrentSession();
      if (session != null) {
        _currentUser = session.user;
        if (session.user.isEmailVerified) {
          _status = AuthStatus.authenticated;
        } else {
          _pendingVerificationEmail = session.user.email;
          _status = AuthStatus.unverified;
        }
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (e) {
      _status = AuthStatus.unauthenticated;
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Đăng nhập
  Future<bool> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final session = await _authService.login(
        email: email,
        password: password,
        rememberMe: rememberMe,
      );
      _currentUser = session.user;

      if (session.user.isEmailVerified) {
        _status = AuthStatus.authenticated;
        _pendingVerificationEmail = null;
      } else {
        _status = AuthStatus.unverified;
        _pendingVerificationEmail = session.user.email;
      }
      return true;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Đã xảy ra lỗi không xác định. Vui lòng thử lại.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Đăng ký tài khoản
  Future<bool> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final session = await _authService.register(
        fullName: fullName,
        email: email,
        password: password,
      );
      _currentUser = session.user;
      _pendingVerificationEmail = session.user.email;
      _status = AuthStatus.unverified;
      return true;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Không thể đăng ký tài khoản. Vui lòng thử lại sau.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Đăng nhập mạng xã hội
  Future<bool> loginWithSocial(String provider) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final session = await _authService.loginWithSocial(provider: provider);
      _currentUser = session.user;
      _status = AuthStatus.authenticated;
      _pendingVerificationEmail = null;
      return true;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Đăng nhập mạng xã hội thất bại.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Xác thực OTP Email
  Future<bool> verifyEmailOtp(String otp) async {
    final email = _pendingVerificationEmail ?? _currentUser?.email;
    if (email == null) {
      _errorMessage = 'Không xác định được email cần kích hoạt.';
      notifyListeners();
      return false;
    }

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final success = await _authService.verifyOtp(
        email: email,
        otp: otp,
        purpose: OtpPurpose.emailVerification,
      );

      if (success) {
        if (_currentUser != null) {
          _currentUser = _currentUser!.copyWith(isEmailVerified: true);
        }
        _status = AuthStatus.authenticated;
        _pendingVerificationEmail = null;
        return true;
      }
      return false;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Xác thực OTP thất bại. Vui lòng thử lại.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Gửi lại OTP kích hoạt email
  Future<bool> resendEmailOtp() async {
    final email = _pendingVerificationEmail ?? _currentUser?.email;
    if (email == null) return false;

    try {
      return await _authService.resendOtp(
        email: email,
        purpose: OtpPurpose.emailVerification,
      );
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Gửi OTP quên mật khẩu
  Future<bool> sendForgotPasswordOtp(String email) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final success = await _authService.sendForgotPasswordOtp(email: email);
      return success;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Không thể gửi mã khôi phục. Vui lòng thử lại.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Đặt lại mật khẩu mới bằng OTP
  Future<bool> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final success = await _authService.resetPassword(
        email: email,
        otp: otp,
        newPassword: newPassword,
      );
      return success;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Đặt lại mật khẩu thất bại.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Đổi mật khẩu trong phiên
  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final success = await _authService.changePassword(
        oldPassword: oldPassword,
        newPassword: newPassword,
      );
      return success;
    } on AuthException catch (e) {
      _errorMessage = e.message;
      return false;
    } catch (e) {
      _errorMessage = 'Đổi mật khẩu thất bại.';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Đăng xuất
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authService.logout();
    } finally {
      _currentUser = null;
      _pendingVerificationEmail = null;
      _status = AuthStatus.unauthenticated;
      _errorMessage = null;
      _isLoading = false;
      notifyListeners();
    }
  }
}
