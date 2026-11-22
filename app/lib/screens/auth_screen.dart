import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class AuthScreen extends StatefulWidget {
  final ApiService api;
  final ValueChanged<AuthSession> onAuthenticated;

  const AuthScreen({super.key, required this.api, required this.onAuthenticated});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose(); _email.dispose(); _password.dispose(); super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });
    try {
      final session = _register
          ? await widget.api.register(name: _name.text.trim(), email: _email.text.trim(), password: _password.text)
          : await widget.api.login(email: _email.text.trim(), password: _password.text);
      if (mounted) widget.onAuthenticated(session);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 430),
            child: Card(
              elevation: 0,
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Form(
                  key: _formKey,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle),
                      child: const Icon(Icons.bolt_rounded, color: Colors.white, size: 32),
                    ),
                    const SizedBox(height: 18),
                    Text('Chào mừng đến OnisAgent', textAlign: TextAlign.center, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Text(_register ? 'Tạo tài khoản để đồng bộ dữ liệu cá nhân' : 'Đăng nhập để tiếp tục quản lý tài chính và công việc', textAlign: TextAlign.center),
                    const SizedBox(height: 24),
                    if (_register) ...[
                      TextFormField(controller: _name, decoration: const InputDecoration(labelText: 'Tên hiển thị', prefixIcon: Icon(Icons.person_outline)), validator: (v) => v == null || v.trim().isEmpty ? 'Nhập tên của bạn' : null),
                      const SizedBox(height: 12),
                    ],
                    TextFormField(controller: _email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)), validator: (v) => v == null || !v.contains('@') ? 'Email không hợp lệ' : null),
                    const SizedBox(height: 12),
                    TextFormField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'Mật khẩu', prefixIcon: Icon(Icons.lock_outline)), validator: (v) => v == null || v.length < 8 ? 'Mật khẩu tối thiểu 8 ký tự' : null),
                    if (_error != null) ...[const SizedBox(height: 12), Text(_error!, style: TextStyle(color: theme.colorScheme.error))],
                    const SizedBox(height: 20),
                    FilledButton(onPressed: _loading ? null : _submit, child: _loading ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2)) : Text(_register ? 'Tạo tài khoản' : 'Đăng nhập')),
                    TextButton(onPressed: _loading ? null : () => setState(() { _register = !_register; _error = null; }), child: Text(_register ? 'Đã có tài khoản? Đăng nhập' : 'Chưa có tài khoản? Đăng ký')),
                  ]),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
