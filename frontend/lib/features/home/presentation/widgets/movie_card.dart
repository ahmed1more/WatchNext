import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class MovieCard extends StatefulWidget {
  const MovieCard({super.key, required this.movie, required this.onTap});

  final Movie movie;
  final VoidCallback onTap;

  @override
  State<MovieCard> createState() => _MovieCardState();
}

class _MovieCardState extends State<MovieCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeInOut,
          margin: const EdgeInsets.symmetric(horizontal: 4),
          transform: _isHovered
              ? (Matrix4.identity()..scale(1.1, 1.1, 1.0))
              : Matrix4.identity(),
          width: 160,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            boxShadow: _isHovered
                ? [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.5),
                      blurRadius: 10,
                      spreadRadius: 2,
                    ),
                  ]
                : [],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: widget.movie.posterUrl != null
                ? CachedNetworkImage(
                    imageUrl: widget.movie.posterUrl!,
                    fit: BoxFit.cover,
                    placeholder: (context, url) => _buildPlaceholder(),
                    errorWidget: (context, url, error) => _buildErrorWidget(),
                  )
                : _buildErrorWidget(),
          ),
        ),
      ),
    );
  }

  Widget _buildPlaceholder() {
    return Shimmer.fromColors(
      baseColor: Colors.grey[900]!,
      highlightColor: Colors.grey[800]!,
      child: Container(color: Colors.black),
    );
  }

  Widget _buildErrorWidget() {
    return Container(
      color: Colors.grey[900],
      child: Center(
        child: Text(
          widget.movie.title,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 12, color: Colors.white),
        ),
      ),
    );
  }
}
