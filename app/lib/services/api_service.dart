import 'dart:convert';
import 'package:http/http.dart' as http;

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
      path: json['path'] as String? ?? 'Fast Path',
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
      path: json['path'] as String? ?? 'Fast Path (~6ms)',
      intent: json['intent'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
      quickReplies: (json['quick_replies'] as List<dynamic>?)
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
  final String baseUrl;
  final String sessionId;

  ApiService({
    this.baseUrl = defaultBaseUrl,
    String? sessionId,
  }) : sessionId = sessionId ?? 'session_${DateTime.now().millisecondsSinceEpoch}';

  /// Classify intent via Kev Decision Model
  Future<IntentClassifyResult> classifyIntent(String text) async {
    final uri = Uri.parse('$baseUrl/api/v1/intent/classify');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'text': text}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return IntentClassifyResult.fromJson(data);
    } else {
      throw Exception('Failed to classify intent: HTTP ${response.statusCode}');
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
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'text': text,
        'session_id': sessionId,
        'user_id': 'default_user',
        if (slots != null) 'slots': slots,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return ChatApiResponse.fromJson(data);
    } else {
      throw Exception('Failed to send chat: HTTP ${response.statusCode}');
    }
  }
}
