import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/models/audit_models.dart';

final auditSessionProvider = ChangeNotifierProvider<AuditSession>((ref) {
  return AuditSession();
});

final auditSummariesProvider = FutureProvider<List<AuditSummary>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final rows = await api.listAudits();
  return rows
      .whereType<Map<Object?, Object?>>()
      .map((row) => AuditSummary.fromJson(Map<String, dynamic>.from(row)))
      .where((summary) => summary.id.isNotEmpty)
      .toList();
});

class AuditSession extends ChangeNotifier {
  Uint8List? _fileBytes;
  String? _fileName;
  String? _datasetId;
  SchemaDetection? _schema;
  AuditDetail? _audit;
  bool _busy = false;
  String? _error;

  String? get fileName => _fileName;
  String? get datasetId => _datasetId;
  SchemaDetection? get schema => _schema;
  AuditDetail? get audit => _audit;
  bool get busy => _busy;
  String? get error => _error;
  String? get currentAuditId => _audit?.id;

  bool get hasFile => _fileBytes != null && _fileName != null;
  bool get canUpload => hasFile && !_busy;
  bool get canAnalyze => _schema?.isReady == true && !_busy;

  String? get reportUrl {
    final id = currentAuditId;
    if (id == null) return null;
    return '$kApiBaseUrl/audits/$id/report';
  }

  Future<void> pickFile() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv', 'xlsx'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.first;
    _fileBytes = file.bytes;
    _fileName = file.name;
    _datasetId = null;
    _schema = null;
    _audit = null;
    _error = null;
    notifyListeners();
  }

  Future<void> uploadAndDetect(ApiClient api) async {
    final bytes = _fileBytes;
    final name = _fileName;
    if (bytes == null || name == null) return;
    await _run(() async {
      final upload = await api.uploadDataset(bytes: bytes, filename: name);
      _datasetId = upload['dataset_id'] as String?;
      if (_datasetId == null) {
        throw ApiException('Upload completed without a dataset id.');
      }
      _schema = SchemaDetection.fromJson(await api.detectSchema(_datasetId!));
    });
  }

  Future<String?> createAndAnalyze(ApiClient api) async {
    final schema = _schema;
    final datasetId = _datasetId;
    if (schema == null || datasetId == null || !schema.isReady) return null;
    String? auditId;
    await _run(() async {
      final created = await api.createAudit({
        'title': 'Audit - ${_fileName ?? 'uploaded dataset'}',
        'dataset_id': datasetId,
        'domain': 'hiring',
        'mode': 'audit',
        'provenance_kind': 'synthetic',
        'provenance_label': _fileName ?? 'Uploaded dataset',
        'sensitive_attributes':
            schema.sensitiveAttributes.map((attribute) => attribute.column).toList(),
        'outcome_column': schema.outcomeColumn!.column,
        'positive_value': schema.outcomeColumn!.positiveValue,
        'score_column': schema.scoreColumn,
        'feature_columns': schema.featureColumns,
        'identifier_columns': schema.identifierColumns,
      });
      auditId = created['audit_id'] as String?;
      if (auditId == null) {
        throw ApiException('Audit creation did not return an audit id.');
      }
      _audit = AuditDetail.fromJson(await api.analyzeAudit(auditId!));
    });
    return auditId;
  }

  Future<void> loadAudit(ApiClient api, String auditId) async {
    if (_audit?.id == auditId) return;
    await _run(() async {
      _audit = AuditDetail.fromJson(await api.getAudit(auditId));
    });
  }

  Future<void> applyReweighting(ApiClient api) async {
    final audit = _audit;
    if (audit == null || audit.sensitiveAttributes.isEmpty) return;
    await _run(() async {
      final target = audit.sensitiveAttributes.first;
      _audit = AuditDetail.fromJson(
        await api.remediateAudit(
          audit.id,
          targetAttribute: target,
          justification:
              'Apply Kamiran-Calders reweighting to address $target disparity.',
        ),
      );
    });
  }

  Future<void> signOff(ApiClient api, String notes) async {
    final audit = _audit;
    if (audit == null) return;
    await _run(() async {
      _audit = AuditDetail.fromJson(await api.signOffAudit(audit.id, notes: notes));
    });
  }

  Future<void> generateReport(ApiClient api) async {
    final audit = _audit;
    if (audit == null) return;
    await _run(() async {
      await api.generateReport(audit.id);
      _audit = AuditDetail.fromJson(await api.getAudit(audit.id));
    });
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> _run(Future<void> Function() task) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      await task();
    } catch (error) {
      _error = friendlyApiError(error);
    } finally {
      _busy = false;
      notifyListeners();
    }
  }
}

String friendlyApiError(Object error) {
  if (error is ApiException) {
    final status = error.status;
    if (status == 404) return 'That audit is not available in the local backend.';
    if (status == 502 || status == 503) {
      return 'The analysis service is temporarily unavailable. Retry after the backend settles.';
    }
    return error.message;
  }
  final message = error.toString();
  if (message.contains('XMLHttpRequest') || message.contains('SocketException')) {
    return 'The frontend cannot reach the API. Confirm the backend is running on port 8000.';
  }
  if (message.contains('TimeoutException') || message.contains('connection took longer')) {
    return 'The API request timed out. Retry once the backend has finished warming up.';
  }
  return 'Something went wrong while processing the audit.';
}
