import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:watch_next_frontend/features/home/presentation/widgets/movie_card.dart';
import 'package:watch_next_frontend/features/movies/domain/models/movie.dart';

class MovieRow extends StatefulWidget {
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
  State<MovieRow> createState() => _MovieRowState();
}

class _MovieRowState extends State<MovieRow> {
  static const double _rowHeight = 240;
  static const double _scrollStep = 360;

  late final ScrollController _scrollController;
  bool _canScrollBack = false;
  bool _canScrollForward = false;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController()..addListener(_updateScrollState);
    WidgetsBinding.instance.addPostFrameCallback((_) => _updateScrollState());
  }

  @override
  void didUpdateWidget(covariant MovieRow oldWidget) {
    super.didUpdateWidget(oldWidget);
    WidgetsBinding.instance.addPostFrameCallback((_) => _updateScrollState());
  }

  @override
  void dispose() {
    _scrollController
      ..removeListener(_updateScrollState)
      ..dispose();
    super.dispose();
  }

  void _updateScrollState() {
    if (!_scrollController.hasClients) {
      return;
    }

    final position = _scrollController.position;
    final canScrollBack = position.pixels > position.minScrollExtent;
    final canScrollForward = position.pixels < position.maxScrollExtent;

    if (canScrollBack != _canScrollBack ||
        canScrollForward != _canScrollForward) {
      setState(() {
        _canScrollBack = canScrollBack;
        _canScrollForward = canScrollForward;
      });
    }
  }

  Future<void> _scrollBy(double delta) async {
    if (!_scrollController.hasClients) {
      return;
    }

    final position = _scrollController.position;
    final target = (position.pixels + delta).clamp(
      position.minScrollExtent,
      position.maxScrollExtent,
    );

    await _scrollController.animateTo(
      target,
      duration: const Duration(milliseconds: 260),
      curve: Curves.easeOutCubic,
    );
  }

  void _handlePointerSignal(PointerSignalEvent event) {
    if (event is! PointerScrollEvent || !_scrollController.hasClients) {
      return;
    }

    final delta = event.scrollDelta.dx == 0
        ? event.scrollDelta.dy
        : event.scrollDelta.dx;
    if (delta == 0) {
      return;
    }

    final position = _scrollController.position;
    final target = (position.pixels + delta).clamp(
      position.minScrollExtent,
      position.maxScrollExtent,
    );
    _scrollController.jumpTo(target);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 12),
          child: Text(
            widget.title,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
        ),
        SizedBox(
          height: _rowHeight,
          child: Stack(
            children: [
              Scrollbar(
                controller: _scrollController,
                thumbVisibility: _canScrollBack || _canScrollForward,
                child: Listener(
                  onPointerSignal: _handlePointerSignal,
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 36),
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.movies.length,
                    itemBuilder: (context, index) {
                      return MovieCard(
                        movie: widget.movies[index],
                        onTap: () => widget.onMovieTap(widget.movies[index]),
                      );
                    },
                  ),
                ),
              ),
              if (_canScrollBack)
                _RowNavButton(
                  alignment: Alignment.centerLeft,
                  icon: Icons.chevron_left,
                  onPressed: () => _scrollBy(-_scrollStep),
                ),
              if (_canScrollForward)
                _RowNavButton(
                  alignment: Alignment.centerRight,
                  icon: Icons.chevron_right,
                  onPressed: () => _scrollBy(_scrollStep),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _RowNavButton extends StatelessWidget {
  const _RowNavButton({
    required this.alignment,
    required this.icon,
    required this.onPressed,
  });

  final Alignment alignment;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: alignment,
      child: Container(
        width: 64,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: alignment == Alignment.centerLeft
                ? Alignment.centerLeft
                : Alignment.centerRight,
            end: alignment == Alignment.centerLeft
                ? Alignment.centerRight
                : Alignment.centerLeft,
            colors: [
              Colors.black.withValues(alpha: 0.85),
              Colors.black.withValues(alpha: 0.0),
            ],
          ),
        ),
        child: Center(
          child: IconButton.filled(
            onPressed: onPressed,
            style: IconButton.styleFrom(
              backgroundColor: Colors.black.withValues(alpha: 0.65),
            ),
            icon: Icon(icon, size: 28),
          ),
        ),
      ),
    );
  }
}
