from __future__ import annotations

import json

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import seaborn as sns
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    sns = None

from src.common import get_paths
from src.data_loader import load_raw_data


def _extract_release_year(movies: pd.DataFrame) -> pd.Series:
    return (
        movies["title"]
        .str.extract(r"\((\d{4})\)$")[0]
        .pipe(pd.to_numeric, errors="coerce")
    )


def run_eda(cold_user_threshold: int = 20, cold_item_threshold: int = 10) -> dict[str, float]:
    paths = get_paths()
    dataset = load_raw_data()
    movies = dataset["movies"].copy()
    ratings = dataset["ratings"].copy()
    links = dataset["links"].copy()
    tags = dataset["tags"].copy()

    movies["release_year"] = _extract_release_year(movies)
    movies["genres_list"] = movies["genres"].fillna("(no genres listed)").str.split("|")
    ratings_with_movies = ratings.merge(movies[["movieId", "genres_list", "release_year"]], on="movieId", how="left")

    duplicate_pairs = int(ratings.duplicated(subset=["userId", "movieId"]).sum())
    dangling_movie_ids = int((~ratings["movieId"].isin(movies["movieId"])).sum())
    null_counts = {
        table_name: frame.isnull().sum().sum().item()
        for table_name, frame in dataset.items()
    }

    user_counts = ratings.groupby("userId").size()
    movie_counts = ratings.groupby("movieId").size()
    sparsity = 1.0 - (len(ratings) / (ratings["userId"].nunique() * ratings["movieId"].nunique()))

    metrics = {
        "num_users": float(ratings["userId"].nunique()),
        "num_movies": float(movies["movieId"].nunique()),
        "num_ratings": float(len(ratings)),
        "ratings_sparsity": float(sparsity),
        "duplicate_user_movie_pairs": float(duplicate_pairs),
        "dangling_movie_ids": float(dangling_movie_ids),
        "cold_start_users": float((user_counts < cold_user_threshold).sum()),
        "cold_start_movies": float((movie_counts < cold_item_threshold).sum()),
    }
    metrics.update({f"nulls_{name}": float(count) for name, count in null_counts.items()})

    if sns is not None:
        sns.set_theme(style="whitegrid")

    plt.figure(figsize=(8, 5))
    if sns is not None:
        sns.histplot(ratings["rating"], bins=np.arange(0.25, 5.75, 0.5), kde=False)
    else:
        plt.hist(ratings["rating"], bins=np.arange(0.25, 5.75, 0.5))
    plt.title("Rating Distribution")
    plt.tight_layout()
    plt.savefig(paths.plots / "rating_distribution.png", dpi=150)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    if sns is not None:
        sns.histplot(user_counts, bins=40, ax=axes[0])
    else:
        axes[0].hist(user_counts, bins=40)
    axes[0].set_yscale("log")
    axes[0].set_title("Ratings Per User")
    if sns is not None:
        sns.histplot(movie_counts, bins=40, ax=axes[1])
    else:
        axes[1].hist(movie_counts, bins=40)
    axes[1].set_yscale("log")
    axes[1].set_title("Ratings Per Movie")
    fig.tight_layout()
    fig.savefig(paths.plots / "ratings_per_user_movie.png", dpi=150)
    plt.close(fig)

    user_sample = ratings["userId"].drop_duplicates().sample(min(100, ratings["userId"].nunique()), random_state=42)
    movie_sample = ratings["movieId"].drop_duplicates().sample(min(100, ratings["movieId"].nunique()), random_state=42)
    density_matrix = (
        ratings[ratings["userId"].isin(user_sample) & ratings["movieId"].isin(movie_sample)]
        .assign(interaction=1)
        .pivot_table(index="userId", columns="movieId", values="interaction", fill_value=0)
    )
    plt.figure(figsize=(10, 8))
    if sns is not None:
        sns.heatmap(density_matrix, cbar=False)
    else:
        plt.imshow(density_matrix, aspect="auto", interpolation="nearest")
    plt.title("Interaction Density Sample")
    plt.tight_layout()
    plt.savefig(paths.plots / "interaction_density.png", dpi=150)
    plt.close()

    genre_exploded = movies[["movieId", "genres_list"]].explode("genres_list")
    genre_pairs = genre_exploded.merge(genre_exploded, on="movieId")
    genre_matrix = pd.crosstab(genre_pairs["genres_list_x"], genre_pairs["genres_list_y"])
    plt.figure(figsize=(10, 8))
    if sns is not None:
        sns.heatmap(genre_matrix, cmap="mako")
    else:
        plt.imshow(genre_matrix, aspect="auto", interpolation="nearest")
    plt.title("Genre Co-occurrence")
    plt.tight_layout()
    plt.savefig(paths.plots / "genre_cooccurrence.png", dpi=150)
    plt.close()

    ratings["rating_year"] = pd.to_datetime(ratings["timestamp"], unit="s").dt.year
    yearly_ratings = ratings.groupby("rating_year")["rating"].mean()
    yearly_release = ratings_with_movies.groupby("release_year")["rating"].mean().dropna()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    yearly_ratings.plot(ax=axes[0], title="Average Rating by Rating Year")
    yearly_release.plot(ax=axes[1], title="Average Rating by Release Year")
    fig.tight_layout()
    fig.savefig(paths.plots / "temporal_drift.png", dpi=150)
    plt.close(fig)

    top_tags = tags["tag"].str.lower().value_counts().head(20)
    plt.figure(figsize=(10, 6))
    if sns is not None:
        sns.barplot(x=top_tags.values, y=top_tags.index)
    else:
        plt.barh(top_tags.index, top_tags.values)
    plt.title("Top Tag Frequency")
    plt.tight_layout()
    plt.savefig(paths.plots / "tag_frequency.png", dpi=150)
    plt.close()

    with open(paths.processed / "eda_summary.json", "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    return metrics


if __name__ == "__main__":
    summary = run_eda()
    print(json.dumps(summary, indent=2))
