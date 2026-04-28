import 'package:flutter/material.dart';

const Color _ink = Color(0xFF18212F);
const Color _teal = Color(0xFF167A7F);
const Color _amber = Color(0xFFE5A23A);
const Color _coral = Color(0xFFD96657);
const Color _green = Color(0xFF2E7D5B);

ThemeData buildLightTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: _teal,
    brightness: Brightness.light,
    primary: _ink,
    secondary: _teal,
    tertiary: _amber,
    error: _coral,
    surface: const Color(0xFFF7F8FA),
  );
  return _buildTheme(scheme);
}

ThemeData buildDarkTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: _teal,
    brightness: Brightness.dark,
    primary: const Color(0xFFD9E5EA),
    secondary: const Color(0xFF67C5C6),
    tertiary: const Color(0xFFF2C36F),
    error: const Color(0xFFFF9B8F),
    surface: const Color(0xFF10151D),
  );
  return _buildTheme(scheme);
}

ThemeData _buildTheme(ColorScheme scheme) {
  final border = BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.7));
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: scheme.surface,
    visualDensity: VisualDensity.adaptivePlatformDensity,
    appBarTheme: AppBarTheme(
      elevation: 0,
      centerTitle: false,
      backgroundColor: scheme.surface,
      foregroundColor: scheme.onSurface,
      surfaceTintColor: Colors.transparent,
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      margin: EdgeInsets.zero,
      color: scheme.surfaceContainerLowest,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: border,
      ),
    ),
    dividerTheme: DividerThemeData(
      color: scheme.outlineVariant.withValues(alpha: 0.8),
      thickness: 1,
      space: 1,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 44)),
        padding: const WidgetStatePropertyAll(
          EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        ),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        textStyle: const WidgetStatePropertyAll(
          TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 44)),
        padding: const WidgetStatePropertyAll(
          EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        ),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        side: WidgetStateProperty.resolveWith(
          (states) => BorderSide(
            color: states.contains(WidgetState.disabled)
                ? scheme.outlineVariant
                : scheme.outline,
          ),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: scheme.surfaceContainerLowest,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: border,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: border,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: scheme.secondary, width: 1.4),
      ),
    ),
    chipTheme: ChipThemeData(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      side: border,
    ),
  );
}

class NyayaColors {
  const NyayaColors._();

  static const Color ink = _ink;
  static const Color teal = _teal;
  static const Color amber = _amber;
  static const Color coral = _coral;
  static const Color green = _green;
}

class ProvenanceColors {
  const ProvenanceColors._();

  static const Color realData = _green;
  static const Color benchmark = _teal;
  static const Color synthetic = _amber;
  static const Color llmGenerated = Color(0xFF7A5BA6);
}
