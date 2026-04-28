import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:nyayalens_client/shared/api/api_client.dart';
import 'package:nyayalens_client/shared/widgets/nyaya_surface.dart';

class NyayaAppShell extends StatelessWidget {
  const NyayaAppShell({
    super.key,
    required this.title,
    required this.selectedRoute,
    required this.children,
    this.subtitle,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final String selectedRoute;
  final Widget? trailing;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 920;
        final page = NyayaGridBackdrop(
          child: SafeArea(
            child: CustomScrollView(
              slivers: [
                SliverPadding(
                  padding: EdgeInsets.fromLTRB(
                    compact ? 18 : 28,
                    compact ? 18 : 24,
                    compact ? 18 : 32,
                    18,
                  ),
                  sliver: SliverToBoxAdapter(
                    child: _PageHeader(
                      title: title,
                      subtitle: subtitle,
                      trailing: trailing,
                    ),
                  ),
                ),
                SliverPadding(
                  padding: EdgeInsets.fromLTRB(
                    compact ? 18 : 28,
                    0,
                    compact ? 18 : 32,
                    36,
                  ),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        if (index.isOdd) return const SizedBox(height: 18);
                        return children[index ~/ 2];
                      },
                      childCount:
                          children.isEmpty ? 0 : children.length * 2 - 1,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );

        return Scaffold(
          appBar: compact
              ? AppBar(
                  title: const Text('NyayaLens'),
                  actions: [
                    IconButton(
                      tooltip: 'New audit',
                      onPressed: () => context.go('/audits/new'),
                      icon: const Icon(Icons.add_circle_outline),
                    ),
                  ],
                )
              : null,
          drawer: compact
              ? Drawer(
                  child: SafeArea(
                    child: _AppNavigation(
                      selectedRoute: selectedRoute,
                      compact: true,
                    ),
                  ),
                )
              : null,
          body: Row(
            children: [
              if (!compact)
                _AppNavigation(
                  selectedRoute: selectedRoute,
                  compact: false,
                ),
              Expanded(child: page),
            ],
          ),
        );
      },
    );
  }
}

class _PageHeader extends StatelessWidget {
  const _PageHeader({
    required this.title,
    this.subtitle,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 16,
      runSpacing: 12,
      children: [
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 6),
                Text(
                  subtitle!,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
              ],
            ],
          ),
        ),
        if (trailing != null) trailing!,
      ],
    );
  }
}

class _AppNavigation extends StatelessWidget {
  const _AppNavigation({
    required this.selectedRoute,
    required this.compact,
  });

  final String selectedRoute;
  final bool compact;

  static const items = [
    _NavigationItem(
      label: 'Dashboard',
      route: '/',
      icon: Icons.space_dashboard_outlined,
      selectedIcon: Icons.space_dashboard,
    ),
    _NavigationItem(
      label: 'New audit',
      route: '/audits/new',
      icon: Icons.upload_file_outlined,
      selectedIcon: Icons.upload_file,
    ),
    _NavigationItem(
      label: 'Audits',
      route: '/audits',
      icon: Icons.analytics_outlined,
      selectedIcon: Icons.analytics,
    ),
    _NavigationItem(
      label: 'Settings',
      route: '/settings',
      icon: Icons.tune_outlined,
      selectedIcon: Icons.tune,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: compact ? null : 260,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLowest,
        border: Border(
          right: BorderSide(
            color: compact ? Colors.transparent : scheme.outlineVariant,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 18),
            child: Row(
              children: [
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: scheme.primary,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const SizedBox(
                    width: 38,
                    height: 38,
                    child: Icon(
                      Icons.balance,
                      size: 22,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'NyayaLens',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w900,
                            ),
                      ),
                      Text(
                        'Fairness audit console',
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: scheme.onSurfaceVariant,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(12),
              children: [
                for (final item in items)
                  _NavigationTile(
                    item: item,
                    selected: _isSelected(item.route),
                    onTap: () {
                      if (compact) Navigator.of(context).pop();
                      context.go(item.route);
                    },
                  ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: StatusBadge(
              label: 'API ${Uri.parse(kApiBaseUrl).host}',
              tone: BadgeTone.info,
              icon: Icons.cloud_queue,
            ),
          ),
        ],
      ),
    );
  }

  bool _isSelected(String route) {
    if (route == '/') return selectedRoute == '/';
    if (route == '/audits/new') return selectedRoute == '/audits/new';
    if (route == '/audits') {
      return selectedRoute == '/audits' ||
          (selectedRoute.startsWith('/audits/') &&
              !selectedRoute.startsWith('/audits/new'));
    }
    return selectedRoute == route || selectedRoute.startsWith('$route/');
  }
}

class _NavigationTile extends StatelessWidget {
  const _NavigationTile({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  final _NavigationItem item;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Material(
        color: selected
            ? scheme.secondaryContainer.withValues(alpha: 0.72)
            : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            child: Row(
              children: [
                Icon(
                  selected ? item.selectedIcon : item.icon,
                  color: selected
                      ? scheme.onSecondaryContainer
                      : scheme.onSurfaceVariant,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    item.label,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: selected
                              ? scheme.onSecondaryContainer
                              : scheme.onSurface,
                          fontWeight:
                              selected ? FontWeight.w800 : FontWeight.w600,
                        ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavigationItem {
  const _NavigationItem({
    required this.label,
    required this.route,
    required this.icon,
    required this.selectedIcon,
  });

  final String label;
  final String route;
  final IconData icon;
  final IconData selectedIcon;
}
