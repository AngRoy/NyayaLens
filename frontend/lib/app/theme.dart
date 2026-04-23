// NyayaLens theme — Material 3 with a justice-leaning palette.
//
// Primary: deep slate (reflective, institutional).
// Secondary: saffron accent (nod to the Nyaya Chakra).
// Semantic provenance colors match the badge colours documented in
// the design doc §12.2:
//   - real data      : green
//   - benchmark      : blue
//   - synthetic      : amber
//   - llm-generated  : purple

import 'package:flutter/material.dart';

const Color _nyayaSlate = Color(0xFF1E2A44);
const Color _nyayaSaffron = Color(0xFFF5A623);

ThemeData buildLightTheme() => ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: _nyayaSlate,
        brightness: Brightness.light,
        secondary: _nyayaSaffron,
      ),
      visualDensity: VisualDensity.adaptivePlatformDensity,
    );

ThemeData buildDarkTheme() => ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: _nyayaSlate,
        brightness: Brightness.dark,
        secondary: _nyayaSaffron,
      ),
      visualDensity: VisualDensity.adaptivePlatformDensity,
    );

/// Colours for the data-provenance badge in the top bar (S05 and elsewhere).
class ProvenanceColors {
  const ProvenanceColors._();

  static const Color realData = Color(0xFF2E7D32);     // green
  static const Color benchmark = Color(0xFF1565C0);    // blue
  static const Color synthetic = Color(0xFFF9A825);    // amber
  static const Color llmGenerated = Color(0xFF6A1B9A); // purple
}
