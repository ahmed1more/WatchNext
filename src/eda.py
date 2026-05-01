from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from data_loader import load_data, parent_dir


movies, ratings = load_data(parent_dir)

def basic_info(movies, ratings):
    print("Number of users:", ratings["userId"].nunique())
    print("Number of movies:", movies["movieId"].nunique())
    print("Number of ratings:", len(ratings))


def most_rated_movies(ratings, movies):
    movie_counts = ratings["movieId"].value_counts().head(10)
    
    top_movies = movies[movies["movieId"].isin(movie_counts.index)]
    
    print("\nTop 10 most rated movies:")
    print(top_movies[["title"]])

def rating_distribution(ratings):
    plt.hist(ratings["rating"], bins=10)
    plt.title("Rating Distribution")
    plt.xlabel("Rating")
    plt.ylabel("Count")
    plt.show()


if __name__ == "__main__":
    movies, ratings = load_data(parent_dir)
    
    basic_info(movies, ratings)
    most_rated_movies(ratings, movies)
    rating_distribution(ratings)