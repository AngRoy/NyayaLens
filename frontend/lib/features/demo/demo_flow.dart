// Single-page audit-lifecycle flow (S03→S09 consolidated).
//
// Step 1: Upload CSV
// Step 2: Confirm Gemini-detected schema
// Step 3: View heatmap, metrics, explanations, conflicts, proxies
// Step 4: Apply reweighting + see before/after DIR
// Step 5: Sign off with documented justification
// Step 6: Generate + download PDF audit report

import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/platform/url_opener.dart';
import 'package:nyayalens_client/shared/widgets/bias_heatmap.dart';

class DemoFlowScreen extends ConsumerStatefulWidget {
  const DemoFlowScreen({super.key});

  @override
  ConsumerState<DemoFlowScreen> createState() => _DemoFlowScreenState();
}

class _DemoFlowScreenState extends ConsumerState<DemoFlowScreen> {
  Uint8List? _fileBytes;
  String? _fileName;
  String? _datasetId;
  Map<String, dynamic>? _schema;
  String? _auditId;
  Map<String, dynamic>? _audit;
  bool _busy = false;
  String? _error;

  Future<void> _withBusy(Future<void> Function() task) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await task();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickFile() async {
    final picked = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv', 'xlsx'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return;
    final f = picked.files.first;
    setState(() {
      _fileBytes = f.bytes;
      _fileName = f.name;
    });
  }

  Future<void> _uploadAndDetect() async {
    final api = ref.read(apiClientProvider);
    if (_fileBytes == null || _fileName == null) return;
    await _withBusy(() async {
      final upload = await api.uploadDataset(
        bytes: _fileBytes!,
        filename: _fileName!,
      );
      _datasetId = upload['dataset_id'] as String;
      _schema = await api.detectSchema(_datasetId!);
    });
  }

  Future<void> _createAndAnalyze() async {
    final api = ref.read(apiClientProvider);
    if (_datasetId == null || _schema == null) return;
    await _withBusy(() async {
      final sens = (_schema!['sensitive_attributes'] as List)
          .map((e) => (e as Map)['column'] as String)
          .toList();
      final outcome =
          (_schema!['outcome_column'] as Map?)?['column'] as String?;
      if (outcome == null || sens.isEmpty) {
        throw ApiException('Schema review needs sensitive attrs + outcome');
      }
      final created = await api.createAudit({
        'title': 'Audit — ${_fileName ?? 'demo'}',
        'dataset_id': _datasetId,
        'domain': 'hiring',
        'mode': 'audit',
        'provenance_kind': 'synthetic',
        'provenance_label': _fileName ?? 'Uploaded dataset',
        'sensitive_attributes': sens,
        'outcome_column': outcome,
        'positive_value':
            (_schema!['outcome_column'] as Map?)?['positive_value'] ?? 1,
        'score_column': _schema!['score_column'],
        'feature_columns':
            (_schema!['feature_columns'] as List?)?.cast<String>() ?? [],
        'identifier_columns':
            (_schema!['identifier_columns'] as List?)?.cast<String>() ?? [],
      });
      _auditId = created['audit_id'] as String;
      _audit = await api.analyzeAudit(_auditId!);
    });
  }

  Future<void> _applyReweighting() async {
    final api = ref.read(apiClientProvider);
    if (_auditId == null || _audit == null) return;
    await _withBusy(() async {
      final attr = (_audit!['sensitive_attributes'] as List).first as String;
      _audit = await api.remediateAudit(
        _auditId!,
        targetAttribute: attr,
        justification:
            'Apply Kamiran-Calders reweighting to address $attr disparity (demo).',
      );
    });
  }

  Future<void> _signOff(String notes) async {
    final api = ref.read(apiClientProvider);
    if (_auditId == null) return;
    await _withBusy(() async {
      _audit = await api.signOffAudit(_auditId!, notes: notes);
    });
  }

  Future<void> _generateReport() async {
    final api = ref.read(apiClientProvider);
    if (_auditId == null) return;
    await _withBusy(() async {
      await api.generateReport(_auditId!);
      _audit = await api.getAudit(_auditId!);
    });
  }

  String? get _reportUrl {
    final id = _auditId;
    if (id == null) return null;
    return '$kApiBaseUrl/audits/$id/report';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('NyayaLens — Audit Flow'),
        actions: [
          if (_audit != null) _ProvenanceBadge(audit: _audit!),
          const SizedBox(width: 12),
        ],
      ),
      body: Stack(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ListView(
              children: [
                _StepCard(
                  step: 1,
                  title: 'Upload dataset',
                  child: _Step1Upload(
                    onPick: _pickFile,
                    onUpload: _uploadAndDetect,
                    fileName: _fileName,
                    schema: _schema,
                  ),
                ),
                if (_schema != null)
                  _StepCard(
                    step: 2,
                    title: 'Confirm Gemini-detected schema',
                    child: _Step2Schema(
                      schema: _schema!,
                      onAnalyze: _createAndAnalyze,
                      analyzed: _audit != null,
                    ),
                  ),
                if (_audit != null)
                  _StepCard(
                    step: 3,
                    title: 'Bias heatmap & metrics',
                    child: _Step3Dashboard(audit: _audit!),
                  ),
                if (_audit != null)
                  _StepCard(
                    step: 4,
                    title: 'Apply reweighting · before / after',
                    child: _Step4Remediation(
                      audit: _audit!,
                      onApply: _applyReweighting,
                    ),
                  ),
                if (_audit != null)
                  _StepCard(
                    step: 5,
                    title: 'Sign off',
                    child: _Step5SignOff(
                      audit: _audit!,
                      onSign: _signOff,
                    ),
                  ),
                if (_audit != null &&
                    (_audit!['summary']['status'] == 'signed_off'))
                  _StepCard(
                    step: 6,
                    title: 'Generate audit report',
                    child: _Step6Report(
                      audit: _audit!,
                      onGenerate: _generateReport,
                      reportUrl: _reportUrl,
                    ),
                  ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      _error!,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error),
                    ),
                  ),
              ],
            ),
          ),
          if (_busy)
            Container(
              color: Colors.black26,
              child: const Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }
}

// ----- Step cards ---------------------------------------------------

class _StepCard extends StatelessWidget {
  const _StepCard({
    required this.step,
    required this.title,
    required this.child,
  });

  final int step;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 14,
                  child: Text(
                    '$step',
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _ProvenanceBadge extends StatelessWidget {
  const _ProvenanceBadge({required this.audit});
  final Map<String, dynamic> audit;

  @override
  Widget build(BuildContext context) {
    final kind = audit['summary']['provenance_kind'] as String? ?? 'unknown';
    final label = audit['summary']['provenance_label'] as String? ?? '';
    Color colour;
    switch (kind) {
      case 'real':
        colour = const Color(0xFF2E7D32);
        break;
      case 'benchmark':
        colour = const Color(0xFF1565C0);
        break;
      case 'synthetic':
        colour = const Color(0xFFF9A825);
        break;
      case 'llm_generated':
        colour = const Color(0xFF6A1B9A);
        break;
      default:
        colour = Colors.grey;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: colour,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        '${kind.toUpperCase()} · $label',
        style: const TextStyle(color: Colors.white, fontSize: 11),
      ),
    );
  }
}

// ----- Step 1: Upload -----------------------------------------------

class _Step1Upload extends StatelessWidget {
  const _Step1Upload({
    required this.onPick,
    required this.onUpload,
    required this.fileName,
    required this.schema,
  });

  final VoidCallback onPick;
  final VoidCallback onUpload;
  final String? fileName;
  final Map<String, dynamic>? schema;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Choose a CSV/XLSX file (≤100MB).'),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          children: [
            FilledButton.icon(
              onPressed: onPick,
              icon: const Icon(Icons.upload_file),
              label: Text(fileName ?? 'Choose file'),
            ),
            FilledButton.tonal(
              onPressed: fileName == null ? null : onUpload,
              child: const Text('Upload + detect schema'),
            ),
          ],
        ),
        if (schema != null) ...[
          const SizedBox(height: 8),
          Text(
            'Schema detected — review below.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ],
    );
  }
}

// ----- Step 2: Schema review ---------------------------------------

class _Step2Schema extends StatelessWidget {
  const _Step2Schema({
    required this.schema,
    required this.onAnalyze,
    required this.analyzed,
  });

  final Map<String, dynamic> schema;
  final VoidCallback onAnalyze;
  final bool analyzed;

  @override
  Widget build(BuildContext context) {
    final sens = (schema['sensitive_attributes'] as List).cast<Map>();
    final outcome = schema['outcome_column'] as Map?;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Sensitive attributes:',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        ...sens.map(
          (s) => ListTile(
            dense: true,
            leading: const Icon(Icons.bolt, size: 20),
            title: Text('${s['column']} — ${s['category']}'),
            subtitle: Text(
              'confidence: ${(s['confidence'] as num).toStringAsFixed(2)} · '
              '${s['rationale']}',
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Outcome: ${outcome?['column']} '
          '(positive = ${outcome?['positive_value']})',
        ),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: analyzed ? null : onAnalyze,
          child: const Text('Confirm & run analysis'),
        ),
      ],
    );
  }
}

// ----- Step 3: Dashboard --------------------------------------------

class _Step3Dashboard extends StatelessWidget {
  const _Step3Dashboard({required this.audit});

  final Map<String, dynamic> audit;

  @override
  Widget build(BuildContext context) {
    final attrs = (audit['sensitive_attributes'] as List).cast<String>();
    final cells = (audit['heatmap_cells'] as List).cast<Map>();
    final metrics = <String>[];
    for (final c in cells) {
      final m = c['metric'] as String;
      if (!metrics.contains(m)) metrics.add(m);
    }
    final mapped = cells
        .map(
          (c) => HeatmapCell(
            attribute: c['attribute'] as String,
            metric: c['metric'] as String,
            value: (c['value'] as num?)?.toDouble(),
            severity: c['severity'] as String,
            note: c['note'] as String? ?? '',
          ),
        )
        .toList();

    final explanations = (audit['explanations'] as List).cast<Map>();
    final conflicts = (audit['conflicts'] as List).cast<Map>();
    final proxies = (audit['proxies'] as List).cast<Map>();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        BiasHeatmap(
          attributes: attrs,
          metrics: metrics,
          cells: mapped,
        ),
        const SizedBox(height: 16),
        if (explanations.isNotEmpty) ...[
          Text(
            'Gemini explanation',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 4),
          ...explanations.map(
            (e) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${e['metric']} · ${e['attribute']}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Text(e['summary'] as String? ?? ''),
                  Text(
                    e['interpretation'] as String? ?? '',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (e['grounded'] != true)
                    Text(
                      '(template fallback — Gemini grounding failed)',
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                        fontSize: 12,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
        if (conflicts.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(
            'Metric conflicts',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          ...conflicts.map(
            (c) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Text(
                '${c['metric_a']} vs ${c['metric_b']}: ${c['description']}',
              ),
            ),
          ),
        ],
        if (proxies.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(
            'Proxy features',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          ...proxies.map(
            (p) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Text(
                '${p['feature']} → ${p['sensitive_attribute']} '
                '(${p['method']}, ${(p['strength'] as num).toStringAsFixed(2)}, '
                '${p['severity']})',
              ),
            ),
          ),
        ],
      ],
    );
  }
}

// ----- Step 4: Remediation (before/after) ---------------------------

class _Step4Remediation extends StatelessWidget {
  const _Step4Remediation({required this.audit, required this.onApply});

  final Map<String, dynamic> audit;
  final VoidCallback onApply;

  @override
  Widget build(BuildContext context) {
    final rem = audit['remediation'] as Map<String, dynamic>?;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (rem == null)
          FilledButton.icon(
            onPressed: onApply,
            icon: const Icon(Icons.tune),
            label: const Text('Apply reweighting'),
          )
        else
          _BeforeAfter(remediation: rem),
      ],
    );
  }
}

class _BeforeAfter extends StatelessWidget {
  const _BeforeAfter({required this.remediation});
  final Map<String, dynamic> remediation;

  @override
  Widget build(BuildContext context) {
    // DIR is `null` on the wire when the privileged-group rate is zero
    // (ratio undefined). Render as "n/a" rather than "0.00".
    final double? dirBefore = (remediation['dir_before'] as num?)?.toDouble();
    final double? dirAfter = (remediation['dir_after'] as num?)?.toDouble();
    final double accDelta =
        (remediation['accuracy_estimate_delta'] as num?)?.toDouble() ?? 0;
    return Row(
      children: [
        Expanded(
          child: _MetricBox(
            label: 'DIR before',
            value: dirBefore,
            colour: const Color(0xFFC62828),
          ),
        ),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 8),
          child: Icon(Icons.arrow_forward),
        ),
        Expanded(
          child: _MetricBox(
            label: 'DIR after',
            value: dirAfter,
            colour: const Color(0xFF2E7D32),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _MetricBox(
            label: 'Accuracy Δ (est.)',
            value: accDelta,
            colour: const Color(0xFF1565C0),
            formatter: (v) => '${v.toStringAsFixed(3)} pp',
          ),
        ),
      ],
    );
  }
}

class _MetricBox extends StatelessWidget {
  const _MetricBox({
    required this.label,
    required this.value,
    required this.colour,
    this.formatter,
  });

  final String label;
  final double? value;
  final Color colour;
  final String Function(double)? formatter;

  @override
  Widget build(BuildContext context) {
    final v = value;
    final display = v == null
        ? 'n/a'
        : (formatter ?? (x) => x.toStringAsFixed(2))(v);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colour.withValues(alpha: 0.08),
        border: Border.all(color: colour.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 6),
          Text(
            display,
            style: Theme.of(context)
                .textTheme
                .headlineSmall
                ?.copyWith(color: colour, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

// ----- Step 5: Sign off --------------------------------------------

class _Step5SignOff extends StatefulWidget {
  const _Step5SignOff({required this.audit, required this.onSign});

  final Map<String, dynamic> audit;
  final Future<void> Function(String) onSign;

  @override
  State<_Step5SignOff> createState() => _Step5SignOffState();
}

class _Step5SignOffState extends State<_Step5SignOff> {
  final _ctl = TextEditingController(
    text:
        'Reviewed disparity. Accepting reweighting tradeoff to bring DIR within reference threshold.',
  );
  bool _confirmed = false;

  @override
  Widget build(BuildContext context) {
    final signedOff = widget.audit['sign_off'] as Map?;
    if (signedOff != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.verified, color: Color(0xFF2E7D32)),
          const SizedBox(height: 4),
          Text(
            'Signed off by ${signedOff['reviewer_name']} '
            '(${signedOff['reviewer_role']}) at ${signedOff['signed_at']}',
          ),
          Text(
            'Notes: ${signedOff['notes']}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _ctl,
          maxLines: 3,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            labelText: 'Justification (≥10 chars)',
          ),
        ),
        CheckboxListTile(
          value: _confirmed,
          onChanged: (v) => setState(() => _confirmed = v ?? false),
          title: const Text(
            'I confirm I reviewed these findings and accept this tradeoff.',
          ),
        ),
        FilledButton(
          onPressed: _confirmed && _ctl.text.length >= 10
              ? () => widget.onSign(_ctl.text)
              : null,
          child: const Text('Sign off'),
        ),
      ],
    );
  }
}

// ----- Step 6: Report ----------------------------------------------

class _Step6Report extends StatelessWidget {
  const _Step6Report({
    required this.audit,
    required this.onGenerate,
    required this.reportUrl,
  });

  final Map<String, dynamic> audit;
  final VoidCallback onGenerate;
  final String? reportUrl;

  @override
  Widget build(BuildContext context) {
    final hasReport = audit['has_report'] == true;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!hasReport)
          FilledButton.icon(
            onPressed: onGenerate,
            icon: const Icon(Icons.picture_as_pdf),
            label: const Text('Generate audit report (PDF)'),
          )
        else
          Wrap(
            spacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              FilledButton.icon(
                onPressed: reportUrl == null
                    ? null
                    : () => openExternalUrl(reportUrl!),
                icon: const Icon(Icons.open_in_new),
                label: const Text('Open audit report PDF'),
              ),
              if (reportUrl != null)
                Text(
                  reportUrl!,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
            ],
          ),
      ],
    );
  }
}
