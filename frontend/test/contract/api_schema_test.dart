// Contract tests — verify the JSON Schemas exported from the FastAPI
// backend still expose the field names the Flutter client reads.
//
// Schemas are produced by `backend/scripts/export_schemas.py` and live at
// `../shared/schemas/<ClassName>.json` (or downloaded as the `api-schemas`
// artifact in CI).
//
// We do NOT validate JSON Schema semantics here — the goal is drift
// detection: a renamed field or removed key on the backend fails CI before
// it reaches a deployed bundle.

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

const _schemaDir = '../shared/schemas';

Map<String, dynamic> _loadSchema(String className) {
  final file = File('$_schemaDir/$className.json');
  if (!file.existsSync()) {
    fail(
      'Missing schema file: ${file.path}\n'
      'Run `python scripts/export_schemas.py --out ../shared/schemas` from '
      'backend/ to regenerate.',
    );
  }
  return json.decode(file.readAsStringSync()) as Map<String, dynamic>;
}

Iterable<String> _propertyNames(Map<String, dynamic> schema) {
  final props = schema['properties'];
  if (props is! Map) return const [];
  return props.keys.cast<String>();
}

void main() {
  group('API contract', () {
    test('AuditDetailResponse exposes the keys demo_flow.dart reads', () {
      final schema = _loadSchema('AuditDetailResponse');
      final keys = _propertyNames(schema).toSet();
      expect(keys, containsAll(<String>{'audit_id', 'title', 'status', 'mode'}));
    });

    test('DatasetUploadResponse exposes dataset_id and preview', () {
      final schema = _loadSchema('DatasetUploadResponse');
      final keys = _propertyNames(schema).toSet();
      expect(keys, containsAll(<String>{'dataset_id', 'preview', 'provenance'}));
    });

    test('SchemaDetectionResponse exposes needs_review and dataset_id', () {
      final schema = _loadSchema('SchemaDetectionResponse');
      final keys = _propertyNames(schema).toSet();
      expect(keys, containsAll(<String>{'dataset_id', 'needs_review'}));
    });

    test('SignOffRequest enforces a non-trivial notes minimum length', () {
      final schema = _loadSchema('SignOffRequest');
      final notes = (schema['properties'] as Map)['notes'] as Map?;
      expect(notes, isNotNull);
      // Backend Pydantic Field(min_length=10) maps to JSON Schema minLength.
      expect(notes!['minLength'], greaterThanOrEqualTo(10));
    });
  });
}
