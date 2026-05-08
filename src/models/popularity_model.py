import pandas as pd
from ..data_loader import load_data


movies, ratings = load_data()


def get_popular_movies(movies, ratings, min_ratings=50):
    # Count ratings per movie
    rating_counts = ratings.groupby("movieId").size()

    # Average rating per movie
    rating_means = ratings.groupby("movieId")["rating"].mean()

    # Combine
    popularity = pd.DataFrame({
        "count": rating_counts,
        "mean": rating_means
    })

    # Filter movies with enough ratings
    popularity = popularity[popularity["count"] >= min_ratings]

    # Sort by rating, then use count as a tie-breaker.
    popularity = popularity.sort_values(by=["mean", "count"], ascending=[False, False])

    # Merge with movie titles
    popularity = popularity.merge(movies, on="movieId")

    return popularity[["movieId", "title", "count", "mean"]]


if __name__ == "__main__":
    movies, ratings = load_data()
    
    top_movies = get_popular_movies(movies, ratings)
    
    print("Top Recommended Movies (Popularity-Based):\n")
    print(top_movies)
