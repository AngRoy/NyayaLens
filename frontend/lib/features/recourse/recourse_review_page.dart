import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:nyayalens_client/features/audits/audit_session.dart';
import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/models/audit_models.dart';
import 'package:nyayalens_client/shared/widgets/app_shell.dart';
import 'package:nyayalens_client/shared/widgets/nyaya_surface.dart';

final recourseRequestsProvider = FutureProvider.autoDispose<List<RecourseRequest>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final rows = await api.listRecourseRequests();
  return rows
      .whereType<Map<Object?, Object?>>()
      .map((row) => RecourseRequest.fromJson(Map<String, dynamic>.from(row)))
      .toList();
});

class RecourseReviewPage extends ConsumerWidget {
  const RecourseReviewPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncRequests = ref.watch(recourseRequestsProvider);
    return NyayaAppShell(
      title: 'Recourse review',
      subtitle: 'Applicant review requests filed against your audits.',
      selectedRoute: '/recourse',
      children: [
        asyncRequests.when(
          data: (requests) => requests.isEmpty
              ? const EmptyStatePanel(
                  icon: Icons.inbox_outlined,
                  title: 'No recourse requests',
                  message: 'No applicant has filed a recourse request yet.',
                )
              : _RecourseList(requests: requests),
          loading: () => const SurfacePanel(
            child: SizedBox(
              height: 96,
              child: Center(child: CircularProgressIndicator()),
            ),
          ),
          error: (error, _) => EmptyStatePanel(
            icon: Icons.error_outline,
            title: 'Could not load recourse requests',
            message: friendlyApiError(error),
            action: FilledButton.icon(
              onPressed: () => ref.invalidate(recourseRequestsProvider),
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ),
        ),
      ],
    );
  }
}

class _RecourseList extends StatelessWidget {
  const _RecourseList({required this.requests});

  final List<RecourseRequest> requests;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final request in requests) ...[
          _RecourseCard(request: request),
          const SizedBox(height: 12),
        ],
      ],
    );
  }
}

class _RecourseCard extends ConsumerWidget {
  const _RecourseCard({required this.request});

  final RecourseRequest request;

  BadgeTone get _statusTone {
    return switch (request.status) {
      'pending' => BadgeTone.warning,
      'in_review' => BadgeTone.info,
      'resolved_upheld' => BadgeTone.neutral,
      'resolved_overturned' => BadgeTone.good,
      'resolved_referred' => BadgeTone.info,
      _ => BadgeTone.neutral,
    };
  }

  String get _statusLabel {
    return switch (request.status) {
      'pending' => 'Pending',
      'in_review' => 'In review',
      'resolved_upheld' => 'Upheld',
      'resolved_overturned' => 'Overturned',
      'resolved_referred' => 'Referred',
      _ => request.status,
    };
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: request.applicantIdentifier,
            subtitle: 'Audit ${request.auditId} · ${request.requestType.replaceAll('_', ' ')}',
            trailing: StatusBadge(
              label: _statusLabel,
              tone: _statusTone,
              icon: Icons.flag_outlined,
            ),
          ),
          const SizedBox(height: 12),
          Text(request.body),
          if (request.reviewerNotes.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Reviewer notes: ${request.reviewerNotes}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            'Filed ${request.createdAt}'
            '${request.assignedToName == null ? '' : ' · assigned to ${request.assignedToName}'}'
            '${request.resolvedAt == null ? '' : ' · resolved ${request.resolvedAt}'}',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          if (request.isOpen) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: () => _openAssignDialog(context, ref),
                  icon: const Icon(Icons.assignment_ind_outlined),
                  label: const Text('Assign'),
                ),
                FilledButton.icon(
                  onPressed: () => _openResolveDialog(context, ref),
                  icon: const Icon(Icons.gavel_outlined),
                  label: const Text('Resolve'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _openAssignDialog(BuildContext context, WidgetRef ref) async {
    final uidController = TextEditingController();
    final nameController = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Assign reviewer'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: uidController,
              decoration: const InputDecoration(labelText: 'Reviewer UID'),
            ),
            TextField(
              controller: nameController,
              decoration: const InputDecoration(labelText: 'Reviewer name'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Assign')),
        ],
      ),
    );
    if (result == true) {
      try {
        await ref.read(apiClientProvider).assignRecourse(
              request.requestId,
              assigneeUid: uidController.text.trim(),
              assigneeName: nameController.text.trim(),
            );
        ref.invalidate(recourseRequestsProvider);
      } catch (error) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(friendlyApiError(error))),
          );
        }
      }
    }
  }

  Future<void> _openResolveDialog(BuildContext context, WidgetRef ref) async {
    String resolution = 'resolved_upheld';
    final notesController = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Text('Resolve recourse'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                initialValue: resolution,
                items: const [
                  DropdownMenuItem(value: 'resolved_upheld', child: Text('Upheld')),
                  DropdownMenuItem(value: 'resolved_overturned', child: Text('Overturned')),
                  DropdownMenuItem(value: 'resolved_referred', child: Text('Referred')),
                ],
                onChanged: (value) => setState(() => resolution = value ?? resolution),
                decoration: const InputDecoration(labelText: 'Resolution'),
              ),
              TextField(
                controller: notesController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Reviewer notes (10 char minimum)',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Resolve')),
          ],
        ),
      ),
    );
    if (result == true) {
      try {
        await ref.read(apiClientProvider).resolveRecourse(
              request.requestId,
              resolution: resolution,
              reviewerNotes: notesController.text.trim(),
            );
        ref.invalidate(recourseRequestsProvider);
      } catch (error) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(friendlyApiError(error))),
          );
        }
      }
    }
  }
}
