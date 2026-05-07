from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, save_npz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer

from watchnext.common import get_paths
from watchnext.data_loader import load_raw_data


def _extract_release_year(movies: pd.DataFrame) -> pd.Series:
    return pd.to_numeric(movies["title"].str.extract(r"\((\d{4})\)$")[0], errors="coerce")


def build_user_features(ratings: pd.DataFrame) -> pd.DataFrame:
    """Calculate user-level features like rating behavior and recency."""
    ratings = ratings.copy()
    ratings["rated_at"] = pd.to_datetime(ratings["timestamp"], unit="s")
    max_timestamp = ratings["rated_at"].max()
    ratings["days_since_rating"] = (max_timestamp - ratings["rated_at"]).dt.days
    ratings["recency_weight"] = np.exp(-ratings["days_since_rating"] / 365.0)

    user_features = ratings.groupby("userId").agg(
        mean_rating=("rating", "mean"),
        std_rating=("rating", "std"),
        rating_count=("rating", "count"),
        first_rating=("rated_at", "min"),
        last_rating=("rated_at", "max"),
        mean_recency_weight=("recency_weight", "mean"),
    )
    user_features["active_years"] = (
        (user_features["last_rating"] - user_features["first_rating"]).dt.days / 365.25
    ).fillna(0.0)
    user_features = user_features.drop(columns=["first_rating", "last_rating"]).fillna(0.0)
    return user_features


def build_genre_features(movies: pd.DataFrame) -> pd.DataFrame:
    """Multi-hot encode movie genres."""
    movies = movies.copy()
    movies["genres_list"] = movies["genres"].fillna("(no genres listed)").str.split("|")
    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform(movies["genres_list"])
    return pd.DataFrame(
        genre_matrix,
        index=movies["movieId"],
        columns=[f"genre_{genre}" for genre in mlb.classes_],
    )


def build_tag_features(tags: pd.DataFrame, movies: pd.DataFrame, max_features: int = 500) -> pd.DataFrame:
    """Create TF-IDF features from user-assigned tags."""
    tag_text = (
        tags.assign(tag=tags["tag"].fillna("").str.lower())
        .groupby("movieId")["tag"]
        .apply(lambda values: " ".join(values))
    )
    
    # Ensure all movies have a tag_text entry even if empty
    movies_tag_text = movies["movieId"].map(tag_text).fillna("")
    
    tfidf = TfidfVectorizer(max_features=max_features, stop_words="english")
    tag_matrix = tfidf.fit_transform(movies_tag_text)
    
    return pd.DataFrame(
        tag_matrix.toarray(),
        index=movies["movieId"],
        columns=[f"tag_{name}" for name in tfidf.get_feature_names_out()],
    )


def build_item_features(
    movies: pd.DataFrame, 
    ratings: pd.DataFrame, 
    genre_features: pd.DataFrame, 
    tag_features: pd.DataFrame
) -> pd.DataFrame:
    """Combine movies info, ratings stats, genres, and tag features."""
    movies = movies.copy()
    movies["release_year"] = _extract_release_year(movies)
    movies["release_decade"] = (movies["release_year"].fillna(0) // 10 * 10).astype(int)
    
    item_stats = ratings.groupby("movieId").agg(
        avg_rating=("rating", "mean"),
        rating_count=("rating", "count"),
        rating_std=("rating", "std"),
    ).fillna(0.0)

    return (
        movies.set_index("movieId")[["release_year", "release_decade"]]
        .join(item_stats, how="left")
        .join(genre_features, how="left")
        .join(tag_features, how="left")
        .fillna(0.0)
    )


def build_interaction_matrix(ratings: pd.DataFrame) -> tuple[csr_matrix, dict]:
    """Create a sparse interaction matrix and mappings."""
    user_categories = pd.Categorical(ratings["userId"])
    movie_categories = pd.Categorical(ratings["movieId"])
    
    interactions = csr_matrix(
        (
            ratings["rating"].astype(np.float32),
            (user_categories.codes, movie_categories.codes),
        ),
        shape=(len(user_categories.categories), len(movie_categories.categories)),
    )
    
    mappings = {
        "user_ids": list(map(int, user_categories.categories.tolist())),
        "movie_ids": list(map(int, movie_categories.categories.tolist())),
    }
    
    return interactions, mappings


def build_features(output_dir: Path | None = None) -> dict[str, Path]:
    """Execute full feature engineering pipeline and save artifacts."""
    paths = get_paths()
    target_dir = output_dir or paths.processed
    target_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_raw_data()
    
    user_features = build_user_features(dataset["ratings"])
    genre_features = build_genre_features(dataset["movies"])
    tag_features = build_tag_features(dataset["tags"], dataset["movies"])
    item_features = build_item_features(dataset["movies"], dataset["ratings"], genre_features, tag_features)
    interactions, interaction_mappings = build_interaction_matrix(dataset["ratings"])

    user_features_path = target_dir / "user_features.pkl"
    item_features_path = target_dir / "item_features.pkl"
    interactions_path = target_dir / "interaction_matrix.npz"
    mappings_path = target_dir / "interaction_mappings.json"

    user_features.to_pickle(user_features_path)
    item_features.to_pickle(item_features_path)
    save_npz(interactions_path, interactions)

    interaction_mappings["tag_feature_count"] = int(tag_features.shape[1])
    with open(mappings_path, "w", encoding="utf-8") as file:
        json.dump(interaction_mappings, file)

    return {
        "user_features": user_features_path,
        "item_features": item_features_path,
        "interaction_matrix": interactions_path,
        "interaction_mappings": mappings_path,
    }


if __name__ == "__main__":
    print(build_features())
