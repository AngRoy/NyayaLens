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
/// in production.
const Map<String, String> kDemoUserHeaders = {
  'X-User-Id': 'demo-uid',
  'X-User-Name': 'Demo Reviewer',
  'X-User-Role': 'admin',
  'X-Organization-Id': 'demo-org',
};

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

  Future<List<dynamic>> listAudits() async {
    final r = await _dio.get('/audits');
    return r.data as List<dynamic>;
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

  Future<List<dynamic>> auditTrail() async {
    final r = await _dio.get('/audit-trail');
    return r.data as List<dynamic>;
  }

  // ---- Internals ----------------------------------------------------

  Future<Map<String, dynamic>> _get(String path) async {
    try {
      final r = await _dio.get(path);
      return Map<String, dynamic>.from(r.data as Map);
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  Future<Map<String, dynamic>> _post(String path, {Object? data}) async {
    try {
      final r = await _dio.post(path, data: data);
      return Map<String, dynamic>.from(r.data as Map);
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  ApiException _toApiException(DioException e) {
    final status = e.response?.statusCode;
    final detail = e.response?.data is Map
        ? (e.response!.data as Map)['detail']?.toString() ?? e.message
        : e.message;
    return ApiException(detail ?? 'Network error', status);
  }
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
