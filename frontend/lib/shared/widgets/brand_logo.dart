import 'package:flutter/material.dart';

import 'package:nyayalens_client/app/theme.dart';

class NyayaBrandMark extends StatelessWidget {
  const NyayaBrandMark({
    super.key,
    this.size = 38,
  });

  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: size,
      child: CustomPaint(
        painter: _NyayaBrandPainter(
          ink: NyayaColors.ink,
          teal: NyayaColors.teal,
          amber: NyayaColors.amber,
          surface: Theme.of(context).colorScheme.surfaceContainerLowest,
        ),
      ),
    );
  }
}

class NyayaBrandLockup extends StatelessWidget {
  const NyayaBrandLockup({
    super.key,
    this.subtitle,
  });

  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const NyayaBrandMark(),
        const SizedBox(width: 12),
        Flexible(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'NyayaLens',
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
              ),
              if (subtitle != null)
                Text(
                  subtitle!,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _NyayaBrandPainter extends CustomPainter {
  const _NyayaBrandPainter({
    required this.ink,
    required this.teal,
    required this.amber,
    required this.surface,
  });

  final Color ink;
  final Color teal;
  final Color amber;
  final Color surface;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final radius = size.shortestSide * 0.22;
    final background = Paint()..color = ink;
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, Radius.circular(radius)),
      background,
    );

    final grid = Paint()
      ..color = Colors.white.withValues(alpha: 0.10)
      ..strokeWidth = size.shortestSide * 0.014;
    final spacing = size.width / 4;
    for (var index = 1; index < 4; index += 1) {
      final offset = spacing * index;
      canvas.drawLine(Offset(offset, 0), Offset(offset, size.height), grid);
      canvas.drawLine(Offset(0, offset), Offset(size.width, offset), grid);
    }

    final center = Offset(size.width * 0.50, size.height * 0.50);
    final ringRadius = size.shortestSide * 0.25;
    final ring = Paint()
      ..color = teal
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = size.shortestSide * 0.075;
    canvas.drawCircle(center, ringRadius, ring);

    final beam = Paint()
      ..color = amber
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = size.shortestSide * 0.065;
    canvas.drawLine(
      Offset(center.dx, size.height * 0.20),
      Offset(center.dx, size.height * 0.80),
      beam,
    );
    canvas.drawLine(
      Offset(size.width * 0.28, size.height * 0.36),
      Offset(size.width * 0.72, size.height * 0.36),
      beam,
    );

    final lensFill = Paint()..color = surface.withValues(alpha: 0.92);
    canvas.drawCircle(center, ringRadius * 0.42, lensFill);
  }

  @override
  bool shouldRepaint(covariant _NyayaBrandPainter oldDelegate) {
    return oldDelegate.ink != ink ||
        oldDelegate.teal != teal ||
        oldDelegate.amber != amber ||
        oldDelegate.surface != surface;
  }
}
