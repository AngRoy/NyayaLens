import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:nyayalens_client/features/audits/audit_pages.dart';
import 'package:nyayalens_client/features/dashboard/dashboard_page.dart';
import 'package:nyayalens_client/features/recourse/recourse_review_page.dart';
import 'package:nyayalens_client/features/settings/settings_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: <RouteBase>[
      GoRoute(
        path: '/',
        name: 'dashboard',
        builder: (context, state) => const DashboardPage(),
      ),
      GoRoute(
        path: '/demo',
        redirect: (context, state) => '/audits/new',
      ),
      GoRoute(
        path: '/audits',
        name: 'audits',
        builder: (context, state) => const AuditsIndexPage(),
        routes: [
          GoRoute(
            path: 'new',
            name: 'new-audit',
            builder: (context, state) => const NewAuditPage(),
          ),
          GoRoute(
            path: ':auditId',
            name: 'audit-overview',
            builder: (context, state) => AuditWorkspacePage(
              auditId: state.pathParameters['auditId'] ?? '',
              tab: AuditWorkspaceTab.overview,
            ),
            routes: [
              GoRoute(
                path: 'remediation',
                name: 'audit-remediation',
                builder: (context, state) => AuditWorkspacePage(
                  auditId: state.pathParameters['auditId'] ?? '',
                  tab: AuditWorkspaceTab.remediation,
                ),
              ),
              GoRoute(
                path: 'signoff',
                name: 'audit-signoff',
                builder: (context, state) => AuditWorkspacePage(
                  auditId: state.pathParameters['auditId'] ?? '',
                  tab: AuditWorkspaceTab.signoff,
                ),
              ),
              GoRoute(
                path: 'report',
                name: 'audit-report',
                builder: (context, state) => AuditWorkspacePage(
                  auditId: state.pathParameters['auditId'] ?? '',
                  tab: AuditWorkspaceTab.report,
                ),
              ),
            ],
          ),
        ],
      ),
      GoRoute(
        path: '/recourse',
        name: 'recourse-review',
        builder: (context, state) => const RecourseReviewPage(),
      ),
      GoRoute(
        path: '/settings',
        name: 'settings',
        builder: (context, state) => const SettingsPage(),
      ),
    ],
  );
});
