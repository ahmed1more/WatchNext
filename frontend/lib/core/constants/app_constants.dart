import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConstants {
  static const String backendBaseUrl = 'http://127.0.0.1:8000';
  static const String tmdbBaseUrl = 'https://api.themoviedb.org/3';
  static const String tmdbImageBaseUrl = 'https://image.tmdb.org/t/p/w500';
  static const String tmdbBackdropBaseUrl =
      'https://image.tmdb.org/t/p/original';

  static String get tmdbApiKey => dotenv.env['TMDB_API_KEY'] ?? '';
}
