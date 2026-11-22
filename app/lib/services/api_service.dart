import 'dart:convert';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

String resolveDefaultBaseUrl() {
  const envUrl = String.fromEnvironment('API_BASE_URL');
  if (envUrl.isNotEmpty) return envUrl;
  if (!kIsWeb) {
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000';
      }
    } catch (_) {}
  }
  return 'http://127.0.0.1:8000';
}

class ApiAuthSession {
  final String token;
  final String userId;
  final String email;
  final String name;

  const ApiAuthSession({
    required this.token,
    required this.userId,
    required this.email,
    required this.name,
  });

  factory ApiAuthSession.fromJson(Map<String, dynamic> json) {
    final user = (json['user'] as Map<String, dynamic>?) ?? {};
    return ApiAuthSession(
      token: json['access_token'] as String? ?? '',
      userId: user['id']?.toString() ?? '',
      email: user['email']?.toString() ?? '',
      name: (user['name'] ?? user['full_name'] ?? user['display_name'] ?? '')
          .toString(),
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
  final Map<String, dynamic> data;
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
    required this.data,
    required this.requiresHitl,
  });

  factory ChatApiResponse.fromJson(Map<String, dynamic> json) {
    return ChatApiResponse(
      reply: json['reply'] as String? ?? json['message'] as String? ?? '',
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
      data: (json['data'] as Map<String, dynamic>?) ?? {},
      requiresHitl: json['requires_hitl'] as bool? ?? false,
    );
  }
}

class ApiService {
  static final String defaultBaseUrl = resolveDefaultBaseUrl();
  final String baseUrl;
  final String sessionId;
  final http.Client _client;
  String? token;
  static String? authToken;

  ApiService({
    String? baseUrl,
    this.token,
    String? sessionId,
    http.Client? client,
  }) : baseUrl = baseUrl ?? defaultBaseUrl,
       _client = client ?? http.Client(),
       sessionId =
           sessionId ?? 'session_${DateTime.now().millisecondsSinceEpoch}';

  /// Check backend health status
  Future<Map<String, dynamic>> checkHealth() async {
    final response = await _client
        .get(_uri('/api/v1/health'))
        .timeout(const Duration(seconds: 4));
    if (response.statusCode != 200) {
      throw _apiError('check backend health', response);
    }
    return _decodeObject(response);
  }

  /// Classify intent via Kev Decision Model
  Future<IntentClassifyResult> classifyIntent(String text) async {
    final response = await _client.post(
      _uri('/api/v1/intent/classify'),
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
    bool userConfirmed = false,
    String? idempotencyKey,
    String? userId,
  }) async {
    final response = await _client.post(
      _uri('/api/v1/chat'),
      headers: _headers,
      body: jsonEncode({
        'text': text,
        'session_id': sessionId,
        'user_id': userId ?? 'default_user',
        'user_confirmed': userConfirmed,
        'idempotency_key': ?idempotencyKey,
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

  Future<ApiAuthSession> register({
    required String name,
    required String email,
    required String password,
  }) async {
    return _authRequest('/api/v1/auth/register', {
      'display_name': name,
      'email': email,
      'password': password,
    });
  }

  Future<ApiAuthSession> login({
    required String email,
    required String password,
  }) async {
    return _authRequest('/api/v1/auth/login', {
      'email': email,
      'password': password,
    });
  }

  Future<ApiAuthSession> me() async {
    final response = await _client.get(
      _uri('/api/v1/auth/me'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('load current user', response);
    }
    final data = _decodeObject(response);
    final user = data['user'] as Map<String, dynamic>;
    return ApiAuthSession(
      token: token ?? authToken ?? '',
      userId: user['id'].toString(),
      email: user['email'].toString(),
      name: (user['name'] ?? user['full_name'] ?? user['display_name'] ?? '')
          .toString(),
    );
  }

  Future<void> logout() async {
    if (token == null && authToken == null) return;
    try {
      final response = await _client.post(
        _uri('/api/v1/auth/logout'),
        headers: _headers,
      );
      if (response.statusCode != 200 && response.statusCode != 401) {
        throw _apiError('logout', response);
      }
    } finally {
      token = null;
      authToken = null;
    }
  }

  // ------------------ TRANSACTIONS CRUD ------------------

  Future<List<dynamic>> listTransactions({
    String? category,
    String? keyword,
  }) async {
    final queryParams = <String, String>{};
    if (category != null && category.isNotEmpty) {
      queryParams['category'] = category;
    }
    if (keyword != null && keyword.isNotEmpty) {
      queryParams['keyword'] = keyword;
    }

    final uri = _uri(
      '/api/v1/transactions',
    ).replace(queryParameters: queryParams.isEmpty ? null : queryParams);

    final response = await _client.get(uri, headers: _headers);
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
    String account = 'default_account',
  }) async {
    final response = await _client.post(
      _uri('/api/v1/transactions'),
      headers: _headers,
      body: jsonEncode({
        'amount': amount,
        'type': type,
        'description': description,
        'category': category,
        'account': account,
      }),
    );
    if (response.statusCode != 201) {
      throw _apiError('create transaction', response);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateTransaction({
    required String id,
    double? amount,
    String? type,
    String? description,
    String? category,
  }) async {
    final response = await _client.patch(
      _uri('/api/v1/transactions/$id'),
      headers: _headers,
      body: jsonEncode({
        'amount': ?amount,
        'type': ?type,
        'description': ?description,
        'category': ?category,
      }),
    );
    if (response.statusCode != 200) {
      throw _apiError('update transaction', response);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> deleteTransaction(String id) async {
    final response = await _client.delete(
      _uri('/api/v1/transactions/$id'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('delete transaction', response);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getTransaction(String id) async {
    final response = await _client.get(
      _uri('/api/v1/transactions/$id'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('load transaction', response);
    }
    return _decodeObject(response);
  }

  Future<Map<String, dynamic>> correctTransactionCategory({
    required String transactionId,
    required String rawDescription,
    required String predictedCategory,
    required String correctedCategory,
  }) async {
    final response = await _client.post(
      _uri('/api/v1/transactions/corrections'),
      headers: _headers,
      body: jsonEncode({
        'transaction_id': transactionId,
        'raw_description': rawDescription,
        'ai_predicted_category': predictedCategory,
        'user_corrected_category': correctedCategory,
      }),
    );
    if (response.statusCode != 201) {
      throw _apiError('correct transaction category', response);
    }
    return _decodeObject(response);
  }

  // ------------------ TASKS CRUD ------------------

  Future<List<dynamic>> listTasks({String status = 'all'}) async {
    final response = await _client.get(
      _uri('/api/v1/tasks').replace(queryParameters: {'status_filter': status}),
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
    String category = 'Chung',
    bool isImportant = false,
  }) async {
    final response = await _client.post(
      _uri('/api/v1/tasks'),
      headers: _headers,
      body: jsonEncode({
        'title': title,
        'description': description,
        'deadline': deadline,
        'priority': priority,
        'category': category,
        'is_important': isImportant,
      }),
    );
    if (response.statusCode != 201) throw _apiError('create task', response);
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateTask({
    required String id,
    String? status,
    String? title,
    String? description,
    String? deadline,
    String? priority,
    bool? isImportant,
  }) async {
    final response = await _client.patch(
      _uri('/api/v1/tasks/$id'),
      headers: _headers,
      body: jsonEncode({
        'status': ?status,
        'title': ?title,
        'description': ?description,
        'deadline': ?deadline,
        'priority': ?priority,
        'is_important': ?isImportant,
      }),
    );
    if (response.statusCode != 200) throw _apiError('update task', response);
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> deleteTask(String id) async {
    final response = await _client.delete(
      _uri('/api/v1/tasks/$id'),
      headers: _headers,
    );
    // Note: Backend returns 200 with {ok: false, status: 'BLOCKED', requires_hitl: true, task: ...}
    if (response.statusCode != 200) throw _apiError('delete task', response);
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  // ------------------ SAVINGS GOALS ------------------

  Future<List<dynamic>> listSavingsGoals() async {
    final response = await _client.get(
      _uri('/api/v1/savings-goals'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('load savings goals', response);
    }
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return data['savings_goals'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> createSavingsGoal({
    required String title,
    required double targetAmount,
    double currentAmount = 0.0,
    String? deadlineDate,
  }) async {
    final response = await _client.post(
      _uri('/api/v1/savings-goals'),
      headers: _headers,
      body: jsonEncode({
        'values': {
          'title': title,
          'target_amount': targetAmount,
          'current_amount': currentAmount,
          'deadline_date': deadlineDate,
        },
      }),
    );
    if (response.statusCode != 201) {
      throw _apiError('create savings goal', response);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  // ------------------ DEBTS ------------------

  Future<List<dynamic>> listDebts() async {
    final response = await _client.get(
      _uri('/api/v1/debts'),
      headers: _headers,
    );
    if (response.statusCode != 200) throw _apiError('load debts', response);
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return data['debts'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> createDebt({
    required String person,
    required double amount,
    required String debtType,
    String? note,
  }) async {
    final response = await _client.post(
      _uri('/api/v1/debts'),
      headers: _headers,
      body: jsonEncode({
        'values': {
          'person': person,
          'amount': amount,
          'debt_type': debtType,
          'note': note,
        },
      }),
    );
    if (response.statusCode != 201) throw _apiError('create debt', response);
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  // ------------------ HITL APPROVAL ------------------

  Future<Map<String, dynamic>> approveHitl({
    required String idempotencyKey,
    required String action,
    required Map<String, dynamic> payload,
  }) async {
    final response = await _client.post(
      _uri('/api/v1/hitl/approve'),
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

  Future<Map<String, dynamic>> logoutAll() async {
    final response = await _client.post(
      _uri('/api/v1/auth/logout-all'),
      headers: _headers,
    );
    if (response.statusCode != 200) {
      throw _apiError('log out all sessions', response);
    }
    return _decodeObject(response);
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if ((token ?? authToken)?.isNotEmpty ?? false)
      'Authorization': 'Bearer ${token ?? authToken}',
  };

  Future<ApiAuthSession> _authRequest(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _client.post(
      _uri(path),
      headers: _headers,
      body: jsonEncode(body),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw _apiError('authenticate', response);
    }
    final session = ApiAuthSession.fromJson(_decodeObject(response));
    token = session.token;
    authToken = session.token;
    return session;
  }

  Exception _apiError(String operation, http.Response response) {
    var message = response.body;
    if (response.body.isNotEmpty) {
      try {
        final payload = jsonDecode(utf8.decode(response.bodyBytes));
        if (payload is Map<String, dynamic>) {
          message = payload['detail']?.toString() ?? response.body;
        }
      } on FormatException {
        message = response.body;
      }
    }
    final detail = message.isEmpty ? '' : ' — $message';
    return Exception(
      'Failed to $operation: HTTP ${response.statusCode}$detail',
    );
  }

  Uri _uri(String path) {
    final normalizedBase = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    return Uri.parse('$normalizedBase$path');
  }

  Map<String, dynamic> _decodeObject(http.Response response) {
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Expected a JSON object from the API.');
    }
    return decoded;
  }

  void close() => _client.close();
}
