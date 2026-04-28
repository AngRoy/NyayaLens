import 'package:flutter/material.dart';

import 'package:nyayalens_client/shared/models/audit_models.dart';
import 'package:nyayalens_client/shared/widgets/nyaya_surface.dart';

class DataQualityChip extends StatelessWidget {
  const DataQualityChip({super.key, required this.quality});

  final DataQuality quality;

  BadgeTone get _tone {
    if (quality.overallScore >= 0.85) return BadgeTone.good;
    if (quality.overallScore >= 0.6) return BadgeTone.warning;
    return BadgeTone.critical;
  }

  String get _label {
    if (quality.overallScore >= 0.85) return 'Healthy';
    if (quality.overallScore >= 0.6) return 'Caveats';
    return 'Risky';
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SurfacePanel(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Data quality',
            subtitle: 'Snapshot computed during upload — applies to fairness statistics downstream.',
            trailing: StatusBadge(
              label: '$_label · score ${quality.overallScore.toStringAsFixed(2)}',
              tone: _tone,
              icon: Icons.fact_check_outlined,
            ),
          ),
          const SizedBox(height: 14),
          LinearProgressIndicator(
            value: quality.overallScore.clamp(0, 1).toDouble(),
            minHeight: 6,
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _StatPill(label: 'Rows', value: quality.rowCount.toString()),
              _StatPill(label: 'Columns', value: quality.columnCount.toString()),
              _StatPill(label: 'Missing cells', value: _pct(quality.missingCellPct)),
              _StatPill(label: 'Duplicate rows', value: _pct(quality.duplicateRowPct)),
              _StatPill(label: 'Type consistency', value: _pct(quality.typeConsistencyPct)),
            ],
          ),
          const SizedBox(height: 14),
          if (quality.hasWarnings)
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final warning in quality.warnings)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.error_outline, size: 16, color: scheme.error),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            warning,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            )
          else
            Text(
              'No warnings — fairness analysis can proceed with default settings.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
        ],
      ),
    );
  }

  static String _pct(double value) => '${(value * 100).toStringAsFixed(1)}%';
}

class _StatPill extends StatelessWidget {
  const _StatPill({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        border: Border.all(color: scheme.outlineVariant),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(width: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
