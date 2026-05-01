from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from watchnext.data_loader import load_raw_data
from watchnext.models.content_based import recommend_similar
from watchnext.models.hybrid_recommender import HybridRecommender

dataset = load_raw_data()
movies = dataset["movies"].merge(dataset["links"][["movieId", "tmdbId"]], on="movieId", how="left")
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
