// RED reproducer for the tradeoff selection UI on the audit overview.
//
// When metric conflicts are detected and no tradeoff is yet recorded,
// the workspace must offer a "Resolve metric conflict" card with a
// metric chooser. After submission, the recorded tradeoff is rendered
// alongside who chose it.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:nyayalens_client/features/audits/audit_pages.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/models/audit_models.dart';

void main() {
  test('Tradeoff.fromJson parses backend payload', () {
    final tradeoff = Tradeoff.fromJson({
      'metric_chosen': 'dir',
      'justification': 'Disparate impact prioritised over equal opportunity for hiring fairness.',
      'conflicts_acknowledged': ['dir-vs-eod'],
      'selected_by_uid': 'demo-uid',
      'selected_by_name': 'Demo Reviewer',
      'selected_at': '2026-04-28T10:00:00Z',
    });

    expect(tradeoff.metricChosen, 'dir');
    expect(tradeoff.justification, contains('Disparate impact'));
    expect(tradeoff.conflictsAcknowledged, contains('dir-vs-eod'));
    expect(tradeoff.selectedByName, 'Demo Reviewer');
  });

  test('AuditDetail.fromJson surfaces tradeoff when present', () {
    final detail = AuditDetail.fromJson({
      'summary': {
        'audit_id': 'a1',
        'title': 'Audit',
        'status': 'analyzing',
        'mode': 'audit',
        'domain': 'hiring',
        'provenance_kind': 'synthetic',
        'provenance_label': 'placement_synthetic.csv',
      },
      'sensitive_attributes': ['gender'],
      'outcome_column': 'selected',
      'metrics': [],
      'heatmap_cells': [],
      'explanations': [],
      'conflicts': [],
      'proxies': [],
      'remediation': null,
      'sign_off': null,
      'tradeoff': {
        'metric_chosen': 'spd',
        'justification': 'Statistical parity prioritised; documented for audit trail.',
        'conflicts_acknowledged': ['spd-vs-eod'],
        'selected_by_uid': 'u',
        'selected_by_name': 'Reviewer',
        'selected_at': '2026-04-28T10:00:00Z',
      },
      'has_report': false,
    });

    expect(detail.tradeoff, isNotNull);
    expect(detail.tradeoff!.metricChosen, 'spd');
  });

  testWidgets('overview shows Resolve metric conflict prompt when conflicts exist', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(_ConflictApiClient())],
        child: const MaterialApp(
          home: AuditWorkspacePage(
            auditId: 'audit-conflict',
            tab: AuditWorkspaceTab.overview,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(find.text('Resolve metric conflict'), findsOneWidget);
    expect(find.textContaining('dir'), findsWidgets);
  });

  testWidgets('overview shows resolved tradeoff banner when tradeoff is present', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(_ResolvedTradeoffApiClient())],
        child: const MaterialApp(
          home: AuditWorkspacePage(
            auditId: 'audit-resolved',
            tab: AuditWorkspaceTab.overview,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(find.textContaining('Tradeoff resolved'), findsOneWidget);
    expect(find.textContaining('Demo Reviewer'), findsOneWidget);
  });
}

class _ConflictApiClient extends ApiClient {
  _ConflictApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<Map<String, dynamic>> getAudit(String auditId) async => _conflictDetail;
}

class _ResolvedTradeoffApiClient extends ApiClient {
  _ResolvedTradeoffApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<Map<String, dynamic>> getAudit(String auditId) async => _resolvedDetail;
}

final Map<String, dynamic> _conflictDetail = {
  'summary': {
    'audit_id': 'audit-conflict',
    'title': 'Audit with conflicts',
    'status': 'analyzing',
    'mode': 'audit',
    'domain': 'hiring',
    'provenance_kind': 'synthetic',
    'provenance_label': 'placement_synthetic.csv',
  },
  'sensitive_attributes': ['gender'],
  'outcome_column': 'selected',
  'metrics': [],
  'heatmap_cells': [],
  'explanations': [],
  'conflicts': [
    {
      'metric_a': 'dir',
      'metric_b': 'eod',
      'description': 'Disparate impact and equal opportunity disagree.',
    },
  ],
  'proxies': [],
  'remediation': null,
  'sign_off': null,
  'tradeoff': null,
  'has_report': false,
};

final Map<String, dynamic> _resolvedDetail = {
  ..._conflictDetail,
  'summary': {..._conflictDetail['summary']! as Map<String, dynamic>, 'audit_id': 'audit-resolved'},
  'tradeoff': {
    'metric_chosen': 'dir',
    'justification': 'Prioritised disparate impact for downstream hiring fairness.',
    'conflicts_acknowledged': ['dir-vs-eod'],
    'selected_by_uid': 'demo-uid',
    'selected_by_name': 'Demo Reviewer',
    'selected_at': '2026-04-28T10:00:00Z',
  },
};
