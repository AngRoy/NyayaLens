// RED reproducer for the 409 mode-guard friendly error path.
//
// The backend refuses lifecycle endpoints (analyze, remediate, sign-off,
// recourse, report) on probe-mode audits with HTTP 409 + a detail that
// names "probe". The Flutter shell must surface a humane toast and hide
// lifecycle actions on the workspace page so reviewers don't keep
// clicking buttons that will keep returning 409.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:nyayalens_client/features/audits/audit_pages.dart';
import 'package:nyayalens_client/features/audits/audit_session.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';

void main() {
  test('friendlyApiError maps 409 probe-mode detail to a clear message', () {
    final message = friendlyApiError(
      ApiException(
        "Audit is in 'probe' mode; lifecycle endpoints are reserved for 'audit' mode.",
        409,
      ),
    );

    expect(message, contains('probe'));
    expect(message.toLowerCase(), contains('mode'));
  });

  test('friendlyApiError leaves unrelated 409 errors untouched', () {
    final message = friendlyApiError(
      ApiException('Audit already signed off; further edits are blocked.', 409),
    );

    expect(message, contains('signed off'));
  });

  testWidgets('workspace hides remediate / report actions for probe-mode audits', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(_ProbeModeApiClient())],
        child: const MaterialApp(
          home: AuditWorkspacePage(
            auditId: 'probe-1',
            tab: AuditWorkspaceTab.overview,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(find.widgetWithText(OutlinedButton, 'Remediate'), findsNothing);
    expect(find.widgetWithText(FilledButton, 'Report'), findsNothing);
    expect(find.textContaining('Probe'), findsWidgets);
  });
}

class _ProbeModeApiClient extends ApiClient {
  _ProbeModeApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<Map<String, dynamic>> getAudit(String auditId) async {
    return _probeAuditDetail;
  }
}

final Map<String, dynamic> _probeAuditDetail = {
  'summary': {
    'audit_id': 'probe-1',
    'title': 'JD perturbation probe',
    'status': 'analyzing',
    'mode': 'probe',
    'domain': 'hiring',
    'provenance_kind': 'llm_generated',
    'provenance_label': 'Synthetic JD perturbation set',
  },
  'sensitive_attributes': ['gender'],
  'outcome_column': null,
  'metrics': [],
  'heatmap_cells': [],
  'explanations': [],
  'conflicts': [],
  'proxies': [],
  'remediation': null,
  'sign_off': null,
  'has_report': false,
};
