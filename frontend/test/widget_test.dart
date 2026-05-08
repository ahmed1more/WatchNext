import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:watch_next_frontend/app.dart';
import 'package:watch_next_frontend/features/home/presentation/screens/home_screen.dart';
import 'package:watch_next_frontend/features/movies/data/services/movie_api_service.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

void main() {
  testWidgets('renders the home shell', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          movieApiServiceProvider.overrideWithValue(_FakeMovieApiService()),
        ],
        child: const WatchNextApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(HomeScreen), findsOneWidget);
    expect(find.byIcon(Icons.person_search), findsOneWidget);
    expect(find.text('Start Rating'), findsOneWidget);
  });
}

class _FakeMovieApiService extends MovieApiService {
  @override
  Future<int> getNextUserId() async => 999;

  @override
  Future<List<Movie>> getRecommendations(int userId) async => [
    Movie(movieId: 1, title: 'Test Recommendation', genres: 'Drama'),
  ];

  @override
  Future<List<Movie>> getTrendingMovies() async => [
    Movie(movieId: 2, title: 'Trending Test Title', genres: 'Comedy'),
  ];
}
