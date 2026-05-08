import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/movie_row.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';
import 'package:watch_next_frontend/features/movies/providers/movie_providers.dart';

class MovieDetailScreen extends ConsumerWidget {
  const MovieDetailScreen({super.key, required this.movie});

  final Movie movie;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final similarMovies = ref.watch(similarMoviesProvider(movie.movieId));

    return Scaffold(
      appBar: AppBar(title: Text(movie.title)),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _MovieDetailHeader(movie: movie),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    movie.title,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    movie.overview?.trim().isNotEmpty == true
                        ? movie.overview!
                        : 'No overview available for this movie yet.',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              ),
            ),
            similarMovies.when(
              data: (movies) => movies.isEmpty
                  ? const SizedBox.shrink()
                  : MovieRow(
                      title: 'More Like This',
                      movies: movies,
                      onMovieTap: (selectedMovie) {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) =>
                                MovieDetailScreen(movie: selectedMovie),
                          ),
                        );
                      },
                    ),
              loading: () => const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, stackTrace) => Padding(
                padding: const EdgeInsets.all(24),
                child: Text('Unable to load similar titles: $error'),
              ),
            ),
            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }
}

class _MovieDetailHeader extends StatelessWidget {
  const _MovieDetailHeader({required this.movie});

  final Movie movie;

  @override
  Widget build(BuildContext context) {
    final imageUrl = movie.backdropUrl ?? movie.posterUrl;
    if (imageUrl == null) {
      return _MovieDetailFallback(title: movie.title);
    }

    return CachedNetworkImage(
      imageUrl: imageUrl,
      width: double.infinity,
      height: 280,
      fit: BoxFit.cover,
      placeholder: (_, _) =>
          Container(height: 280, color: Colors.grey.shade900),
      errorWidget: (_, _, _) => _MovieDetailFallback(title: movie.title),
    );
  }
}

class _MovieDetailFallback extends StatelessWidget {
  const _MovieDetailFallback({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 280,
      color: Colors.grey.shade900,
      alignment: Alignment.center,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Text(
        title,
        style: const TextStyle(color: Colors.white, fontSize: 24),
        textAlign: TextAlign.center,
      ),
    );
  }
}
