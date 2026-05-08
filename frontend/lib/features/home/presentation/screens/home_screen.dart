import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/hero_banner.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/movie_row.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/rating_setup_dialog.dart';
import 'package:watch_next_frontend/features/movies/data/services/movie_api_service.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';
import 'package:watch_next_frontend/features/movies/presentation/screens/movie_detail_screen.dart';
import 'package:watch_next_frontend/features/movies/providers/movie_providers.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final ScrollController _scrollController = ScrollController();
  bool _isScrolled = false;
  bool _didBootstrapUser = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(() {
      if (_scrollController.offset > 50 && !_isScrolled) {
        setState(() => _isScrolled = true);
      } else if (_scrollController.offset <= 50 && _isScrolled) {
        setState(() => _isScrolled = false);
      }
    });
    Future.microtask(_bootstrapUserProfile);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _openMovieDetails(Movie movie) {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => MovieDetailScreen(movie: movie)));
  }

  Future<void> _bootstrapUserProfile() async {
    if (_didBootstrapUser) {
      return;
    }
    _didBootstrapUser = true;

    final nextUserId = await ref.read(movieApiServiceProvider).getNextUserId();
    if (!mounted) {
      return;
    }

    ref.read(currentUserProvider.notifier).updateUser(nextUserId);
  }

  Future<void> _openRatingDialog(List<Movie> seedMovies) async {
    final userId = ref.read(currentUserProvider);
    final savedCount = await showDialog<int>(
      context: context,
      builder: (context) =>
          RatingSetupDialog(userId: userId, seedMovies: seedMovies),
    );

    if (!mounted || savedCount == null || savedCount == 0) {
      return;
    }

    ref.invalidate(recommendationsProvider(userId));
    ref.invalidate(trendingProvider);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Saved $savedCount rating${savedCount == 1 ? '' : 's'} for profile #$userId.',
        ),
      ),
    );
  }

  List<Movie> _buildSeedMovies(
    List<Movie> recommendations,
    List<Movie> trending,
  ) {
    final byId = <int, Movie>{};
    for (final movie in [...recommendations.take(6), ...trending.take(8)]) {
      byId[movie.movieId] = movie;
    }
    return byId.values.toList();
  }

  @override
  Widget build(BuildContext context) {
    final currentUserId = ref.watch(currentUserProvider);
    final recommendations = ref.watch(recommendationsProvider(currentUserId));
    final trending = ref.watch(trendingProvider);
    final recommendedMovies = recommendations.asData?.value ?? const <Movie>[];
    final trendingMovies = trending.asData?.value ?? const <Movie>[];
    final heroMovie = recommendedMovies.isNotEmpty
        ? recommendedMovies.first
        : (trendingMovies.isNotEmpty ? trendingMovies.first : null);
    final seedMovies = _buildSeedMovies(recommendedMovies, trendingMovies);

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: _isScrolled ? Colors.black : Colors.transparent,
        title: Image.network(
          'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg',
          height: 30,
          errorBuilder: (context, error, stackTrace) => const Text(
            'WATCHNEXT',
            style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
          ),
        ),
        actions: [
          TextButton.icon(
            onPressed: () => _openRatingDialog(seedMovies),
            icon: const Icon(Icons.star_rate_rounded),
            label: const Text('Rate Taste'),
          ),
          _SearchAction(),
          const SizedBox(width: 20),
          CircleAvatar(
            backgroundColor: Colors.red.shade700,
            radius: 18,
            child: Text(
              '$currentUserId',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 24),
        ],
      ),
      body: SingleChildScrollView(
        controller: _scrollController,
        child: Column(
          children: [
            HeroBanner(
              movie: heroMovie,
              onMoreInfo: heroMovie != null
                  ? () => _openMovieDetails(heroMovie)
                  : null,
            ),
            Transform.translate(
              offset: const Offset(0, -56),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: _TasteSetupPanel(
                  userId: currentUserId,
                  onRatePressed: () => _openRatingDialog(seedMovies),
                ),
              ),
            ),
            recommendations.when(
              data: (movies) => MovieRow(
                title: 'Top Picks For Profile #$currentUserId',
                movies: movies,
                onMovieTap: _openMovieDetails,
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stackTrace) =>
                  Center(child: Text('Error: $error')),
            ),
            trending.when(
              data: (movies) => MovieRow(
                title: 'Trending Now',
                movies: movies,
                onMovieTap: _openMovieDetails,
              ),
              loading: () => const SizedBox(),
              error: (error, stackTrace) => const SizedBox(),
            ),
            const SizedBox(height: 100),
          ],
        ),
      ),
    );
  }
}

class _TasteSetupPanel extends StatelessWidget {
  const _TasteSetupPanel({required this.userId, required this.onRatePressed});

  final int userId;
  final VoidCallback onRatePressed;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1A1A1A),
            const Color(0xFFE50914).withValues(alpha: 0.35),
          ],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 22,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        runSpacing: 16,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Shape your feed in minutes',
                  style: theme.textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  'Open the rating window, pick a few titles, and WatchNext will refresh recommendations and trending signals for profile #$userId.',
                  style: theme.textTheme.bodyLarge,
                ),
              ],
            ),
          ),
          FilledButton.icon(
            onPressed: onRatePressed,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Start Rating'),
          ),
        ],
      ),
    );
  }
}

class _SearchAction extends ConsumerWidget {
  const _SearchAction();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return IconButton(
      icon: const Icon(Icons.person_search),
      tooltip: 'Change User',
      onPressed: () {
        showDialog(
          context: context,
          builder: (context) {
            final controller = TextEditingController();
            return AlertDialog(
              title: const Text('Search Recommendations by User ID'),
              content: TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  hintText: 'Enter User ID (e.g., 1, 2, 3)',
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () {
                    final id = int.tryParse(controller.text);
                    if (id != null) {
                      ref.read(currentUserProvider.notifier).updateUser(id);
                      ref.invalidate(recommendationsProvider(id));
                      Navigator.pop(context);
                    }
                  },
                  child: const Text('Search'),
                ),
              ],
            );
          },
        );
      },
    );
  }
}
