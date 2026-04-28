import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:nyayalens_client/features/audits/audit_pages.dart';
import 'package:nyayalens_client/features/dashboard/dashboard_page.dart';
import 'package:nyayalens_client/main.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/widgets/bias_heatmap.dart';

void main() {
  testWidgets('shell navigation opens the new audit page', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(_FakeApiClient()),
        ],
        child: const NyayaLensApp(),
      ),
    );
    await tester.pump();

    await tester.tap(find.widgetWithText(FilledButton, 'New audit').first);
    await tester.pumpAndSettle();

    expect(find.text('New fairness audit'), findsOneWidget);
    expect(find.text('Upload and detect schema'), findsOneWidget);
  });

  testWidgets('new audit upload action is gated before a file is selected', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(_FakeApiClient()),
        ],
        child: const MaterialApp(home: NewAuditPage()),
      ),
    );

    final upload = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Upload and detect schema'),
    );
    expect(upload.onPressed, isNull);
  });

  testWidgets('heatmap remains scrollable in a narrow viewport', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 320,
            child: BiasHeatmap(
              attributes: ['gender', 'caste', 'region'],
              metrics: ['spd', 'dir', 'eo', 'aod'],
              cells: [
                HeatmapCell(
                  attribute: 'gender',
                  metric: 'spd',
                  value: 0.18,
                  severity: 'warning',
                ),
                HeatmapCell(
                  attribute: 'caste',
                  metric: 'dir',
                  value: 0.62,
                  severity: 'critical',
                ),
              ],
            ),
          ),
        ),
      ),
    );

    expect(tester.takeException(), isNull);
    expect(find.byType(BiasHeatmap), findsOneWidget);
  });

  testWidgets('report page exposes an open PDF action after sign-off', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(_FakeApiClient()),
        ],
        child: const MaterialApp(
          home: AuditWorkspacePage(
            auditId: 'audit-1',
            tab: AuditWorkspaceTab.report,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(find.text('Audit report'), findsOneWidget);
    expect(find.text('Open PDF'), findsOneWidget);
  });

  testWidgets('dashboard renders a recoverable API error state', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(_FailingApiClient()),
        ],
        child: const MaterialApp(home: DashboardPage()),
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(find.text('Could not load audits'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
  });
}

class _FakeApiClient extends ApiClient {
  _FakeApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<List<dynamic>> listAudits() async {
    return [
      {
        'audit_id': 'audit-1',
        'title': 'Placement fairness audit',
        'status': 'signed_off',
        'mode': 'audit',
        'domain': 'hiring',
        'provenance_kind': 'synthetic',
        'provenance_label': 'placement_synthetic.csv',
      },
    ];
  }

  @override
  Future<Map<String, dynamic>> getAudit(String auditId) async {
    return _auditDetail;
  }
}

class _FailingApiClient extends ApiClient {
  _FailingApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<List<dynamic>> listAudits() async {
    throw ApiException('Backend unavailable', 503);
  }
}

final Map<String, dynamic> _auditDetail = {
  'summary': {
    'audit_id': 'audit-1',
    'title': 'Placement fairness audit',
    'status': 'signed_off',
    'mode': 'audit',
    'domain': 'hiring',
    'provenance_kind': 'synthetic',
    'provenance_label': 'placement_synthetic.csv',
  },
  'sensitive_attributes': ['gender', 'caste'],
  'outcome_column': 'selected',
  'metrics': [],
  'heatmap_cells': [
    {
      'attribute': 'gender',
      'metric': 'spd',
      'value': 0.12,
      'severity': 'warning',
      'note': 'Review disparity.',
    },
  ],
  'explanations': [],
  'conflicts': [],
  'proxies': [],
  'remediation': null,
  'sign_off': {
    'reviewer_name': 'Demo Reviewer',
    'reviewer_role': 'admin',
    'signed_at': '2026-04-28T10:00:00Z',
    'notes': 'Reviewed and approved.',
  },
  'has_report': true,
};
