class SchemaDetection {
  const SchemaDetection({
    required this.datasetId,
    required this.needsReview,
    required this.sensitiveAttributes,
    required this.outcomeColumn,
    required this.featureColumns,
    required this.identifierColumns,
    required this.scoreColumn,
  });

  factory SchemaDetection.fromJson(Map<String, dynamic> json) {
    return SchemaDetection(
      datasetId: _asString(json['dataset_id'], 'unknown-dataset'),
      needsReview: json['needs_review'] == true,
      sensitiveAttributes: _asMapList(json['sensitive_attributes'])
          .map(SensitiveAttribute.fromJson)
          .toList(),
      outcomeColumn: json['outcome_column'] == null
          ? null
          : OutcomeColumn.fromJson(_asMap(json['outcome_column'])),
      featureColumns: _asStringList(json['feature_columns']),
      identifierColumns: _asStringList(json['identifier_columns']),
      scoreColumn: _nullableString(json['score_column']),
    );
  }

  final String datasetId;
  final bool needsReview;
  final List<SensitiveAttribute> sensitiveAttributes;
  final OutcomeColumn? outcomeColumn;
  final List<String> featureColumns;
  final List<String> identifierColumns;
  final String? scoreColumn;

  bool get isReady =>
      sensitiveAttributes.isNotEmpty && outcomeColumn?.column.isNotEmpty == true;
}

class SensitiveAttribute {
  const SensitiveAttribute({
    required this.column,
    required this.category,
    required this.confidence,
    required this.rationale,
  });

  factory SensitiveAttribute.fromJson(Map<String, dynamic> json) {
    return SensitiveAttribute(
      column: _asString(json['column'], 'unknown'),
      category: _asString(json['category'], 'sensitive'),
      confidence: _asDouble(json['confidence']) ?? 0,
      rationale: _asString(json['rationale'], 'Review recommended.'),
    );
  }

  final String column;
  final String category;
  final double confidence;
  final String rationale;
}

class OutcomeColumn {
  const OutcomeColumn({
    required this.column,
    required this.positiveValue,
    required this.confidence,
  });

  factory OutcomeColumn.fromJson(Map<String, dynamic> json) {
    return OutcomeColumn(
      column: _asString(json['column'], 'unknown'),
      positiveValue: _asObject(json['positive_value'], 1),
      confidence: _asDouble(json['confidence']) ?? 0,
    );
  }

  final String column;
  final Object positiveValue;
  final double confidence;
}

class AuditSummary {
  const AuditSummary({
    required this.id,
    required this.title,
    required this.status,
    required this.mode,
    required this.domain,
    required this.provenanceKind,
    required this.provenanceLabel,
  });

  factory AuditSummary.fromJson(Map<String, dynamic> json) {
    return AuditSummary(
      id: _asString(json['audit_id'], ''),
      title: _asString(json['title'], 'Untitled audit'),
      status: _asString(json['status'], 'draft'),
      mode: _asString(json['mode'], 'audit'),
      domain: _asString(json['domain'], 'hiring'),
      provenanceKind: _asString(json['provenance_kind'], 'synthetic'),
      provenanceLabel: _asString(json['provenance_label'], 'Uploaded dataset'),
    );
  }

  final String id;
  final String title;
  final String status;
  final String mode;
  final String domain;
  final String provenanceKind;
  final String provenanceLabel;
}

class AuditDetail {
  const AuditDetail({
    required this.summary,
    required this.sensitiveAttributes,
    required this.outcomeColumn,
    required this.metrics,
    required this.heatmapCells,
    required this.explanations,
    required this.conflicts,
    required this.proxies,
    required this.remediation,
    required this.signOff,
    required this.tradeoff,
    required this.hasReport,
  });

  factory AuditDetail.fromJson(Map<String, dynamic> json) {
    return AuditDetail(
      summary: AuditSummary.fromJson(_asMap(json['summary'])),
      sensitiveAttributes: _asStringList(json['sensitive_attributes']),
      outcomeColumn: _nullableString(json['outcome_column']),
      metrics: _asMapList(json['metrics']).map(AuditMetric.fromJson).toList(),
      heatmapCells:
          _asMapList(json['heatmap_cells']).map(AuditHeatmapCell.fromJson).toList(),
      explanations:
          _asMapList(json['explanations']).map(AuditExplanation.fromJson).toList(),
      conflicts: _asMapList(json['conflicts']).map(AuditConflict.fromJson).toList(),
      proxies: _asMapList(json['proxies']).map(ProxyFlag.fromJson).toList(),
      remediation: json['remediation'] == null
          ? null
          : RemediationResult.fromJson(_asMap(json['remediation'])),
      signOff:
          json['sign_off'] == null ? null : SignOff.fromJson(_asMap(json['sign_off'])),
      tradeoff: json['tradeoff'] == null
          ? null
          : Tradeoff.fromJson(_asMap(json['tradeoff'])),
      hasReport: json['has_report'] == true,
    );
  }

  final AuditSummary summary;
  final List<String> sensitiveAttributes;
  final String? outcomeColumn;
  final List<AuditMetric> metrics;
  final List<AuditHeatmapCell> heatmapCells;
  final List<AuditExplanation> explanations;
  final List<AuditConflict> conflicts;
  final List<ProxyFlag> proxies;
  final RemediationResult? remediation;
  final SignOff? signOff;
  final Tradeoff? tradeoff;
  final bool hasReport;

  String get id => summary.id;
  String get title => summary.title;
  String get status => summary.status;

  int get criticalCount =>
      heatmapCells.where((cell) => cell.severity == 'critical').length;

  int get warningCount =>
      heatmapCells.where((cell) => cell.severity == 'warning').length;

  int get unavailableCount =>
      heatmapCells.where((cell) => cell.severity == 'unavailable').length;

  List<String> get metricNames {
    final names = <String>[];
    for (final cell in heatmapCells) {
      if (!names.contains(cell.metric)) names.add(cell.metric);
    }
    if (names.isNotEmpty) return names;
    return metrics.map((metric) => metric.name).where((name) => name.isNotEmpty).toList();
  }
}

class AuditMetric {
  const AuditMetric({
    required this.name,
    required this.value,
    required this.label,
  });

  factory AuditMetric.fromJson(Map<String, dynamic> json) {
    return AuditMetric(
      name: _asString(json['metric'], _asString(json['name'], 'metric')),
      value: _asDouble(json['value']),
      label: _asString(json['label'], ''),
    );
  }

  final String name;
  final double? value;
  final String label;
}

class AuditHeatmapCell {
  const AuditHeatmapCell({
    required this.attribute,
    required this.metric,
    required this.value,
    required this.severity,
    required this.note,
  });

  factory AuditHeatmapCell.fromJson(Map<String, dynamic> json) {
    return AuditHeatmapCell(
      attribute: _asString(json['attribute'], 'unknown'),
      metric: _asString(json['metric'], 'metric'),
      value: _asDouble(json['value']),
      severity: _asString(json['severity'], 'unavailable'),
      note: _asString(json['note'], ''),
    );
  }

  final String attribute;
  final String metric;
  final double? value;
  final String severity;
  final String note;
}

class AuditExplanation {
  const AuditExplanation({
    required this.metric,
    required this.attribute,
    required this.summary,
    required this.interpretation,
    required this.grounded,
  });

  factory AuditExplanation.fromJson(Map<String, dynamic> json) {
    return AuditExplanation(
      metric: _asString(json['metric'], 'metric'),
      attribute: _asString(json['attribute'], 'attribute'),
      summary: _asString(json['summary'], ''),
      interpretation: _asString(json['interpretation'], ''),
      grounded: json['grounded'] == true,
    );
  }

  final String metric;
  final String attribute;
  final String summary;
  final String interpretation;
  final bool grounded;
}

class AuditConflict {
  const AuditConflict({
    required this.metricA,
    required this.metricB,
    required this.description,
  });

  factory AuditConflict.fromJson(Map<String, dynamic> json) {
    return AuditConflict(
      metricA: _asString(json['metric_a'], 'metric A'),
      metricB: _asString(json['metric_b'], 'metric B'),
      description: _asString(json['description'], ''),
    );
  }

  final String metricA;
  final String metricB;
  final String description;
}

class ProxyFlag {
  const ProxyFlag({
    required this.feature,
    required this.sensitiveAttribute,
    required this.method,
    required this.strength,
    required this.severity,
  });

  factory ProxyFlag.fromJson(Map<String, dynamic> json) {
    return ProxyFlag(
      feature: _asString(json['feature'], 'feature'),
      sensitiveAttribute: _asString(json['sensitive_attribute'], 'attribute'),
      method: _asString(json['method'], 'correlation'),
      strength: _asDouble(json['strength']) ?? 0,
      severity: _asString(json['severity'], 'warning'),
    );
  }

  final String feature;
  final String sensitiveAttribute;
  final String method;
  final double strength;
  final String severity;
}

class RemediationResult {
  const RemediationResult({
    required this.dirBefore,
    required this.dirAfter,
    required this.spdBefore,
    required this.spdAfter,
    required this.accuracyEstimateDelta,
  });

  factory RemediationResult.fromJson(Map<String, dynamic> json) {
    return RemediationResult(
      dirBefore: _asDouble(json['dir_before']),
      dirAfter: _asDouble(json['dir_after']),
      spdBefore: _asDouble(json['spd_before']),
      spdAfter: _asDouble(json['spd_after']),
      accuracyEstimateDelta: _asDouble(json['accuracy_estimate_delta']) ?? 0,
    );
  }

  final double? dirBefore;
  final double? dirAfter;
  final double? spdBefore;
  final double? spdAfter;
  final double accuracyEstimateDelta;
}

class Tradeoff {
  const Tradeoff({
    required this.metricChosen,
    required this.justification,
    required this.conflictsAcknowledged,
    required this.selectedByUid,
    required this.selectedByName,
    required this.selectedAt,
  });

  factory Tradeoff.fromJson(Map<String, dynamic> json) {
    return Tradeoff(
      metricChosen: _asString(json['metric_chosen'], 'metric'),
      justification: _asString(json['justification'], ''),
      conflictsAcknowledged: _asStringList(json['conflicts_acknowledged']),
      selectedByUid: _asString(json['selected_by_uid'], ''),
      selectedByName: _asString(json['selected_by_name'], 'Reviewer'),
      selectedAt: _asString(json['selected_at'], ''),
    );
  }

  final String metricChosen;
  final String justification;
  final List<String> conflictsAcknowledged;
  final String selectedByUid;
  final String selectedByName;
  final String selectedAt;
}

class DataQuality {
  const DataQuality({
    required this.rowCount,
    required this.columnCount,
    required this.missingCellPct,
    required this.duplicateRowPct,
    required this.typeConsistencyPct,
    required this.overallScore,
    required this.warnings,
  });

  factory DataQuality.fromJson(Map<String, dynamic> json) {
    return DataQuality(
      rowCount: (_asDouble(json['row_count']) ?? 0).toInt(),
      columnCount: (_asDouble(json['column_count']) ?? 0).toInt(),
      missingCellPct: _asDouble(json['missing_cell_pct']) ?? 0,
      duplicateRowPct: _asDouble(json['duplicate_row_pct']) ?? 0,
      typeConsistencyPct: _asDouble(json['type_consistency_pct']) ?? 1,
      overallScore: _asDouble(json['overall_score']) ?? 0,
      warnings: _asStringList(json['warnings']),
    );
  }

  final int rowCount;
  final int columnCount;
  final double missingCellPct;
  final double duplicateRowPct;
  final double typeConsistencyPct;
  final double overallScore;
  final List<String> warnings;

  bool get hasWarnings => warnings.isNotEmpty;
}

class SignOff {
  const SignOff({
    required this.reviewerName,
    required this.reviewerRole,
    required this.signedAt,
    required this.notes,
  });

  factory SignOff.fromJson(Map<String, dynamic> json) {
    return SignOff(
      reviewerName: _asString(json['reviewer_name'], 'Reviewer'),
      reviewerRole: _asString(json['reviewer_role'], 'reviewer'),
      signedAt: _asString(json['signed_at'], ''),
      notes: _asString(json['notes'], ''),
    );
  }

  final String reviewerName;
  final String reviewerRole;
  final String signedAt;
  final String notes;
}

String displayStatus(String status) {
  return status.replaceAll('_', ' ').toUpperCase();
}

String formatScore(double? value, {int digits = 2}) {
  if (value == null) return 'n/a';
  return value.toStringAsFixed(digits);
}

Map<String, dynamic> _asMap(Object? value) {
  if (value is Map<Object?, Object?>) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

List<Map<String, dynamic>> _asMapList(Object? value) {
  if (value is! List<Object?>) return const [];
  return value
      .whereType<Map<Object?, Object?>>()
      .map((entry) => Map<String, dynamic>.from(entry))
      .toList();
}

List<String> _asStringList(Object? value) {
  if (value is! List<Object?>) return const [];
  return value
      .map((entry) => entry?.toString().trim() ?? '')
      .where((entry) => entry.isNotEmpty)
      .toList();
}

String _asString(Object? value, String fallback) {
  final text = value?.toString().trim();
  if (text == null || text.isEmpty) return fallback;
  return text;
}

String? _nullableString(Object? value) {
  final text = value?.toString().trim();
  if (text == null || text.isEmpty) return null;
  return text;
}

double? _asDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '');
}

Object _asObject(Object? value, Object fallback) {
  return value ?? fallback;
}
