import 'dart:convert';

import 'package:app/models/models.dart';
import 'package:app/services/api_service.dart';
import 'package:app/services/app_data_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  setUp(() {
    ApiService.authToken = null;
  });

  test('loads backend data and persists task actions through API', () async {
    final requests = <http.Request>[];
    final service = AppDataService.forTesting(
      ApiService(
        baseUrl: 'https://api.example.test',
        client: MockClient((request) async {
          requests.add(request);
          if (request.method == 'GET' &&
              request.url.path == '/api/v1/transactions') {
            return _jsonResponse({'transactions': []}, 200);
          }
          if (request.method == 'GET' && request.url.path == '/api/v1/tasks') {
            return _jsonResponse({'tasks': []}, 200);
          }
          if (request.method == 'GET' &&
              request.url.path == '/api/v1/savings-goals') {
            return _jsonResponse({'savings_goals': []}, 200);
          }
          if (request.method == 'GET' && request.url.path == '/api/v1/debts') {
            return _jsonResponse({'debts': []}, 200);
          }
          if (request.method == 'POST' && request.url.path == '/api/v1/tasks') {
            return _jsonResponse({
              'task': {
                'id': 'task-server-1',
                'title': 'Server task',
                'status': 'pending',
                'priority': 'high',
              },
            }, 201);
          }
          if (request.method == 'DELETE' &&
              request.url.path == '/api/v1/tasks/task-server-1') {
            return _jsonResponse({
              'ok': false,
              'status': 'BLOCKED',
              'requires_hitl': true,
            }, 200);
          }
          if (request.method == 'POST' &&
              request.url.path == '/api/v1/hitl/approve') {
            return _jsonResponse({'ok': true}, 200);
          }
          return _jsonResponse({'detail': 'Unexpected request'}, 404);
        }),
      ),
    );

    await service.refresh();
    expect(service.errorMessage, isNull);
    expect(service.tasks, isEmpty);

    await service.addTask(TaskItem(id: 'temporary-id', title: 'Server task'));
    expect(service.tasks.single.id, 'task-server-1');

    await service.deleteTask('task-server-1');
    final proposal = service.messages.single.hitlProposal!;
    expect(proposal.actionType, 'task_delete');
    expect(proposal.payload['task_id'], 'task-server-1');
    expect(service.tasks, hasLength(1));

    await service.approveHitlProposal(proposal.id);
    expect(service.tasks, isEmpty);
    expect(proposal.status, HitlStatus.approved);
    expect(
      requests.any(
        (request) =>
            request.url.path == '/api/v1/hitl/approve' &&
            jsonDecode(request.body)['action'] == 'task_delete',
      ),
      isTrue,
    );
  });

  test('does not insert a transaction when backend creation fails', () async {
    final service = AppDataService.forTesting(
      ApiService(
        baseUrl: 'https://api.example.test',
        client: MockClient(
          (_) async => _jsonResponse({'detail': 'database unavailable'}, 503),
        ),
      ),
    );

    await service.addTransaction(
      TransactionItem(
        id: 'local-id',
        description: 'Coffee',
        amount: 35000,
        type: 'expense',
        category: 'Food',
        date: DateTime(2026),
      ),
    );

    expect(service.transactions, isEmpty);
    expect(service.errorMessage, contains('database unavailable'));
  });
}

http.Response _jsonResponse(Map<String, dynamic> body, int statusCode) =>
    http.Response(
      jsonEncode(body),
      statusCode,
      headers: {'content-type': 'application/json'},
    );
