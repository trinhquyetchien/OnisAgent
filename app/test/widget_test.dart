// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'package:app/main.dart';

void main() {
  setUpAll(() async {
    await initializeDateFormatting('vi', null);
  });

  testWidgets('App smoke test loads successfully', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const OnisApp());
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pumpAndSettle();

    // Verify that the OnisAgent title is present.
    expect(find.textContaining('Onis'), findsWidgets);
  });
}
