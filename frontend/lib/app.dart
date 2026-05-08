import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_next_frontend/core/theme/app_theme.dart';
import 'package:watch_next_frontend/features/home/presentation/screens/home_screen.dart';

class WatchNextRoot extends StatelessWidget {
  const WatchNextRoot({super.key});

  @override
  Widget build(BuildContext context) {
    return const ProviderScope(child: WatchNextApp());
  }
}

class WatchNextApp extends StatelessWidget {
  const WatchNextApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WatchNext AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      scrollBehavior: const _WatchNextScrollBehavior(),
      home: const HomeScreen(),
    );
  }
}

class _WatchNextScrollBehavior extends MaterialScrollBehavior {
  const _WatchNextScrollBehavior();

  @override
  Set<PointerDeviceKind> get dragDevices => {
    PointerDeviceKind.touch,
    PointerDeviceKind.mouse,
    PointerDeviceKind.stylus,
    PointerDeviceKind.invertedStylus,
    PointerDeviceKind.trackpad,
  };
}
