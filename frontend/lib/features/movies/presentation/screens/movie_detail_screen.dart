import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class MovieDetailScreen extends StatelessWidget {
  const MovieDetailScreen({super.key, required this.movie});

  final Movie movie;

  @override
  Widget build(BuildContext context) {
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
      placeholder: (_, _) => Container(
        height: 280,
        color: Colors.grey.shade900,
      ),
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
