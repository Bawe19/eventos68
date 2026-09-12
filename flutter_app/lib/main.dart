import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(const Eventos68App());
}

class Eventos68App extends StatelessWidget {
  const Eventos68App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Eventos68',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFB45309),
          primary: const Color(0xFFB45309),
          secondary: const Color(0xFF0F172A),
          surface: Colors.white,
          background: const Color(0xFFF8FAFC),
        ),
        appBarTheme: const AppBarTheme(
          elevation: 0,
          centerTitle: false,
          backgroundColor: Color(0xFF0F172A),
          foregroundColor: Colors.white,
        ),
      ),
      home: const DashboardScreen(),
    );
  }
}
