import 'package:flutter/material.dart';

import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/widgets/app_shell.dart';
import 'package:nyayalens_client/shared/widgets/nyaya_surface.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return NyayaAppShell(
      title: 'Workspace settings',
      subtitle: 'Local configuration used by the web client during development.',
      selectedRoute: '/settings',
      children: const [
        _RuntimePanel(),
        _GovernancePanel(),
      ],
    );
  }
}

class _RuntimePanel extends StatelessWidget {
  const _RuntimePanel();

  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Runtime',
            subtitle: 'Build-time API and demo identity values.',
          ),
          const SizedBox(height: 18),
          _SettingRow(
            icon: Icons.cloud_queue,
            label: 'API base',
            value: kApiBaseUrl,
          ),
          const Divider(),
          _SettingRow(
            icon: Icons.person_outline,
            label: 'Demo reviewer',
            value: kDemoUserHeaders['X-User-Name'] ?? 'Not sent',
          ),
          const Divider(),
          _SettingRow(
            icon: Icons.security_outlined,
            label: 'Role',
            value: kDemoUserHeaders['X-User-Role'] ?? 'Not sent',
          ),
        ],
      ),
    );
  }
}

class _GovernancePanel extends StatelessWidget {
  const _GovernancePanel();

  @override
  Widget build(BuildContext context) {
    return SurfacePanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Governance defaults',
            subtitle:
                'NyayaLens keeps raw data away from the LLM path and records reviewer actions.',
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: const [
              StatusBadge(
                label: 'Human sign-off required',
                tone: BadgeTone.info,
                icon: Icons.verified_user_outlined,
              ),
              StatusBadge(
                label: 'Report after approval',
                tone: BadgeTone.good,
                icon: Icons.picture_as_pdf_outlined,
              ),
              StatusBadge(
                label: 'PII-safe LLM payloads',
                tone: BadgeTone.warning,
                icon: Icons.privacy_tip_outlined,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SettingRow extends StatelessWidget {
  const _SettingRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Icon(icon, color: Theme.of(context).colorScheme.secondary),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.titleSmall,
            ),
          ),
          Flexible(
            child: Text(
              value,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.end,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
