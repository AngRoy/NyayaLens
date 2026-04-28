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
  DataQuality? _quality;
  AuditDetail? _audit;
  bool _busy = false;
  String? _busyLabel;
  String? _error;

  String? get fileName => _fileName;
  String? get datasetId => _datasetId;
  SchemaDetection? get schema => _schema;
  DataQuality? get quality => _quality;
  AuditDetail? get audit => _audit;
  bool get busy => _busy;
  String? get busyLabel => _busyLabel;
  String? get error => _error;
  String? get currentAuditId => _audit?.id;

  bool get hasFile => _fileBytes != null && _fileName != null;
  bool get hasProgress =>
      hasFile || _datasetId != null || _schema != null || _audit != null;
  bool get canUpload => hasFile && !_busy;
  bool get canAnalyze => _schema?.isReady == true && !_busy;

  String? get reportUrl {
    final id = currentAuditId;
    if (id == null) return null;
    return '$kApiBaseUrl/audits/$id/report';
  }

  Future<void> pickFile() async {
    final picked = await FilePicker.pickFiles(
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
    _quality = null;
    _audit = null;
    _error = null;
    notifyListeners();
  }

  Future<void> uploadAndDetect(ApiClient api) async {
    final bytes = _fileBytes;
    final name = _fileName;
    if (bytes == null || name == null) return;
    await _run('Uploading dataset and detecting schema', () async {
      final upload = await api.uploadDataset(bytes: bytes, filename: name);
      _datasetId = upload['dataset_id'] as String?;
      if (_datasetId == null) {
        throw ApiException('Upload completed without a dataset id.');
      }
      final qualityJson = upload['quality'];
      _quality = qualityJson is Map<Object?, Object?>
          ? DataQuality.fromJson(Map<String, dynamic>.from(qualityJson))
          : null;
      _schema = SchemaDetection.fromJson(await api.detectSchema(_datasetId!));
    });
  }

  Future<String?> createAndAnalyze(ApiClient api) async {
    final schema = _schema;
    final datasetId = _datasetId;
    if (schema == null || datasetId == null || !schema.isReady) return null;
    String? auditId;
    await _run('Creating audit and running analysis', () async {
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
    await _run('Loading audit workspace', () async {
      _audit = AuditDetail.fromJson(await api.getAudit(auditId));
    });
  }

  Future<void> applyReweighting(ApiClient api) async {
    final audit = _audit;
    if (audit == null || audit.sensitiveAttributes.isEmpty) return;
    await _run('Applying reweighting mitigation', () async {
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
    await _run('Recording reviewer sign-off', () async {
      _audit = AuditDetail.fromJson(await api.signOffAudit(audit.id, notes: notes));
    });
  }

  Future<void> applyTradeoff(
    ApiClient api, {
    required String metricChosen,
    required String justification,
    required List<String> conflictsAcknowledged,
  }) async {
    final audit = _audit;
    if (audit == null) return;
    await _run('Recording metric tradeoff', () async {
      _audit = AuditDetail.fromJson(
        await api.tradeoffAudit(
          audit.id,
          metricChosen: metricChosen,
          justification: justification,
          conflictsAcknowledged: conflictsAcknowledged,
        ),
      );
    });
  }

  Future<void> generateReport(ApiClient api) async {
    final audit = _audit;
    if (audit == null) return;
    await _run('Generating audit report', () async {
      await api.generateReport(audit.id);
      _audit = AuditDetail.fromJson(await api.getAudit(audit.id));
    });
  }

  void reset() {
    _fileBytes = null;
    _fileName = null;
    _datasetId = null;
    _schema = null;
    _quality = null;
    _audit = null;
    _busy = false;
    _busyLabel = null;
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> _run(String busyLabel, Future<void> Function() task) async {
    _busy = true;
    _busyLabel = busyLabel;
    _error = null;
    notifyListeners();
    try {
      await task();
    } catch (error) {
      _error = friendlyApiError(error);
    } finally {
      _busy = false;
      _busyLabel = null;
      notifyListeners();
    }
  }
}

String friendlyApiError(Object error) {
  if (error is ApiException) {
    final status = error.status;
    if (status == 404) return 'That audit is not available in the local backend.';
    if (status == 409 && error.message.toLowerCase().contains('probe')) {
      return 'This audit is in probe mode. Lifecycle actions like analyze, '
          'remediate, sign-off, and report are reserved for full audit mode.';
    }
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
