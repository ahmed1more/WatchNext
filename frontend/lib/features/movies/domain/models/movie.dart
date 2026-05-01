class Movie {
  final int movieId;
  final String title;
  final int? tmdbId;
  final String? posterUrl;
  final String? backdropUrl;
  final String? overview;

  Movie({
    required this.movieId,
    required this.title,
    this.tmdbId,
    this.posterUrl,
    this.backdropUrl,
    this.overview,
  });

  factory Movie.fromJson(Map<String, dynamic> json) {
    return Movie(
      movieId: (json['movieId'] as num).toInt(),
      title: json['title'] as String,
      tmdbId: json['tmdbId'] != null ? (json['tmdbId'] as num).toInt() : null,
      posterUrl: json['posterUrl'] as String?,
      backdropUrl: json['backdropUrl'] as String?,
      overview: json['overview'] as String?,
    );
  }

  Movie copyWith({
    String? posterUrl,
    String? backdropUrl,
    String? overview,
  }) {
    return Movie(
      movieId: movieId,
      title: title,
      tmdbId: tmdbId,
      posterUrl: posterUrl ?? this.posterUrl,
      backdropUrl: backdropUrl ?? this.backdropUrl,
      overview: overview ?? this.overview,
    );
  }
}
