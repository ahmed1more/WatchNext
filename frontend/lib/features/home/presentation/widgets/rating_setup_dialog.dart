import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_next_frontend/features/movies/data/services/movie_api_service.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class RatingSetupDialog extends ConsumerStatefulWidget {
  const RatingSetupDialog({
    super.key,
    required this.userId,
    required this.seedMovies,
  });

  final int userId;
  final List<Movie> seedMovies;

  @override
  ConsumerState<RatingSetupDialog> createState() => _RatingSetupDialogState();
}

class _RatingSetupDialogState extends ConsumerState<RatingSetupDialog> {
  final TextEditingController _searchController = TextEditingController();
  final Map<int, _RatedMovieSelection> _selectedMovies = {};

  late Future<List<Movie>> _resultsFuture;
  bool _isSaving = false;
  String? _errorText;

  @override
  void initState() {
    super.initState();
    _resultsFuture = _loadInitialResults();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<List<Movie>> _loadInitialResults() async {
    final catalog = await ref.read(movieApiServiceProvider).searchCatalog('');
    return _mergeUniqueMovies([...widget.seedMovies, ...catalog]);
  }

  void _searchCatalog() {
    FocusScope.of(context).unfocus();
    setState(() {
      _resultsFuture = ref
          .read(movieApiServiceProvider)
          .searchCatalog(_searchController.text.trim());
    });
  }

  void _toggleSelection(Movie movie) {
    setState(() {
      if (_selectedMovies.containsKey(movie.movieId)) {
        _selectedMovies.remove(movie.movieId);
      } else {
        _selectedMovies[movie.movieId] = _RatedMovieSelection(
          movie: movie,
          rating: 4.0,
        );
      }
    });
  }

  void _updateRating(int movieId, double rating) {
    final current = _selectedMovies[movieId];
    if (current == null) {
      return;
    }

    setState(() {
      _selectedMovies[movieId] = current.copyWith(rating: rating);
    });
  }

  Future<void> _saveRatings() async {
    if (_selectedMovies.isEmpty) {
      setState(() {
        _errorText =
            'Pick at least one title before saving your taste profile.';
      });
      return;
    }

    setState(() {
      _isSaving = true;
      _errorText = null;
    });

    try {
      final api = ref.read(movieApiServiceProvider);
      await Future.wait(
        _selectedMovies.values.map(
          (selection) => api.submitRating(
            userId: widget.userId,
            movieId: selection.movie.movieId,
            rating: selection.rating,
          ),
        ),
      );

      if (!mounted) {
        return;
      }
      Navigator.of(context).pop(_selectedMovies.length);
    } catch (_) {
      setState(() {
        _errorText =
            'Saving ratings failed. Make sure the backend is running and try again.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Dialog(
      backgroundColor: const Color(0xFF141414),
      insetPadding: const EdgeInsets.all(24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1080, maxHeight: 760),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Rate Your Taste',
                          style: theme.textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Profile #${widget.userId} | Pick a few catalog titles and score them to refresh recommendations and trending.',
                          style: theme.textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: _isSaving
                        ? null
                        : () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              if (widget.seedMovies.isNotEmpty) ...[
                Text('Quick picks', style: theme.textTheme.titleMedium),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: _mergeUniqueMovies(widget.seedMovies)
                      .take(8)
                      .map(
                        (movie) => FilterChip(
                          selected: _selectedMovies.containsKey(movie.movieId),
                          label: Text(movie.title),
                          onSelected: (_) => _toggleSelection(movie),
                        ),
                      )
                      .toList(),
                ),
                const SizedBox(height: 20),
              ],
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      onSubmitted: (_) => _searchCatalog(),
                      decoration: InputDecoration(
                        hintText: 'Search the recommendation catalog',
                        prefixIcon: const Icon(Icons.search),
                        suffixIcon: IconButton(
                          onPressed: _searchCatalog,
                          icon: const Icon(Icons.arrow_forward),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: _searchCatalog,
                    icon: const Icon(Icons.travel_explore),
                    label: const Text('Browse'),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(flex: 6, child: _buildSearchPane(theme)),
                    const SizedBox(width: 20),
                    Expanded(flex: 5, child: _buildSelectionPane(theme)),
                  ],
                ),
              ),
              if (_errorText != null) ...[
                const SizedBox(height: 16),
                Text(
                  _errorText!,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.red.shade300,
                  ),
                ),
              ],
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: _isSaving
                        ? null
                        : () => Navigator.of(context).pop(),
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: _isSaving ? null : _saveRatings,
                    icon: _isSaving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.auto_awesome),
                    label: Text(
                      _isSaving
                          ? 'Saving...'
                          : 'Save ${_selectedMovies.length} Rating${_selectedMovies.length == 1 ? '' : 's'}',
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSearchPane(ThemeData theme) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1C1C1C),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: FutureBuilder<List<Movie>>(
        future: _resultsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  'Search results could not be loaded right now.',
                  style: theme.textTheme.bodyLarge,
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          final movies = snapshot.data ?? const <Movie>[];
          if (movies.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  'No titles matched that search yet.',
                  style: theme.textTheme.bodyLarge,
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          return Scrollbar(
            thumbVisibility: true,
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: movies.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final movie = movies[index];
                final isSelected = _selectedMovies.containsKey(movie.movieId);
                return _CatalogResultCard(
                  movie: movie,
                  isSelected: isSelected,
                  onToggle: () => _toggleSelection(movie),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildSelectionPane(ThemeData theme) {
    final selections = _selectedMovies.values.toList()
      ..sort((left, right) => left.movie.title.compareTo(right.movie.title));

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFFE50914).withValues(alpha: 0.18),
            const Color(0xFF1C1C1C),
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Selected titles', style: theme.textTheme.titleLarge),
          const SizedBox(height: 6),
          Text(
            'Three or more ratings usually gives the profile a much better starting point.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Expanded(
            child: selections.isEmpty
                ? Center(
                    child: Text(
                      'Add titles from the left, then score them here.',
                      style: theme.textTheme.bodyLarge,
                      textAlign: TextAlign.center,
                    ),
                  )
                : ListView.separated(
                    itemCount: selections.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final selection = selections[index];
                      return _SelectedRatingCard(
                        selection: selection,
                        onRemoved: () => _toggleSelection(selection.movie),
                        onRatingChanged: (value) =>
                            _updateRating(selection.movie.movieId, value),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  List<Movie> _mergeUniqueMovies(List<Movie> movies) {
    final byId = <int, Movie>{};
    for (final movie in movies) {
      byId[movie.movieId] = movie;
    }
    return byId.values.toList();
  }
}

class _CatalogResultCard extends StatelessWidget {
  const _CatalogResultCard({
    required this.movie,
    required this.isSelected,
    required this.onToggle,
  });

  final Movie movie;
  final bool isSelected;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isSelected
              ? const Color(0xFFE50914)
              : Colors.white.withValues(alpha: 0.06),
        ),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: SizedBox(
              width: 58,
              height: 84,
              child: movie.posterUrl != null
                  ? CachedNetworkImage(
                      imageUrl: movie.posterUrl!,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      color: Colors.black26,
                      alignment: Alignment.center,
                      child: const Icon(Icons.movie_creation_outlined),
                    ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(movie.title, style: theme.textTheme.titleMedium),
                const SizedBox(height: 6),
                Text(
                  movie.genres?.replaceAll('|', ' / ') ??
                      'Genre data unavailable',
                  style: theme.textTheme.bodyMedium,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 8),
                Text(_buildStatsLine(movie), style: theme.textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: 14),
          FilledButton.tonalIcon(
            onPressed: onToggle,
            icon: Icon(isSelected ? Icons.check : Icons.add),
            label: Text(isSelected ? 'Added' : 'Add'),
          ),
        ],
      ),
    );
  }

  String _buildStatsLine(Movie movie) {
    if (movie.averageRating == null || movie.ratingCount == null) {
      return 'Ready to rate';
    }
    return '${movie.averageRating!.toStringAsFixed(1)} average | ${movie.ratingCount} ratings';
  }
}

class _SelectedRatingCard extends StatelessWidget {
  const _SelectedRatingCard({
    required this.selection,
    required this.onRemoved,
    required this.onRatingChanged,
  });

  final _RatedMovieSelection selection;
  final VoidCallback onRemoved;
  final ValueChanged<double> onRatingChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.22),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  selection.movie.title,
                  style: theme.textTheme.titleMedium,
                ),
              ),
              IconButton(
                onPressed: onRemoved,
                icon: const Icon(Icons.delete_outline),
              ),
            ],
          ),
          Text(
            selection.movie.genres?.replaceAll('|', ' / ') ??
                'Genre data unavailable',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: Slider(
                  min: 0.5,
                  max: 5,
                  divisions: 9,
                  value: selection.rating,
                  label: selection.rating.toStringAsFixed(1),
                  onChanged: onRatingChanged,
                ),
              ),
              Text(
                '${selection.rating.toStringAsFixed(1)} / 5',
                style: theme.textTheme.titleSmall,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _RatedMovieSelection {
  const _RatedMovieSelection({required this.movie, required this.rating});

  final Movie movie;
  final double rating;

  _RatedMovieSelection copyWith({Movie? movie, double? rating}) {
    return _RatedMovieSelection(
      movie: movie ?? this.movie,
      rating: rating ?? this.rating,
    );
  }
}
