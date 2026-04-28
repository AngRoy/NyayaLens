import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:nyayalens_client/features/audits/audit_session.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/models/audit_models.dart';
import 'package:nyayalens_client/shared/platform/url_opener.dart';
import 'package:nyayalens_client/shared/widgets/app_shell.dart';
import 'package:nyayalens_client/shared/widgets/bias_heatmap.dart';
import 'package:nyayalens_client/shared/widgets/data_quality_chip.dart';
import 'package:nyayalens_client/shared/widgets/nyaya_surface.dart';

enum AuditWorkspaceTab { overview, remediation, signoff, report }

class NewAuditPage extends ConsumerWidget {
  const NewAuditPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(auditSessionProvider);
    return NyayaAppShell(
      title: 'New fairness audit',
      subtitle:
          'Upload a dataset, confirm the detected schema, and launch the audit workspace.',
      selectedRoute: '/audits/new',
      trailing: session.hasProgress
          ? OutlinedButton.icon(
              onPressed: session.busy ? null : session.reset,
              icon: const Icon(Icons.restart_alt),
              label: const Text('Start over'),
            )
          : null,
      children: [
        if (session.error != null)
          _ErrorBanner(
            message: session.error!,
            onDismiss: session.clearError,
          ),
        if (session.busy) _BusyPanel(label: session.busyLabel),
        _UploadPanel(session: session),
        if (session.quality != null) ...[
          const SizedBox(height: 18),
          DataQualityChip(quality: session.quality!),
        ],
        if (session.schema != null) _SchemaReviewPanel(session: session),
      ],
    );
  }
}

class AuditWorkspacePage extends ConsumerStatefulWidget {
  const AuditWorkspacePage({
    super.key,
    required this.auditId,
    required this.tab,
  });

  final String auditId;
  final AuditWorkspaceTab tab;

  @override
  ConsumerState<AuditWorkspacePage> createState() => _AuditWorkspacePageState();
}

class _AuditWorkspacePageState extends ConsumerState<AuditWorkspacePage> {
  @override
  void initState() {
    super.initState();
    _scheduleLoad();
  }

  @override
  void didUpdateWidget(covariant AuditWorkspacePage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.auditId != widget.auditId) _scheduleLoad();
  }

  void _scheduleLoad() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final session = ref.read(auditSessionProvider);
      if (session.audit?.id == widget.auditId || session.busy) return;
      session.loadAudit(ref.read(apiClientProvider), widget.auditId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(auditSessionProvider);
    final audit = session.audit?.id == widget.auditId ? session.audit : null;
    return NyayaAppShell(
      title: audit?.title ?? 'Audit workspace',
      subtitle: audit == null
          ? 'Loading audit evidence from the local API.'
          : '${audit.summary.domain} audit - ${displayStatus(audit.status)}',
      selectedRoute: '/audits/${widget.auditId}',
      trailing: audit == null ? null : _WorkspaceActions(audit: audit),
      children: [
        if (session.error != null)
          _ErrorBanner(
            message: session.error!,
            onDismiss: session.clearError,
          ),
        if (session.busy && audit == null) _BusyPanel(label: session.busyLabel),
        if (audit == null && !session.busy)
          EmptyStatePanel(
            icon: Icons.manage_search_outlined,
            title: 'Audit not loaded',
            message:
                'The backend may have restarted or the audit id may no longer be in memory.',
            action: FilledButton.icon(
              onPressed: () => context.go('/audits/new'),
              icon: const Icon(Icons.upload_file),
              label: const Text('Start another audit'),
            ),
          )
        else if (audit != null) ...[
          _WorkspaceTabs(auditId: widget.auditId, tab: widget.tab),
          switch (widget.tab) {
            AuditWorkspaceTab.overview => _AuditOverview(audit: audit),
            AuditWorkspaceTab.remediation => _RemediationView(audit: audit),
            AuditWorkspaceTab.signoff => _SignOffView(audit: audit),
            AuditWorkspaceTab.report => _ReportView(audit: audit),
          },
        ],
      ],
    );
  }
}

class _UploadPanel extends ConsumerWidget {
  const _UploadPanel({required this.session});

  final AuditSession session;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Dataset intake',
            subtitle: 'CSV and XLSX files up to the backend upload limit are accepted.',
          ),
          const SizedBox(height: 18),
          LayoutBuilder(
            builder: (context, constraints) {
              final compact = constraints.maxWidth < 680;
              final picker = OutlinedButton.icon(
                onPressed: session.busy ? null : session.pickFile,
                icon: const Icon(Icons.upload_file),
                label: Text(
                  session.fileName ?? 'Choose dataset',
                  overflow: TextOverflow.ellipsis,
                ),
              );
              final upload = FilledButton.icon(
                onPressed: session.canUpload
                    ? () => session.uploadAndDetect(ref.read(apiClientProvider))
                    : null,
                icon: const Icon(Icons.schema_outlined),
                label: const Text('Upload and detect schema'),
              );
              if (compact) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    picker,
                    const SizedBox(height: 10),
                    upload,
                  ],
                );
              }
              return Row(
                children: [
                  Expanded(child: picker),
                  const SizedBox(width: 12),
                  upload,
                ],
              );
            },
          ),
          if (session.datasetId != null) ...[
            const SizedBox(height: 14),
            StatusBadge(
              label: 'Dataset ${session.datasetId}',
              tone: BadgeTone.info,
              icon: Icons.dataset_outlined,
            ),
          ],
        ],
      ),
    );
  }
}

class _SchemaReviewPanel extends ConsumerWidget {
  const _SchemaReviewPanel({required this.session});

  final AuditSession session;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final schema = session.schema!;
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Schema review',
            subtitle:
                '${schema.sensitiveAttributes.length} sensitive attributes detected.',
            trailing: StatusBadge(
              label: schema.needsReview ? 'Review needed' : 'High confidence',
              tone: schema.needsReview ? BadgeTone.warning : BadgeTone.good,
              icon: schema.needsReview
                  ? Icons.rate_review_outlined
                  : Icons.check_circle_outline,
            ),
          ),
          const SizedBox(height: 18),
          _SchemaGrid(schema: schema),
          const SizedBox(height: 18),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.icon(
              onPressed: session.canAnalyze
                  ? () async {
                      final auditId = await session.createAndAnalyze(
                        ref.read(apiClientProvider),
                      );
                      if (auditId != null && context.mounted) {
                        context.go('/audits/$auditId');
                        ref.invalidate(auditSummariesProvider);
                      }
                    }
                  : null,
              icon: const Icon(Icons.play_arrow),
              label: const Text('Confirm and run analysis'),
            ),
          ),
        ],
      ),
    );
  }
}

class _SchemaGrid extends StatelessWidget {
  const _SchemaGrid({required this.schema});

  final SchemaDetection schema;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 920
            ? 3
            : constraints.maxWidth >= 620
                ? 2
                : 1;
        const spacing = 12.0;
        final width = (constraints.maxWidth - spacing * (columns - 1)) / columns;
        final cards = <Widget>[
          for (final attribute in schema.sensitiveAttributes)
            _SchemaCard(
              icon: Icons.shield_outlined,
              title: attribute.column,
              eyebrow: attribute.category,
              detail: attribute.rationale,
              score: attribute.confidence,
            ),
          if (schema.outcomeColumn != null)
            _SchemaCard(
              icon: Icons.flag_outlined,
              title: schema.outcomeColumn!.column,
              eyebrow: 'Outcome',
              detail: 'Positive value: ${schema.outcomeColumn!.positiveValue}',
              score: schema.outcomeColumn!.confidence,
            ),
          if (schema.scoreColumn != null)
            _SchemaCard(
              icon: Icons.stacked_line_chart,
              title: schema.scoreColumn!,
              eyebrow: 'Score column',
              detail: 'Used as a continuous score when available.',
              score: null,
            ),
        ];
        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: [
            for (final card in cards) SizedBox(width: width, child: card),
          ],
        );
      },
    );
  }
}

class _SchemaCard extends StatelessWidget {
  const _SchemaCard({
    required this.icon,
    required this.title,
    required this.eyebrow,
    required this.detail,
    required this.score,
  });

  final IconData icon;
  final String title;
  final String eyebrow;
  final String detail;
  final double? score;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: Theme.of(context).colorScheme.secondary),
            const SizedBox(height: 12),
            Text(
              eyebrow.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              detail,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (score != null) ...[
              const SizedBox(height: 10),
              LinearProgressIndicator(value: score!.clamp(0, 1).toDouble()),
            ],
          ],
        ),
      ),
    );
  }
}

class _WorkspaceActions extends StatelessWidget {
  const _WorkspaceActions({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        OutlinedButton.icon(
          onPressed: () => context.go('/audits/${audit.id}/remediation'),
          icon: const Icon(Icons.tune_outlined),
          label: const Text('Remediate'),
        ),
        FilledButton.icon(
          onPressed: () => context.go('/audits/${audit.id}/report'),
          icon: const Icon(Icons.picture_as_pdf_outlined),
          label: const Text('Report'),
        ),
      ],
    );
  }
}

class _WorkspaceTabs extends StatelessWidget {
  const _WorkspaceTabs({
    required this.auditId,
    required this.tab,
  });

  final String auditId;
  final AuditWorkspaceTab tab;

  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      padding: const EdgeInsets.all(12),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: SegmentedButton<AuditWorkspaceTab>(
          selected: {tab},
          onSelectionChanged: (selection) {
            context.go(_tabRoute(auditId, selection.first));
          },
          segments: const [
            ButtonSegment(
              value: AuditWorkspaceTab.overview,
              icon: Icon(Icons.analytics_outlined),
              label: Text('Overview'),
            ),
            ButtonSegment(
              value: AuditWorkspaceTab.remediation,
              icon: Icon(Icons.tune_outlined),
              label: Text('Remediation'),
            ),
            ButtonSegment(
              value: AuditWorkspaceTab.signoff,
              icon: Icon(Icons.verified_outlined),
              label: Text('Sign-off'),
            ),
            ButtonSegment(
              value: AuditWorkspaceTab.report,
              icon: Icon(Icons.picture_as_pdf_outlined),
              label: Text('Report'),
            ),
          ],
        ),
      ),
    );
  }
}

class _AuditOverview extends StatelessWidget {
  const _AuditOverview({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _AuditMetricGrid(audit: audit),
        const SizedBox(height: 18),
        _HeatmapPanel(audit: audit),
        const SizedBox(height: 18),
        _FindingsPanel(audit: audit),
      ],
    );
  }
}

class _AuditMetricGrid extends StatelessWidget {
  const _AuditMetricGrid({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context) {
    return _ResponsiveGrid(
      children: [
        MetricTile(
          label: 'Critical cells',
          value: '${audit.criticalCount}',
          icon: Icons.priority_high,
          detail: 'Across fairness metrics',
          tone: audit.criticalCount > 0 ? BadgeTone.critical : BadgeTone.good,
        ),
        MetricTile(
          label: 'Warnings',
          value: '${audit.warningCount}',
          icon: Icons.warning_amber_outlined,
          detail: 'Needs reviewer attention',
          tone: audit.warningCount > 0 ? BadgeTone.warning : BadgeTone.good,
        ),
        MetricTile(
          label: 'Sensitive attributes',
          value: '${audit.sensitiveAttributes.length}',
          icon: Icons.shield_outlined,
          detail: audit.sensitiveAttributes.join(', '),
          tone: BadgeTone.info,
        ),
        MetricTile(
          label: 'Workflow status',
          value: displayStatus(audit.status),
          icon: Icons.route_outlined,
          detail: audit.hasReport ? 'Report generated' : 'Report pending',
          tone: _statusTone(audit.status),
        ),
      ],
    );
  }
}

class _HeatmapPanel extends StatelessWidget {
  const _HeatmapPanel({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context) {
    if (audit.heatmapCells.isEmpty || audit.sensitiveAttributes.isEmpty) {
      return const EmptyStatePanel(
        icon: Icons.grid_off_outlined,
        title: 'No metric grid yet',
        message: 'Run analysis for this audit to produce a fairness heatmap.',
      );
    }
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Bias heatmap',
            subtitle: 'Severity-colored metric results by protected attribute.',
          ),
          const SizedBox(height: 18),
          BiasHeatmap(
            attributes: audit.sensitiveAttributes,
            metrics: audit.metricNames,
            cells: [
              for (final cell in audit.heatmapCells)
                HeatmapCell(
                  attribute: cell.attribute,
                  metric: cell.metric,
                  value: cell.value,
                  severity: cell.severity,
                  note: cell.note,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _FindingsPanel extends StatelessWidget {
  const _FindingsPanel({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Reviewer brief',
            subtitle: 'Grounded explanations, metric tensions, and proxy signals.',
          ),
          const SizedBox(height: 18),
          if (audit.explanations.isEmpty &&
              audit.conflicts.isEmpty &&
              audit.proxies.isEmpty)
            Text(
              'No additional findings were returned by the backend.',
              style: Theme.of(context).textTheme.bodyMedium,
            )
          else ...[
            for (final explanation in audit.explanations)
              _FindingRow(
                icon: explanation.grounded
                    ? Icons.psychology_alt_outlined
                    : Icons.rule_outlined,
                title: '${explanation.metric} - ${explanation.attribute}',
                body: explanation.summary,
                footnote: explanation.interpretation,
              ),
            for (final conflict in audit.conflicts)
              _FindingRow(
                icon: Icons.compare_arrows,
                title: '${conflict.metricA} vs ${conflict.metricB}',
                body: conflict.description,
              ),
            for (final proxy in audit.proxies)
              _FindingRow(
                icon: Icons.link_outlined,
                title: '${proxy.feature} -> ${proxy.sensitiveAttribute}',
                body:
                    '${proxy.method} strength ${proxy.strength.toStringAsFixed(2)} '
                    '(${proxy.severity})',
              ),
          ],
        ],
      ),
    );
  }
}

class _FindingRow extends StatelessWidget {
  const _FindingRow({
    required this.icon,
    required this.title,
    required this.body,
    this.footnote,
  });

  final IconData icon;
  final String title;
  final String body;
  final String? footnote;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Theme.of(context).colorScheme.secondary),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                if (body.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(body),
                ],
                if (footnote != null && footnote!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    footnote!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RemediationView extends ConsumerWidget {
  const _RemediationView({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final remediation = audit.remediation;
    final session = ref.watch(auditSessionProvider);
    if (remediation != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SurfacePanel(
            child: SectionHeader(
              title: 'Reweighting remediation',
              subtitle: 'Before and after disparity ratios from the backend.',
              trailing: StatusBadge(
                label: 'Applied',
                tone: BadgeTone.good,
                icon: Icons.check_circle_outline,
              ),
            ),
          ),
          const SizedBox(height: 18),
          _ResponsiveGrid(
            children: [
              MetricTile(
                label: 'DIR before',
                value: formatScore(remediation.dirBefore),
                icon: Icons.arrow_circle_left_outlined,
                detail: 'Disparate impact ratio',
                tone: BadgeTone.warning,
              ),
              MetricTile(
                label: 'DIR after',
                value: formatScore(remediation.dirAfter),
                icon: Icons.arrow_circle_right_outlined,
                detail: 'Post-reweighting ratio',
                tone: BadgeTone.good,
              ),
              MetricTile(
                label: 'SPD before',
                value: formatScore(remediation.spdBefore, digits: 3),
                icon: Icons.compare_arrows,
                detail: 'Statistical parity delta',
                tone: BadgeTone.warning,
              ),
              MetricTile(
                label: 'Accuracy delta',
                value: formatScore(remediation.accuracyEstimateDelta, digits: 3),
                icon: Icons.speed_outlined,
                detail: 'Estimated impact',
                tone: remediation.accuracyEstimateDelta < 0
                    ? BadgeTone.warning
                    : BadgeTone.good,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.icon(
              onPressed: () => context.go('/audits/${audit.id}/signoff'),
              icon: const Icon(Icons.verified_outlined),
              label: const Text('Continue to sign-off'),
            ),
          ),
        ],
      );
    }
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Reweighting remediation',
            subtitle: 'Apply mitigation after reviewing the heatmap and findings.',
            trailing: FilledButton.icon(
              onPressed: session.busy
                  ? null
                  : () async {
                      await session.applyReweighting(ref.read(apiClientProvider));
                      ref.invalidate(auditSummariesProvider);
                    },
              icon: const Icon(Icons.tune),
              label: const Text('Apply reweighting'),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                Icons.tune_outlined,
                color: Theme.of(context).colorScheme.secondary,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'No remediation has been applied. The audit can continue, '
                  'but sign-off should document that decision.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerRight,
            child: OutlinedButton.icon(
              onPressed: () => context.go('/audits/${audit.id}/signoff'),
              icon: const Icon(Icons.verified_outlined),
              label: const Text('Continue without mitigation'),
            ),
          ),
        ],
      ),
    );
  }
}

class _SignOffView extends StatelessWidget {
  const _SignOffView({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context) {
    final signOff = audit.signOff;
    if (signOff != null) {
      return SurfacePanel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SectionHeader(
              title: 'Reviewer approval',
              subtitle: 'This audit has reviewer sign-off recorded by the backend.',
            ),
            const SizedBox(height: 18),
            StatusBadge(
              label: 'Signed by ${signOff.reviewerName} (${signOff.reviewerRole})',
              tone: BadgeTone.good,
              icon: Icons.verified,
            ),
            const SizedBox(height: 12),
            Text(signOff.notes),
            const SizedBox(height: 18),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: () => context.go('/audits/${audit.id}/report'),
                icon: const Icon(Icons.picture_as_pdf_outlined),
                label: const Text('Prepare report'),
              ),
            ),
          ],
        ),
      );
    }
    return _SignOffForm(audit: audit);
  }
}

class _SignOffForm extends ConsumerStatefulWidget {
  const _SignOffForm({required this.audit});

  final AuditDetail audit;

  @override
  ConsumerState<_SignOffForm> createState() => _SignOffFormState();
}

class _SignOffFormState extends ConsumerState<_SignOffForm> {
  final _controller = TextEditingController(
    text:
        'Reviewed disparity findings and mitigation tradeoffs. Proceeding with '
        'documented approval.',
  );
  bool _confirmed = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(auditSessionProvider);
    final canSign = _confirmed && _controller.text.trim().length >= 10 && !session.busy;
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Reviewer sign-off',
            subtitle: 'Record a human decision before the final audit report is produced.',
          ),
          const SizedBox(height: 18),
          TextField(
            controller: _controller,
            maxLines: 4,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              labelText: 'Decision notes',
            ),
          ),
          const SizedBox(height: 8),
          CheckboxListTile(
            value: _confirmed,
            onChanged: (value) => setState(() => _confirmed = value ?? false),
            contentPadding: EdgeInsets.zero,
            title: const Text('I reviewed the fairness findings and mitigation tradeoffs.'),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.icon(
              onPressed: canSign
                  ? () async {
                      await session.signOff(
                        ref.read(apiClientProvider),
                        _controller.text.trim(),
                      );
                      ref.invalidate(auditSummariesProvider);
                      if (context.mounted) {
                        context.go('/audits/${widget.audit.id}/report');
                      }
                    }
                  : null,
              icon: const Icon(Icons.verified_outlined),
              label: const Text('Sign off audit'),
            ),
          ),
        ],
      ),
    );
  }
}

class _ReportView extends ConsumerWidget {
  const _ReportView({required this.audit});

  final AuditDetail audit;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(auditSessionProvider);
    final signed = audit.signOff != null || audit.status == 'signed_off';
    if (!signed) {
      return EmptyStatePanel(
        icon: Icons.lock_outline,
        title: 'Sign-off required',
        message: 'Generate the PDF report after a reviewer signs off the audit.',
        action: FilledButton.icon(
          onPressed: () => context.go('/audits/${audit.id}/signoff'),
          icon: const Icon(Icons.verified_outlined),
          label: const Text('Go to sign-off'),
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SurfacePanel(
          child: SectionHeader(
            title: 'Audit report',
            subtitle: audit.hasReport
                ? 'The PDF is ready to open from the backend report endpoint.'
                : 'Generate a PDF with metrics, remediation, and reviewer notes.',
            trailing: StatusBadge(
              label: audit.hasReport ? 'Ready' : 'Not generated',
              tone: audit.hasReport ? BadgeTone.good : BadgeTone.warning,
              icon: audit.hasReport
                  ? Icons.check_circle_outline
                  : Icons.pending_outlined,
            ),
          ),
        ),
        const SizedBox(height: 18),
        _ResponsiveGrid(
          children: [
            MetricTile(
              label: 'Protected attributes',
              value: '${audit.sensitiveAttributes.length}',
              icon: Icons.shield_outlined,
              detail: audit.sensitiveAttributes.join(', '),
              tone: BadgeTone.info,
            ),
            MetricTile(
              label: 'Critical findings',
              value: '${audit.criticalCount}',
              icon: Icons.priority_high,
              detail: 'Included in the report',
              tone: audit.criticalCount > 0 ? BadgeTone.critical : BadgeTone.good,
            ),
            MetricTile(
              label: 'Remediation',
              value: audit.remediation == null ? 'None' : 'Applied',
              icon: Icons.tune_outlined,
              detail: 'Reviewer-visible decision',
              tone: audit.remediation == null ? BadgeTone.neutral : BadgeTone.good,
            ),
          ],
        ),
        const SizedBox(height: 18),
        SurfacePanel(
          padding: const EdgeInsets.all(14),
          child: Align(
            alignment: Alignment.centerRight,
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                if (!audit.hasReport)
                  FilledButton.icon(
                    onPressed: session.busy
                        ? null
                        : () async {
                            await session.generateReport(ref.read(apiClientProvider));
                            ref.invalidate(auditSummariesProvider);
                          },
                    icon: const Icon(Icons.picture_as_pdf_outlined),
                    label: const Text('Generate report'),
                  )
                else
                  FilledButton.icon(
                    onPressed: session.reportUrl == null
                        ? null
                        : () => openExternalUrl(session.reportUrl!),
                    icon: const Icon(Icons.open_in_new),
                    label: const Text('Open PDF'),
                  ),
                OutlinedButton.icon(
                  onPressed: () => context.go('/audits/${audit.id}'),
                  icon: const Icon(Icons.analytics_outlined),
                  label: const Text('Back to overview'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ResponsiveGrid extends StatelessWidget {
  const _ResponsiveGrid({required this.children});

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

class _BusyPanel extends StatelessWidget {
  const _BusyPanel({this.label});

  final String? label;

  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      child: SizedBox(
        height: 96,
        child: Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              if (label != null) ...[
                const SizedBox(width: 16),
                Flexible(
                  child: Text(
                    label!,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({
    required this.message,
    required this.onDismiss,
  });

  final String message;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      padding: const EdgeInsets.all(14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline, color: Theme.of(context).colorScheme.error),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.error,
                  ),
            ),
          ),
          IconButton(
            tooltip: 'Dismiss',
            onPressed: onDismiss,
            icon: const Icon(Icons.close),
          ),
        ],
      ),
    );
  }
}

String _tabRoute(String auditId, AuditWorkspaceTab tab) {
  return switch (tab) {
    AuditWorkspaceTab.overview => '/audits/$auditId',
    AuditWorkspaceTab.remediation => '/audits/$auditId/remediation',
    AuditWorkspaceTab.signoff => '/audits/$auditId/signoff',
    AuditWorkspaceTab.report => '/audits/$auditId/report',
  };
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
