import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nyayalens_client/main.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';

void main() {
  testWidgets('App builds smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(_SmokeApiClient()),
        ],
        child: const NyayaLensApp(),
      ),
    );
    await tester.pump();

    expect(find.byType(NyayaLensApp), findsOneWidget);
    expect(find.text('Audit command center'), findsOneWidget);
  });
}

class _SmokeApiClient extends ApiClient {
  _SmokeApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<List<Object?>> listAudits() async => const [];
}
