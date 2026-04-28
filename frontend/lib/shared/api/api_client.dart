// NyayaLens API client — talks to the FastAPI backend.
//
// Uses plain Dart Maps instead of Freezed for MVP velocity. The shapes
// mirror `backend/nyayalens/api/routes.py` 1:1.

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Default API base URL. Override at build time with
/// `--dart-define=API_BASE=https://nyayalens-api...run.app/api/v1`.
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE',
  defaultValue: 'http://localhost:8000/api/v1',
);

/// Demo identity headers — replaced by real Firebase ID-token verification
/// in production. Override at build time with:
///   --dart-define=X_USER_ID=...
///   --dart-define=X_USER_NAME=...
///   --dart-define=X_USER_ROLE=...
///   --dart-define=X_ORGANIZATION_ID=...
/// Pass empty strings to omit a header entirely (so a production bundle
/// does not advertise a baked-in 'admin' role).
const String _demoUserId = String.fromEnvironment('X_USER_ID', defaultValue: 'demo-uid');
const String _demoUserName =
    String.fromEnvironment('X_USER_NAME', defaultValue: 'Demo Reviewer');
const String _demoUserRole = String.fromEnvironment('X_USER_ROLE', defaultValue: 'admin');
const String _demoOrgId =
    String.fromEnvironment('X_ORGANIZATION_ID', defaultValue: 'demo-org');

Map<String, String> _buildDemoHeaders() {
  final headers = <String, String>{};
  if (_demoUserId.isNotEmpty) headers['X-User-Id'] = _demoUserId;
  if (_demoUserName.isNotEmpty) headers['X-User-Name'] = _demoUserName;
  if (_demoUserRole.isNotEmpty) headers['X-User-Role'] = _demoUserRole;
  if (_demoOrgId.isNotEmpty) headers['X-Organization-Id'] = _demoOrgId;
  return headers;
}

final Map<String, String> kDemoUserHeaders = _buildDemoHeaders();

class ApiException implements Exception {
  ApiException(this.message, [this.status]);
  final String message;
  final int? status;

  @override
  String toString() => 'ApiException($status): $message';
}

class ApiClient {
  ApiClient({String? baseUrl, Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: baseUrl ?? kApiBaseUrl,
                connectTimeout: const Duration(minutes: 2),
                receiveTimeout: const Duration(minutes: 4),
                sendTimeout: const Duration(minutes: 2),
                headers: {
                  ...kDemoUserHeaders,
                  'Accept': 'application/json',
                },
                responseType: ResponseType.json,
              ),
            );

  final Dio _dio;

  // ---- Datasets -----------------------------------------------------

  Future<Map<String, dynamic>> uploadDataset({
    required Uint8List bytes,
    required String filename,
    String domain = 'hiring',
  }) async {
    final form = FormData.fromMap({
      'domain': domain,
      'file': MultipartFile.fromBytes(bytes, filename: filename),
    });
    return _post('/datasets/upload', data: form);
  }

  Future<Map<String, dynamic>> detectSchema(String datasetId) =>
      _post('/datasets/$datasetId/detect-schema');

  // ---- Audits -------------------------------------------------------

  Future<Map<String, dynamic>> createAudit(Map<String, dynamic> body) =>
      _post('/audits', data: body);

  Future<List<Object?>> listAudits() async {
    final r = await _dio.get('/audits');
    return _jsonList(r.data);
  }

  Future<Map<String, dynamic>> getAudit(String auditId) =>
      _get('/audits/$auditId');

  Future<Map<String, dynamic>> analyzeAudit(String auditId) =>
      _post('/audits/$auditId/analyze');

  Future<Map<String, dynamic>> remediateAudit(
    String auditId, {
    required String targetAttribute,
    required String justification,
  }) =>
      _post(
        '/audits/$auditId/remediate',
        data: {
          'target_attribute': targetAttribute,
          'justification': justification,
        },
      );

  Future<Map<String, dynamic>> signOffAudit(
    String auditId, {
    required String notes,
  }) =>
      _post(
        '/audits/$auditId/sign-off',
        data: {'notes': notes, 'confirmed': true},
      );

  Future<Map<String, dynamic>> tradeoffAudit(
    String auditId, {
    required String metricChosen,
    required String justification,
    required List<String> conflictsAcknowledged,
  }) =>
      _post(
        '/audits/$auditId/tradeoff',
        data: {
          'metric_chosen': metricChosen,
          'justification': justification,
          'conflicts_acknowledged': conflictsAcknowledged,
        },
      );

  // ---- Reports ------------------------------------------------------

  Future<Map<String, dynamic>> generateReport(String auditId) =>
      _post('/audits/$auditId/report/generate');

  Future<Uint8List> fetchReport(String auditId) async {
    final r = await _dio.get<List<int>>(
      '/audits/$auditId/report',
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(r.data ?? const []);
  }

  // ---- Probes -------------------------------------------------------

  Future<Map<String, dynamic>> jdScan({
    required String jobTitle,
    required String jobDescription,
  }) =>
      _post(
        '/probes/job-description',
        data: {'job_title': jobTitle, 'job_description': jobDescription},
      );

  Future<Map<String, dynamic>> perturbationProbe(Map<String, dynamic> body) =>
      _post('/probes/perturbation', data: body);

  // ---- Recourse + audit trail ---------------------------------------

  Future<Map<String, dynamic>> recourseSummary(
    String auditId,
    Map<String, dynamic> body,
  ) =>
      _post('/audits/$auditId/recourse-summary', data: body);

  Future<List<Object?>> auditTrail() async {
    final r = await _dio.get('/audit-trail');
    return _jsonList(r.data);
  }

  // ---- Internals ----------------------------------------------------

  Future<Map<String, dynamic>> _get(String path) async {
    try {
      final r = await _dio.get(path);
      return _jsonMap(r.data);
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  Future<Map<String, dynamic>> _post(String path, {Object? data}) async {
    try {
      final r = await _dio.post(path, data: data);
      return _jsonMap(r.data);
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  ApiException _toApiException(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;
    final detail = data is Map<Object?, Object?>
        ? data['detail']?.toString() ?? e.message
        : e.message;
    return ApiException(detail ?? 'Network error', status);
  }

  Map<String, dynamic> _jsonMap(Object? data) {
    if (data is Map<Object?, Object?>) return Map<String, dynamic>.from(data);
    throw ApiException('Unexpected API response shape');
  }

  List<Object?> _jsonList(Object? data) {
    if (data is List<Object?>) return data;
    throw ApiException('Unexpected API response shape');
  }
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
