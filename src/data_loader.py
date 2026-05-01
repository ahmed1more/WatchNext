import os
from pathlib import Path
import pandas as pd


parent_dir = Path("./data/ml-latest-small")



def load_data(csv_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads movies and ratings datasets from CSV files.
    
    Args:
        csv_path: Path to the directory containing movies.csv and ratings.csv
        
    Returns:
        A tuple of two DataFrames: (movies, ratings)
    """
    movies = pd.read_csv(csv_path / "movies.csv")
    ratings = pd.read_csv(csv_path / "ratings.csv")
    
    return movies, ratings


if __name__ == "__main__":
    movies, ratings = load_data(parent_dir)
    
    print("Movies shape:", movies.shape)
    print("Ratings shape:", ratings.shape)
    
    print("\nMovies sample:")
    print(movies.head())
    
    print("\nRatings sample:")
    print(ratings.head())