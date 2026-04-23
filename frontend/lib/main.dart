// NyayaLens Flutter web client — entry point.
//
// See docs/system-design.md §12 for screen inventory (S01–S13) and
// docs/adr/0005 for the typed privacy payload contract that the API
// client must honour for every request that carries user data.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

import 'package:nyayalens_client/app/router.dart';
import 'package:nyayalens_client/app/theme.dart';

void main() {
  runApp(
    const ProviderScope(
      child: NyayaLensApp(),
    ),
  );
}

class NyayaLensApp extends ConsumerWidget {
  const NyayaLensApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'NyayaLens',
      debugShowCheckedModeBanner: false,
      theme: buildLightTheme(),
      darkTheme: buildDarkTheme(),
      themeMode: ThemeMode.system,
      routerConfig: router,
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(
          textTheme: GoogleFonts.interTextTheme(Theme.of(context).textTheme),
        ),
        child: child ?? const SizedBox.shrink(),
      ),
    );
  }
}
