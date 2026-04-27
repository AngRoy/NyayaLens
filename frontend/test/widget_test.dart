import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nyayalens_client/main.dart';

void main() {
  testWidgets('App builds smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: NyayaLensApp(),
      ),
    );

    // Just verify app loads
    expect(find.byType(NyayaLensApp), findsOneWidget);
  });
}
