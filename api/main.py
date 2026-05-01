from __future__ import annotations

import time
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from watchnext.common import get_paths
from watchnext.data_loader import load_raw_data
from watchnext.models.content_based import recommend_similar, train_content_model
from watchnext.models.collaborative_filtering import train_collaborative_models
from watchnext.models.hybrid_recommender import HybridRecommender
from watchnext.models.neural_cf import train_neural_cf


def ensure_models_trained():
    """Check if model files exist; if not, trigger training with a lock to prevent race conditions."""
    paths = get_paths()
    lock_file = paths.saved_models / ".init.lock"
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


# Initialize application components
ensure_models_trained()
dataset = load_raw_data()
movies = dataset["movies"].merge(
    dataset["links"][["movieId", "tmdbId"]], on="movieId", how="left"
)
recommender = HybridRecommender()

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
    return {"user_id": user_id, "recommendations": recommender.recommend(user_id, top_n=n)}


@app.get("/similar/{movie_id}")
def similar_movies(movie_id: int, n: int = 10):
    return {"movie_id": movie_id, "similar_movies": recommend_similar(movie_id, top_n=n)}


@app.get("/movie/{movie_id}")
def get_movie(movie_id: int):
    movie = movies[movies["movieId"] == movie_id]
    if movie.empty:
        return {"error": "Movie not found"}
    return movie.iloc[0].to_dict()
