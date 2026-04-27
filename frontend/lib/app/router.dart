// GoRouter configuration.
//
// Screens map 1:1 to the design doc §12 inventory. Week-1 scope is S01
// (landing), S02 (home), S03 (upload wizard); remaining screens follow in
// weeks 2–3. Each feature lives under `lib/features/<slug>/`.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:nyayalens_client/features/demo/demo_flow.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: <RouteBase>[
      GoRoute(
        path: '/',
        name: 'landing',
        builder: (context, state) => const _Landing(),
      ),
      GoRoute(
        path: '/demo',
        name: 'demo',
        builder: (context, state) => const DemoFlowScreen(),
      ),
    ],
  );
});

class _Landing extends StatelessWidget {
  const _Landing();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('NyayaLens')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'NyayaLens — The Eye of Justice',
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              const SizedBox(
                width: 520,
                child: Text(
                  'AI accountability for hiring fairness. Upload a dataset, '
                  'detect sensitive attributes, run five fairness metrics, '
                  'apply reweighting, sign off, and download an audit '
                  'report — all with a documented human-in-the-loop trail.',
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 32),
              FilledButton.icon(
                onPressed: () => context.go('/demo'),
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start audit demo'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
