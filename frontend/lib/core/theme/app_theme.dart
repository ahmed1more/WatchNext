import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const Color background = Colors.black;
  static const Color surface = Color(0xFF121212);
  static const Color primary = Color(0xFFE50914);
  static const Color accent = Colors.white;
  static const Color textPrimary = Colors.white;
  static const Color textSecondary = Colors.grey;

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: primary,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: primary,
        surface: surface,
      ),
      textTheme: GoogleFonts.montserratTextTheme(
        ThemeData.dark().textTheme,
      ).copyWith(
        displayLarge: GoogleFonts.bebasNeue(
          fontSize: 60,
          fontWeight: FontWeight.bold,
          color: textPrimary,
          letterSpacing: 1.2,
        ),
        headlineMedium: GoogleFonts.montserrat(
          fontSize: 24,
          fontWeight: FontWeight.bold,
          color: textPrimary,
        ),
        bodyLarge: GoogleFonts.montserrat(
          fontSize: 16,
          color: textPrimary,
        ),
        bodyMedium: GoogleFonts.montserrat(
          fontSize: 14,
          color: textSecondary,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
      ),
    );
  }
}
