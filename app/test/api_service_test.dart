import 'dart:convert';

import 'package:app/services/api_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  setUp(() {
    ApiService.authToken = null;
  });

  test(
    'register accepts HTTP 201 and matches backend request contract',
    () async {
      late http.Request capturedRequest;
      final service = ApiService(
        baseUrl: 'https://api.example.test/',
        client: MockClient((request) async {
          capturedRequest = request;
          return http.Response(
            jsonEncode({
              'user': {
                'id': 'user-1',
                'email': 'new@example.test',
                'display_name': 'New User',
                'is_verified': false,
              },
              'access_token': 'access-1',
              'refresh_token': 'refresh-1',
              'expires_in': 900,
            }),
            201,
            headers: {'content-type': 'application/json'},
          );
        }),
      );

      final session = await service.register(
        name: 'New User',
        email: 'new@example.test',
        password: 'StrongPass123!',
      );

      expect(capturedRequest.url.path, '/api/v1/auth/register');
      expect(
        jsonDecode(capturedRequest.body),
        containsPair('display_name', 'New User'),
      );
      expect(session.token, 'access-1');
      expect(session.name, 'New User');
      expect(ApiService.authToken, 'access-1');
    },
  );

  test(
    'chat parses backend message field and sends authenticated user id',
    () async {
      late http.Request capturedRequest;
      final service = ApiService(
        baseUrl: 'https://api.example.test',
        sessionId: 'session-1',
        client: MockClient((request) async {
          capturedRequest = request;
          return http.Response(
            jsonEncode({
              'message': 'Đã lưu giao dịch',
              'status': 'READY',
              'route': 'FAST_PATH',
              'intent': 'finance.add_expense',
              'confidence': 0.9,
              'latency_ms': 4.2,
              'data': {
                'transaction': {'id': 'tx-1'},
              },
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }),
      );

      final response = await service.sendMessage(
        text: 'Chi cà phê 35k',
        userId: 'user-1',
      );

      expect(jsonDecode(capturedRequest.body)['user_id'], 'user-1');
      expect(response.reply, 'Đã lưu giao dịch');
      expect(response.data['transaction']['id'], 'tx-1');
    },
  );

  test('API errors use backend detail instead of raw JSON', () async {
    final service = ApiService(
      baseUrl: 'https://api.example.test',
      client: MockClient(
        (_) async => http.Response(
          jsonEncode({'detail': 'Email đã được đăng ký.'}),
          409,
          headers: {'content-type': 'application/json'},
        ),
      ),
    );

    await expectLater(
      service.login(email: 'taken@example.test', password: 'password'),
      throwsA(
        isA<Exception>().having(
          (error) => error.toString(),
          'message',
          contains('Email đã được đăng ký.'),
        ),
      ),
    );
  });
}
