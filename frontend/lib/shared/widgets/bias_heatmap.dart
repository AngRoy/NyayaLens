// BiasHeatmap — the Analysis Dashboard hero widget (S05).
//
// Renders a metric × attribute grid with severity-coloured cells. Tapping
// a cell triggers a drill-down callback. Inspired by the
// responsible-ai-toolbox heatmap; built with plain Flutter widgets.

import 'package:flutter/material.dart';

class HeatmapCell {
  const HeatmapCell({
    required this.attribute,
    required this.metric,
    required this.value,
    required this.severity,
    this.note = '',
  });

  final String attribute;
  final String metric;
  final double? value;
  final String severity; // ok | warning | critical | unavailable
  final String note;
}

class BiasHeatmap extends StatelessWidget {
  const BiasHeatmap({
    super.key,
    required this.attributes,
    required this.metrics,
    required this.cells,
    this.onCellTap,
  });

  final List<String> attributes;
  final List<String> metrics;
  final List<HeatmapCell> cells;
  final void Function(HeatmapCell)? onCellTap;

  Color _severityColor(String severity, BuildContext context) {
    switch (severity) {
      case 'ok':
        return const Color(0xFF2E7D32);
      case 'warning':
        return const Color(0xFFF9A825);
      case 'critical':
        return const Color(0xFFC62828);
      case 'unavailable':
      default:
        return Theme.of(context).colorScheme.outlineVariant;
    }
  }

  String _formatValue(HeatmapCell cell) {
    if (cell.severity == 'unavailable' || cell.value == null) return 'n/a';
    return cell.value!.toStringAsFixed(2);
  }

  HeatmapCell? _lookup(String attribute, String metric) {
    for (final c in cells) {
      if (c.attribute == attribute && c.metric == metric) return c;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    const cellWidth = 110.0;
    const rowHeight = 60.0;
    const headerHeight = 40.0;
    const attributeColumnWidth = 140.0;

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SizedBox(
        width: attributeColumnWidth + cellWidth * metrics.length,
        height: headerHeight + rowHeight * attributes.length,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: headerHeight,
              child: Row(
                children: [
                  const SizedBox(width: attributeColumnWidth),
                  for (final m in metrics)
                    SizedBox(
                      width: cellWidth,
                      child: Center(
                        child: Text(
                          m.toUpperCase(),
                          style: Theme.of(context)
                              .textTheme
                              .labelMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            for (final attr in attributes)
              SizedBox(
                height: rowHeight,
                child: Row(
                  children: [
                    SizedBox(
                      width: attributeColumnWidth,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: Center(
                          child: Text(
                            attr,
                            style: Theme.of(context)
                                .textTheme
                                .titleSmall
                                ?.copyWith(fontWeight: FontWeight.w600),
                          ),
                        ),
                      ),
                    ),
                    for (final m in metrics)
                      _Cell(
                        cell: _lookup(attr, m),
                        width: cellWidth,
                        height: rowHeight,
                        severityColor: _severityColor(
                          _lookup(attr, m)?.severity ?? 'unavailable',
                          context,
                        ),
                        valueText: _formatValue(
                          _lookup(attr, m) ??
                              HeatmapCell(
                                attribute: attr,
                                metric: m,
                                value: null,
                                severity: 'unavailable',
                              ),
                        ),
                        onTap: onCellTap,
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Cell extends StatelessWidget {
  const _Cell({
    required this.cell,
    required this.width,
    required this.height,
    required this.severityColor,
    required this.valueText,
    this.onTap,
  });

  final HeatmapCell? cell;
  final double width;
  final double height;
  final Color severityColor;
  final String valueText;
  final void Function(HeatmapCell)? onTap;

  @override
  Widget build(BuildContext context) {
    final c = cell;
    return InkWell(
      onTap: c == null || onTap == null ? null : () => onTap!(c),
      child: Container(
        width: width,
        height: height,
        margin: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: severityColor.withValues(alpha: 0.85),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Center(
          child: Text(
            valueText,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
              fontSize: 16,
            ),
          ),
        ),
      ),
    );
  }
}
