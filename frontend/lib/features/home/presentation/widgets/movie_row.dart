import 'package:flutter/material.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/movie_card.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class MovieRow extends StatelessWidget {
  const MovieRow({
    super.key,
    required this.title,
    required this.movies,
    required this.onMovieTap,
  });

  final String title;
  final List<Movie> movies;
  final ValueChanged<Movie> onMovieTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 12),
          child: Text(
            title,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
        ),
        SizedBox(
          height: 240,
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 36),
            scrollDirection: Axis.horizontal,
            itemCount: movies.length,
            itemBuilder: (context, index) {
              return MovieCard(
                movie: movies[index],
                onTap: () => onMovieTap(movies[index]),
              );
            },
          ),
        ),
      ],
    );
  }
}
