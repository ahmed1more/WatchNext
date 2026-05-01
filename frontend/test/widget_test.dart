import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:watch_next_frontend/app.dart';

void main() {
  testWidgets('renders the home shell', (WidgetTester tester) async {
    await tester.pumpWidget(const WatchNextRoot());

    expect(find.byIcon(Icons.search), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
