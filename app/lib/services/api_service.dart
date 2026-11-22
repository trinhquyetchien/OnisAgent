import 'dart:convert';
import 'package:http/http.dart' as http;

class AuthSession {
  final String token;
  final String userId;
  final String email;
  final String name;

  const AuthSession({
    required this.token,
    required this.userId,
    required this.email,
    required this.name,
  });

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    final user = (json['user'] as Map<String, dynamic>?) ?? {};
    return AuthSession(
      token: json['access_token'] as String? ?? '',
      userId: user['id'] as String? ?? '',
      email: user['email'] as String? ?? '',
      name: user['name'] as String? ?? '',
    );
  }
}

class IntentClassifyResult {
  final String intent;
  final double confidence;
  final String path;
  final double latencyMs;

  IntentClassifyResult({
    required this.intent,
    required this.confidence,
    required this.path,
    required this.latencyMs,
  });

  factory IntentClassifyResult.fromJson(Map<String, dynamic> json) {
    return IntentClassifyResult(
      intent: json['intent'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      path: json['route'] as String? ?? json['path'] as String? ?? 'FAST_PATH',
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ChatApiResponse {
  final String reply;
  final String status;
  final String path;
  final String intent;
  final double confidence;
  final double latencyMs;
  final List<String> quickReplies;
  final Map<String, dynamic> slots;
  final bool requiresHitl;

  ChatApiResponse({
    required this.reply,
    required this.status,
    required this.path,
    required this.intent,
    required this.confidence,
    required this.latencyMs,
    required this.quickReplies,
    required this.slots,
    required this.requiresHitl,
  });

  factory ChatApiResponse.fromJson(Map<String, dynamic> json) {
    return ChatApiResponse(
      reply: json['reply'] as String? ?? '',
      status: json['status'] as String? ?? 'READY',
      path: json['route'] as String? ?? json['path'] as String? ?? 'FAST_PATH',
      intent: json['intent'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
      quickReplies:
          (json['quick_replies'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      slots: (json['slots'] as Map<String, dynamic>?) ?? {},
      requiresHitl: json['requires_hitl'] as bool? ?? false,
    );
  }
}

class ApiService {
  static const String defaultBaseUrl = 'http://127.0.0.1:8000';
  static const String configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: defaultBaseUrl,
  );
  final String baseUrl;
  final String sessionId;
  String? token;
  static String? authToken;

  ApiService({this.baseUrl = configuredBaseUrl, this.token, String? sessionId})
    : sessionId =
          sessionId ?? 'session_${DateTime.now().millisecondsSinceEpoch}';

  /// Classify intent via Kev Decision Model
  Future<IntentClassifyResult> classifyIntent(String text) async {
    final uri = Uri.parse('$baseUrl/api/v1/intent/classify');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({'text': text}),
    );

    if (response.statusCode == 200) {
      final data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return IntentClassifyResult.fromJson(data);
    } else {
      throw _apiError('classify intent', response);
    }
  }

  /// Chat endpoint with Fast-Path / Clarification multi-turn flow
  Future<ChatApiResponse> sendMessage({
    required String text,
    Map<String, dynamic>? slots,
  }) async {
    final uri = Uri.parse('$baseUrl/api/v1/chat');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'text': text,
        'session_id': sessionId,
        'user_id': 'default_user',
        ...?(slots == null ? null : {'slots': slots}),
      }),
    );

    if (response.statusCode == 200) {
      final data =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return ChatApiResponse.fromJson(data);
    } else {
      throw _apiError('send chat', response);
    }
  }

  Future<AuthSession> register({
    required String name,
    required String email,
    required String password,
  }) async {
    return _authRequest('/api/v1/auth/register', {
      'name': name,
      'email': email,
      'password': password,
    });
  }

  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    return _authRequest('/api/v1/auth/login', {
      'email': email,
      'password': password,
    });
  }

  Future<AuthSession> me() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/v1/auth/me'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('load current user', response);
    }
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return AuthSession(
      token: token ?? '',
      userId: data['user']['id'],
      email: data['user']['email'],
      name: data['user']['name'],
    );
  }

  Future<void> logout() async {
    if (token == null) return;
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/logout'),
      headers: _headers,
    );
    if (response.statusCode != 200 && response.statusCode != 401) {
      throw _apiError('logout', response);
    }
    token = null;
  }

  Future<List<dynamic>> listTransactions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/v1/transactions'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('load transactions', response);
    }
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return data['transactions'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> createTransaction({
    required double amount,
    required String type,
    required String description,
    required String category,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/transactions'),
      headers: _headers,
      body: jsonEncode({
        'amount': amount,
        'type': type,
        'description': description,
        'category': category,
      }),
    );
    if (response.statusCode != 201) {
      throw _apiError('create transaction', response);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<List<dynamic>> listTasks({String status = 'all'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/v1/tasks?status_filter=$status'),
      headers: _headers,
    );
    if (response.statusCode != 200) throw _apiError('load tasks', response);
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return data['tasks'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> createTask({
    required String title,
    String? description,
    String? deadline,
    String priority = 'medium',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/tasks'),
      headers: _headers,
      body: jsonEncode({
        'title': title,
        'description': description,
        'deadline': deadline,
        'priority': priority,
      }),
    );
    if (response.statusCode != 201) throw _apiError('create task', response);
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> approveHitl({
    required String idempotencyKey,
    required String action,
    required Map<String, dynamic> payload,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/hitl/approve'),
      headers: _headers,
      body: jsonEncode({
        'idempotency_key': idempotencyKey,
        'action': action,
        'payload': payload,
      }),
    );
    if (response.statusCode != 200) {
      throw _apiError('approve HITL action', response);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if ((token ?? authToken)?.isNotEmpty ?? false)
      'Authorization': 'Bearer ${token ?? authToken}',
  };

  Future<AuthSession> _authRequest(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    if (response.statusCode != 200) throw _apiError('authenticate', response);
    final session = AuthSession.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
    token = session.token;
    return session;
  }

  Exception _apiError(String operation, http.Response response) {
    final detail = response.body.isEmpty ? '' : ' — ${response.body}';
    return Exception(
      'Failed to $operation: HTTP ${response.statusCode}$detail',
    );
  }
}
