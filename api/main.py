from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from src.common import get_paths
from src.data_loader import load_raw_data
from src.models.content_based import recommend_similar, train_content_model
from src.models.collaborative_filtering import train_collaborative_models
from src.models.hybrid_recommender import HybridRecommender
from src.models.neural_cf import train_neural_cf
from src.models.popularity_model import get_popular_movies


def ensure_models_trained():
    """Check if model files exist; if not, trigger training with a lock to prevent race conditions."""
    paths = get_paths()
    required_files = [
        paths.saved_models / "content_similarity.pkl",
        paths.saved_models / "cf_svd.pkl",
        paths.saved_models / "neural_cf.pt",
    ]

    if all(f.exists() for f in required_files):
        return

    # Simple atomic directory-based lock for cross-platform/multi-worker support
    lock_dir = paths.saved_models / "training.lock"

    # Stale lock recovery (e.g. if a previous container crashed during training)
    if lock_dir.exists() and (time.time() - lock_dir.stat().st_mtime) > 600:
        print("Detected stale training lock. Clearing and restarting training...")
        try:
            lock_dir.rmdir()
        except Exception:
            pass

    try:
        lock_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Another process is already training models. Waiting up to 10 mins...")
        # Wait for the other process to finish (max 10 minutes)
        for _ in range(120):
            time.sleep(5)
            if all(f.exists() for f in required_files):
                print("Models discovered. Continuing.")
                return
        print("Timed out waiting for models. Starting with fallback features.")
        return

    try:
        print("Model files missing. Starting auto-training sequence...")
        train_content_model()
        train_collaborative_models()
        train_neural_cf()
        print("Auto-training complete.")
    finally:
        try:
            lock_dir.rmdir()
        except Exception:
            pass


class Rating(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId", ge=1)
    movie_id: int = Field(alias="movieId", ge=1)
    rating: float = Field(ge=0.5, le=5.0)


def _load_movie_catalog(raw_dataset: dict[str, pd.DataFrame]) -> pd.DataFrame:
    catalog = raw_dataset["movies"].merge(
        raw_dataset["links"][["movieId", "tmdbId"]],
        on="movieId",
        how="left",
    )
    catalog["tmdbId"] = pd.to_numeric(catalog["tmdbId"], errors="coerce").astype("Int64")
    return catalog


def _serialize_records(frame: pd.DataFrame, columns: list[str] | None = None) -> list[dict]:
    if frame.empty:
        return []

    usable = frame.copy()
    if columns is not None:
        usable = usable[[column for column in columns if column in usable.columns]]

    records: list[dict] = []
    for row in usable.to_dict("records"):
        cleaned: dict[str, object] = {}
        for key, value in row.items():
            if pd.isna(value):
                cleaned[key] = None
            elif hasattr(value, "item"):
                cleaned[key] = value.item()
            else:
                cleaned[key] = value
        records.append(cleaned)
    return records


def _attach_movie_metadata(items: list[dict]) -> list[dict]:
    if not items:
        return []

    ranked = pd.DataFrame(items)
    metadata = movies[["movieId", "title", "genres", "tmdbId"]].drop_duplicates("movieId")
    merged = ranked.merge(metadata, on="movieId", how="left", suffixes=("", "_meta"))

    if "title_meta" in merged.columns:
        merged["title"] = merged["title"].fillna(merged["title_meta"])
        merged = merged.drop(columns=["title_meta"])

    ordered_columns = [
        "movieId",
        "title",
        "genres",
        "tmdbId",
        "score",
        "count",
        "mean",
    ]
    return _serialize_records(merged, ordered_columns)


def _refresh_recommender() -> None:
    global recommender
    recommender = HybridRecommender(ratings_frame=dataset["ratings"])


def _get_catalog_with_stats() -> pd.DataFrame:
    stats = (
        dataset["ratings"]
        .groupby("movieId")
        .agg(
            ratingCount=("rating", "size"),
            averageRating=("rating", "mean"),
        )
        .reset_index()
    )
    catalog = movies.merge(stats, on="movieId", how="left")
    catalog["ratingCount"] = catalog["ratingCount"].fillna(0).astype(int)
    catalog["averageRating"] = catalog["averageRating"].fillna(0.0)
    return catalog


# Initialize application components
ensure_models_trained()
dataset = load_raw_data()
movies = _load_movie_catalog(dataset)
recommender = HybridRecommender(ratings_frame=dataset["ratings"])

app = FastAPI(title="WatchNext AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "WatchNext AI is running"}


@app.get("/recommend/{user_id}")
def get_recommendations(user_id: int, n: int = 10):
    recommendations = recommender.recommend(user_id, top_n=n)
    return {
        "user_id": user_id,
        "recommendations": _attach_movie_metadata(recommendations),
    }


@app.get("/similar/{movie_id}")
def similar_movies(movie_id: int, n: int = 10):
    similar = recommend_similar(movie_id, top_n=n)
    return {
        "movie_id": movie_id,
        "similar_movies": _attach_movie_metadata(similar),
    }


@app.get("/trending")
def get_trending_movies(n: int = 10):
    popular = get_popular_movies(dataset["movies"], dataset["ratings"])
    return {"trending": _attach_movie_metadata(popular.head(n).to_dict("records"))}


@app.get("/catalog/search")
def search_catalog(q: str = "", n: int = 20):
    catalog = _get_catalog_with_stats()
    query = q.strip()

    if query:
        lowered = query.lower()
        matches = catalog[catalog["title"].str.contains(query, case=False, na=False)].copy()
        matches["startsWithQuery"] = matches["title"].str.lower().str.startswith(lowered)
        matches = matches.sort_values(
            by=["startsWithQuery", "ratingCount", "averageRating", "title"],
            ascending=[False, False, False, True],
        )
        matches = matches.drop(columns=["startsWithQuery"])
    else:
        matches = catalog.sort_values(
            by=["ratingCount", "averageRating", "title"],
            ascending=[False, False, True],
        )

    return {
        "results": _serialize_records(
            matches.head(n),
            ["movieId", "title", "genres", "tmdbId", "ratingCount", "averageRating"],
        )
    }


@app.get("/users/next")
def get_next_user_id():
    next_user_id = int(dataset["ratings"]["userId"].max()) + 1
    return {"user_id": next_user_id}


@app.post("/rate")
def rate_movie(rating: Rating):
    if movies[movies["movieId"] == rating.movie_id].empty:
        raise HTTPException(status_code=404, detail="Movie not found")

    paths = get_paths()
    ratings_path = paths.raw_data / "ratings.csv"
    new_rating = pd.DataFrame([
        {
            "userId": rating.user_id,
            "movieId": rating.movie_id,
            "rating": rating.rating,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }
    ])

    new_rating.to_csv(ratings_path, mode="a", header=False, index=False)

    global dataset
    dataset["ratings"] = pd.concat([dataset["ratings"], new_rating], ignore_index=True)
    _refresh_recommender()

    return {
        "message": "Rating saved successfully",
        "user_id": rating.user_id,
        "movie_id": rating.movie_id,
        "rating": rating.rating,
    }


@app.get("/movie/{movie_id}")
def get_movie(movie_id: int):
    movie = movies[movies["movieId"] == movie_id]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
    return _serialize_records(movie.head(1))[0]
