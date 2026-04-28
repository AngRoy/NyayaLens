// RED reproducer for the data-quality chip on upload.
//
// `DataQuality` is the wire shape returned by `POST /datasets/upload`'s
// `quality` field. `DataQualityChip` is the small panel rendered under
// the upload step so reviewers see how trustworthy the dataset is
// before they commit to running fairness analysis on it.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:nyayalens_client/shared/models/audit_models.dart';
import 'package:nyayalens_client/shared/widgets/data_quality_chip.dart';

void main() {
  test('DataQuality.fromJson parses backend payload', () {
    final quality = DataQuality.fromJson({
      'row_count': 100,
      'column_count': 5,
      'missing_cell_pct': 0.05,
      'duplicate_row_pct': 0.0,
      'type_consistency_pct': 0.95,
      'overall_score': 0.65,
      'warnings': ['Small dataset (n=100); fairness statistics may be unstable.'],
    });

    expect(quality.rowCount, 100);
    expect(quality.columnCount, 5);
    expect(quality.overallScore, closeTo(0.65, 1e-9));
    expect(quality.missingCellPct, closeTo(0.05, 1e-9));
    expect(quality.warnings, contains('Small dataset (n=100); fairness statistics may be unstable.'));
  });

  test('DataQuality.fromJson tolerates missing optional fields', () {
    final quality = DataQuality.fromJson({});

    expect(quality.rowCount, 0);
    expect(quality.overallScore, 0.0);
    expect(quality.warnings, isEmpty);
  });

  testWidgets('DataQualityChip renders score, row count, and warnings', (tester) async {
    const quality = DataQuality(
      rowCount: 100,
      columnCount: 5,
      missingCellPct: 0.05,
      duplicateRowPct: 0.0,
      typeConsistencyPct: 0.95,
      overallScore: 0.65,
      warnings: ['Small dataset (n=100); fairness statistics may be unstable.'],
    );

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: DataQualityChip(quality: quality)),
      ),
    );

    expect(find.text('Data quality'), findsOneWidget);
    expect(find.textContaining('0.65'), findsOneWidget);
    expect(find.textContaining('100'), findsWidgets);
    expect(find.textContaining('Small dataset'), findsOneWidget);
  });

  testWidgets('DataQualityChip omits warning list when there are none', (tester) async {
    const quality = DataQuality(
      rowCount: 5000,
      columnCount: 12,
      missingCellPct: 0.0,
      duplicateRowPct: 0.0,
      typeConsistencyPct: 1.0,
      overallScore: 1.0,
      warnings: [],
    );

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: DataQualityChip(quality: quality)),
      ),
    );

    expect(find.text('Data quality'), findsOneWidget);
    expect(find.textContaining('No warnings'), findsOneWidget);
  });
}
