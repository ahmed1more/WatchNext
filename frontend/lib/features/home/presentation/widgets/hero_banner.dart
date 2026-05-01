import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class HeroBanner extends StatelessWidget {
  const HeroBanner({super.key, this.movie, this.onMoreInfo});

  final Movie? movie;
  final VoidCallback? onMoreInfo;

  @override
  Widget build(BuildContext context) {
    final featuredMovie = movie;
    if (featuredMovie == null) {
      return const SizedBox(height: 600);
    }

    return Stack(
      children: [
        Container(
          height: 700,
          width: double.infinity,
          foregroundDecoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Colors.black,
                Colors.transparent,
                Colors.transparent,
                Colors.black,
              ],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              stops: [0, 0.2, 0.7, 1],
            ),
          ),
          child: featuredMovie.backdropUrl != null
              ? CachedNetworkImage(
                  imageUrl: featuredMovie.backdropUrl!,
                  fit: BoxFit.cover,
                )
              : Container(color: Colors.grey[900]),
        ),
        Positioned(
          bottom: 100,
          left: 60,
          right: 60,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                featuredMovie.title,
                style: Theme.of(context).textTheme.displayLarge,
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: 600,
                child: Text(
                  featuredMovie.overview?.trim().isNotEmpty == true
                      ? featuredMovie.overview!
                      : 'No description available.',
                  style: Theme.of(context).textTheme.bodyLarge,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(height: 30),
              Row(
                children: [
                  _buildButton(
                    icon: Icons.play_arrow,
                    label: 'Play',
                    color: Colors.white,
                    textColor: Colors.black,
                  ),
                  const SizedBox(width: 15),
                  GestureDetector(
                    onTap: onMoreInfo,
                    child: _buildButton(
                      icon: Icons.info_outline,
                      label: 'More Info',
                      color: Colors.grey.withValues(alpha: 0.5),
                      textColor: Colors.white,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildButton({
    required IconData icon,
    required String label,
    required Color color,
    required Color textColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 12),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          Icon(icon, color: textColor),
          const SizedBox(width: 10),
          Text(
            label,
            style: TextStyle(
              color: textColor,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
        ],
      ),
    );
  }
}
