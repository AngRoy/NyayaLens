// RED reproducer for the recourse review dashboard.
//
// Reviewers need a /recourse page that lists all recourse requests for
// their organisation with assignee + status + a way to assign or
// resolve. This test pins the wire model parsing and that the new
// RecourseReviewPage renders the requests returned by the API.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:nyayalens_client/features/recourse/recourse_review_page.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/models/audit_models.dart';

void main() {
  test('RecourseRequest.fromJson parses backend wire payload', () {
    final request = RecourseRequest.fromJson({
      'request_id': 'req-1',
      'audit_id': 'audit-1',
      'organization_id': 'demo-org',
      'applicant_identifier': 'APP-2026-001',
      'contact_email': 'applicant@example.com',
      'request_type': 'human_review',
      'body': 'I would like a human reviewer to revisit my application.',
      'status': 'pending',
      'assigned_to_uid': null,
      'assigned_to_name': null,
      'reviewer_notes': '',
      'created_at': '2026-04-28T10:00:00Z',
      'resolved_at': null,
    });

    expect(request.requestId, 'req-1');
    expect(request.applicantIdentifier, 'APP-2026-001');
    expect(request.requestType, 'human_review');
    expect(request.status, 'pending');
    expect(request.assignedToName, isNull);
  });

  testWidgets('RecourseReviewPage lists requests returned by the API', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(_RecourseApiClient())],
        child: const MaterialApp(home: RecourseReviewPage()),
      ),
    );
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.text('Recourse review'), findsOneWidget);
    expect(find.textContaining('APP-2026-001'), findsOneWidget);
    expect(find.textContaining('Pending'), findsWidgets);
  });

  testWidgets('RecourseReviewPage renders an empty state when no requests', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(_EmptyRecourseApiClient())],
        child: const MaterialApp(home: RecourseReviewPage()),
      ),
    );
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.textContaining('No recourse requests'), findsOneWidget);
  });
}

class _RecourseApiClient extends ApiClient {
  _RecourseApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<List<Object?>> listRecourseRequests() async {
    return [
      _pendingRecord,
      _resolvedRecord,
    ];
  }
}

class _EmptyRecourseApiClient extends ApiClient {
  _EmptyRecourseApiClient() : super(baseUrl: 'http://test.invalid');

  @override
  Future<List<Object?>> listRecourseRequests() async => const <Object?>[];
}

const Map<String, dynamic> _pendingRecord = {
  'request_id': 'req-1',
  'audit_id': 'audit-1',
  'organization_id': 'demo-org',
  'applicant_identifier': 'APP-2026-001',
  'contact_email': 'a1@example.com',
  'request_type': 'human_review',
  'body': 'Please re-review the screening decision.',
  'status': 'pending',
  'assigned_to_uid': null,
  'assigned_to_name': null,
  'reviewer_notes': '',
  'created_at': '2026-04-28T10:00:00Z',
  'resolved_at': null,
};

const Map<String, dynamic> _resolvedRecord = {
  'request_id': 'req-2',
  'audit_id': 'audit-1',
  'organization_id': 'demo-org',
  'applicant_identifier': 'APP-2026-002',
  'contact_email': 'a2@example.com',
  'request_type': 'explanation',
  'body': 'I would like the reasons behind the decision.',
  'status': 'resolved_overturned',
  'assigned_to_uid': 'rev-uid',
  'assigned_to_name': 'Reviewer Two',
  'reviewer_notes': 'Decision overturned after manual review.',
  'created_at': '2026-04-25T08:00:00Z',
  'resolved_at': '2026-04-27T09:00:00Z',
};
