import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:nyayalens_client/features/audits/audit_session.dart';
import 'package:nyayalens_client/shared/models/audit_models.dart';
import 'package:nyayalens_client/shared/widgets/app_shell.dart';
import 'package:nyayalens_client/shared/widgets/nyaya_surface.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final audits = ref.watch(auditSummariesProvider);
    return NyayaAppShell(
      title: 'Audit command center',
      subtitle:
          'Run hiring fairness audits, track remediation, and preserve reviewer sign-off.',
      selectedRoute: '/',
      trailing: FilledButton.icon(
        onPressed: () => context.go('/audits/new'),
        icon: const Icon(Icons.add),
        label: const Text('New audit'),
      ),
      children: [
        audits.when(
          data: (items) => _DashboardMetrics(items: items),
          loading: () => const _LoadingPanel(),
          error: (error, stackTrace) => _LoadErrorPanel(
            message: friendlyApiError(error),
            onRetry: () => ref.invalidate(auditSummariesProvider),
          ),
        ),
        audits.when(
          data: (items) => _RecentAuditsPanel(items: items),
          loading: () => const SizedBox.shrink(),
          error: (error, stackTrace) => const SizedBox.shrink(),
        ),
        _ProcessPanel(),
      ],
    );
  }
}

class AuditsIndexPage extends ConsumerWidget {
  const AuditsIndexPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final audits = ref.watch(auditSummariesProvider);
    return NyayaAppShell(
      title: 'Audit registry',
      subtitle: 'Review every audit currently available from the local API.',
      selectedRoute: '/audits',
      trailing: OutlinedButton.icon(
        onPressed: () => ref.invalidate(auditSummariesProvider),
        icon: const Icon(Icons.refresh),
        label: const Text('Refresh'),
      ),
      children: [
        audits.when(
          data: (items) => _RecentAuditsPanel(items: items, expanded: true),
          loading: () => const _LoadingPanel(),
          error: (error, stackTrace) => _LoadErrorPanel(
            message: friendlyApiError(error),
            onRetry: () => ref.invalidate(auditSummariesProvider),
          ),
        ),
      ],
    );
  }
}

class _DashboardMetrics extends StatelessWidget {
  const _DashboardMetrics({required this.items});

  final List<AuditSummary> items;

  @override
  Widget build(BuildContext context) {
    final signed = items.where((item) => item.status == 'signed_off').length;
    final remediated = items.where((item) => item.status == 'remediated').length;
    final active = items
        .where((item) => item.status != 'signed_off' && item.status != 'archived')
        .length;
    return _ResponsiveTiles(
      children: [
        MetricTile(
          label: 'Total audits',
          value: '${items.length}',
          icon: Icons.folder_copy_outlined,
          detail: 'Local workspace records',
          tone: BadgeTone.info,
        ),
        MetricTile(
          label: 'Active reviews',
          value: '$active',
          icon: Icons.pending_actions_outlined,
          detail: 'Need review or sign-off',
          tone: active == 0 ? BadgeTone.good : BadgeTone.warning,
        ),
        MetricTile(
          label: 'Remediated',
          value: '$remediated',
          icon: Icons.tune_outlined,
          detail: 'Reweighting applied',
          tone: BadgeTone.good,
        ),
        MetricTile(
          label: 'Signed off',
          value: '$signed',
          icon: Icons.verified_outlined,
          detail: 'Report-ready audits',
          tone: BadgeTone.good,
        ),
      ],
    );
  }
}

class _RecentAuditsPanel extends StatelessWidget {
  const _RecentAuditsPanel({
    required this.items,
    this.expanded = false,
  });

  final List<AuditSummary> items;
  final bool expanded;

  @override
  Widget build(BuildContext context) {
    final visibleItems = expanded ? items : items.take(5).toList();
    if (items.isEmpty) {
      return EmptyStatePanel(
        icon: Icons.balance,
        title: 'No audits yet',
        message: 'Start with a CSV or XLSX file and NyayaLens will build the audit trail.',
        action: FilledButton.icon(
          onPressed: () => context.go('/audits/new'),
          icon: const Icon(Icons.upload_file),
          label: const Text('Upload dataset'),
        ),
      );
    }
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: expanded ? 'All audits' : 'Recent audits',
            subtitle: 'Open an audit to inspect metrics, remediation, and reports.',
            trailing: expanded
                ? null
                : TextButton(
                    onPressed: () => context.go('/audits'),
                    child: const Text('View all'),
                  ),
          ),
          const SizedBox(height: 16),
          for (final item in visibleItems) ...[
            _AuditListRow(item: item),
            if (item != visibleItems.last) const Divider(),
          ],
        ],
      ),
    );
  }
}

class _AuditListRow extends StatelessWidget {
  const _AuditListRow({required this.item});

  final AuditSummary item;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.go('/audits/${item.id}'),
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
        child: Row(
          children: [
            Icon(
              Icons.assignment_outlined,
              color: Theme.of(context).colorScheme.secondary,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${item.domain} - ${item.provenanceLabel}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            StatusBadge(
              label: displayStatus(item.status),
              tone: _statusTone(item.status),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }
}

class _ProcessPanel extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Review pipeline',
            subtitle:
                'The workflow keeps evidence, mitigation, reviewer notes, and reports together.',
          ),
          const SizedBox(height: 16),
          _Pipeline(
            steps: const [
              _PipelineStep('Upload', Icons.upload_file),
              _PipelineStep('Detect schema', Icons.schema_outlined),
              _PipelineStep('Analyze', Icons.analytics_outlined),
              _PipelineStep('Remediate', Icons.tune_outlined),
              _PipelineStep('Sign off', Icons.verified_outlined),
              _PipelineStep('Report', Icons.picture_as_pdf_outlined),
            ],
          ),
        ],
      ),
    );
  }
}

class _Pipeline extends StatelessWidget {
  const _Pipeline({required this.steps});

  final List<_PipelineStep> steps;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 720;
        return Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            for (final step in steps)
              SizedBox(
                width: compact ? constraints.maxWidth : 160,
                child: StatusBadge(
                  label: step.label,
                  tone: BadgeTone.neutral,
                  icon: step.icon,
                ),
              ),
          ],
        );
      },
    );
  }
}

class _PipelineStep {
  const _PipelineStep(this.label, this.icon);

  final String label;
  final IconData icon;
}

class _ResponsiveTiles extends StatelessWidget {
  const _ResponsiveTiles({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        const spacing = 12.0;
        final columns = constraints.maxWidth >= 1120
            ? 4
            : constraints.maxWidth >= 700
                ? 2
                : 1;
        final width = (constraints.maxWidth - spacing * (columns - 1)) / columns;
        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: [
            for (final child in children) SizedBox(width: width, child: child),
          ],
        );
      },
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const SurfacePanel(
      child: SizedBox(
        height: 160,
        child: Center(child: CircularProgressIndicator()),
      ),
    );
  }
}

class _LoadErrorPanel extends StatelessWidget {
  const _LoadErrorPanel({
    required this.message,
    required this.onRetry,
  });

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return EmptyStatePanel(
      icon: Icons.cloud_off_outlined,
      title: 'Could not load audits',
      message: message,
      action: OutlinedButton.icon(
        onPressed: onRetry,
        icon: const Icon(Icons.refresh),
        label: const Text('Retry'),
      ),
    );
  }
}

BadgeTone _statusTone(String status) {
  return switch (status) {
    'signed_off' => BadgeTone.good,
    'remediated' => BadgeTone.info,
    'ready_for_review' => BadgeTone.warning,
    'analyzing' => BadgeTone.warning,
    'archived' => BadgeTone.neutral,
    _ => BadgeTone.neutral,
  };
}
