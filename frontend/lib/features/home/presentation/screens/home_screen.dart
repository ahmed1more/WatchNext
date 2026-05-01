import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/hero_banner.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/movie_row.dart';
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
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _openMovieDetails(Movie movie) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => MovieDetailScreen(movie: movie),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final currentUserId = ref.watch(currentUserProvider);
    final recommendations = ref.watch(recommendationsProvider(currentUserId));

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
        actions: const [
          _SearchAction(),
          SizedBox(width: 20),
          CircleAvatar(backgroundColor: Colors.blue, radius: 15),
          SizedBox(width: 40),
        ],
      ),
      body: SingleChildScrollView(
        controller: _scrollController,
        child: Column(
          children: [
            recommendations.when(
              data: (movies) => HeroBanner(
                movie: movies.isNotEmpty ? movies.first : null,
                onMoreInfo: movies.isNotEmpty
                    ? () => _openMovieDetails(movies.first)
                    : null,
              ),
              loading: () => const HeroBanner(),
              error: (error, stackTrace) => const HeroBanner(),
            ),
            const SizedBox(height: 20),
            recommendations.when(
              data: (movies) => MovieRow(
                title: 'Recommendations For User $currentUserId',
                movies: movies,
                onMovieTap: _openMovieDetails,
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stackTrace) => Center(child: Text('Error: $error')),
            ),
            recommendations.when(
              data: (movies) => MovieRow(
                title: 'Trending Now',
                movies: movies.reversed.toList(),
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
                decoration: const InputDecoration(hintText: 'Enter User ID (e.g., 1, 2, 3)'),
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
