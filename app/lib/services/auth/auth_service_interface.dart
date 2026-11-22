import '../../models/auth_user.dart';

abstract class IAuthService {
  /// Lấy session người dùng hiện tại nếu có
  Future<AuthSession?> getCurrentSession();

  /// Đăng nhập bằng Email và Mật khẩu
  Future<AuthSession> login({
    required String email,
    required String password,
    bool rememberMe = true,
  });

  /// Đăng ký tài khoản mới
  Future<AuthSession> register({
    required String fullName,
    required String email,
    required String password,
  });

  /// Đăng nhập bằng mạng xã hội (Google, Apple)
  Future<AuthSession> loginWithSocial({required String provider});

  /// Xác thực mã OTP cho Email hoặc Quên mật khẩu
  Future<bool> verifyOtp({
    required String email,
    required String otp,
    required OtpPurpose purpose,
  });

  /// Gửi lại mã OTP
  Future<bool> resendOtp({
    required String email,
    required OtpPurpose purpose,
  });

  /// Yêu cầu gửi OTP quên mật khẩu
  Future<bool> sendForgotPasswordOtp({required String email});

  /// Đặt lại mật khẩu mới thông qua OTP
  Future<bool> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  });

  /// Đổi mật khẩu khi đã đăng nhập
  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  });

  /// Đăng xuất khỏi hệ thống
  Future<void> logout();
}
