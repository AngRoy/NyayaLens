// GoRouter configuration.
//
// Screens map 1:1 to the design doc §12 inventory. Week-1 scope is S01
// (landing), S02 (home), S03 (upload wizard); remaining screens follow in
// weeks 2–3. Each feature lives under `lib/features/<slug>/`.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: <RouteBase>[
      GoRoute(
        path: '/',
        name: 'landing',
        builder: (context, state) => const _PlaceholderScreen(
          title: 'S01 Landing / Auth',
          body: 'Sign-in flow lands here on Day 2-3.',
        ),
      ),
      GoRoute(
        path: '/home',
        name: 'home',
        builder: (context, state) => const _PlaceholderScreen(
          title: 'S02 Home Dashboard',
          body: 'List of audits, New Audit CTA (Week 1 Day 3-4).',
        ),
      ),
      GoRoute(
        path: '/upload',
        name: 'upload',
        builder: (context, state) => const _PlaceholderScreen(
          title: 'S03 Upload Wizard',
          body: 'Drag-drop + file preview (Week 1 Day 4-5).',
        ),
      ),
      // S04 Schema Review, S05 Analysis Dashboard etc. are added incrementally.
    ],
  );
});

class _PlaceholderScreen extends StatelessWidget {
  const _PlaceholderScreen({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('NyayaLens · $title')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(body, textAlign: TextAlign.center),
        ),
      ),
    );
  }
}
