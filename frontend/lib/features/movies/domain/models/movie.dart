class Movie {
  final int movieId;
  final String title;
  final int? tmdbId;
  final String? genres;
  final double? score;
  final double? averageRating;
  final int? ratingCount;
  final String? posterUrl;
  final String? backdropUrl;
  final String? overview;

  Movie({
    required this.movieId,
    required this.title,
    this.tmdbId,
    this.genres,
    this.score,
    this.averageRating,
    this.ratingCount,
    this.posterUrl,
    this.backdropUrl,
    this.overview,
  });

  factory Movie.fromJson(Map<String, dynamic> json) {
    int? readInt(String key) {
      final value = json[key];
      if (value is num) {
        return value.toInt();
      }
      return null;
    }

    double? readDouble(String key) {
      final value = json[key];
      if (value is num) {
        return value.toDouble();
      }
      return null;
    }

    return Movie(
      movieId: readInt('movieId') ?? 0,
      title: (json['title'] as String?) ?? 'Untitled',
      tmdbId: readInt('tmdbId'),
      genres: json['genres'] as String?,
      score: readDouble('score'),
      averageRating: readDouble('averageRating') ?? readDouble('mean'),
      ratingCount: readInt('ratingCount') ?? readInt('count'),
      posterUrl: json['posterUrl'] as String?,
      backdropUrl: json['backdropUrl'] as String?,
      overview: json['overview'] as String?,
    );
  }

  Movie copyWith({
    String? title,
    int? tmdbId,
    String? genres,
    double? score,
    double? averageRating,
    int? ratingCount,
    String? posterUrl,
    String? backdropUrl,
    String? overview,
  }) {
    return Movie(
      movieId: movieId,
      title: title ?? this.title,
      tmdbId: tmdbId ?? this.tmdbId,
      genres: genres ?? this.genres,
      score: score ?? this.score,
      averageRating: averageRating ?? this.averageRating,
      ratingCount: ratingCount ?? this.ratingCount,
      posterUrl: posterUrl ?? this.posterUrl,
      backdropUrl: backdropUrl ?? this.backdropUrl,
      overview: overview ?? this.overview,
    );
  }
}
