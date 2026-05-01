import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_next_frontend/features/movies/data/services/movie_api_service.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class CurrentUserNotifier extends Notifier<int> {
  @override
  int build() => 1;

  void updateUser(int id) {
    state = id;
  }
}

final currentUserProvider =
    NotifierProvider<CurrentUserNotifier, int>(CurrentUserNotifier.new);

final recommendationsProvider = FutureProvider.family<List<Movie>, int>((
  ref,
  userId,
) {
  final apiService = ref.read(movieApiServiceProvider);
  return apiService.getRecommendations(userId);
});

final similarMoviesProvider = FutureProvider.family<List<Movie>, int>((
  ref,
  movieId,
) {
  final apiService = ref.read(movieApiServiceProvider);
  return apiService.getSimilarMovies(movieId);
});
