from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from watchnext.common import get_paths
from watchnext.data_loader import load_raw_data
from watchnext.models.content_based import recommend_similar, train_content_model
from watchnext.models.collaborative_filtering import train_collaborative_models
from watchnext.models.hybrid_recommender import HybridRecommender
from watchnext.models.neural_cf import train_neural_cf


def ensure_models_trained():
    """Check if model files exist; if not, trigger training."""
    paths = get_paths()
    required_files = [
        paths.saved_models / "content_similarity.pkl",
        paths.saved_models / "cf_svd.pkl",
        paths.saved_models / "neural_cf.pt",
    ]

    if all(f.exists() for f in required_files):
        return

    print("Model files missing. Starting auto-training sequence (this may take a minute)...")
    train_content_model()
    train_collaborative_models()
    train_neural_cf()
    print("Auto-training complete.")


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
