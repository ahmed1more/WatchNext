from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from watchnext.common import get_paths
from watchnext.data_loader import load_raw_data
from watchnext.models import collaborative_filtering, content_based, neural_cf


class HybridRecommender:
    def __init__(
        self,
        model_dir: Path | None = None,
        alpha: float = 0.45,
        beta: float = 0.35,
        gamma: float = 0.20,
        ratings_frame: pd.DataFrame | None = None,
    ):
        self.paths = get_paths()
        self.model_dir = model_dir or self.paths.saved_models
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        dataset = load_raw_data()
        self.movies = dataset["movies"]
        self.ratings = ratings_frame.copy() if ratings_frame is not None else dataset["ratings"]
        self.user_counts = self.ratings.groupby("userId").size()
        self.movie_counts = self.ratings.groupby("movieId").size()
        self.user_seen = self.ratings.groupby("userId")["movieId"].apply(set).to_dict()
        
        similarity_path = self.model_dir / "content_similarity.pkl"
        if similarity_path.exists():
            self.content_similarity = pd.read_pickle(similarity_path)
        else:
            print(f"Warning: {similarity_path} not found. Content-based features will be limited.")
            self.content_similarity = pd.DataFrame()

    def _normalize(self, scores: pd.Series) -> pd.Series:
        if scores.empty:
            return scores
        min_score = scores.min()
        max_score = scores.max()
        if max_score == min_score:
            return pd.Series(1.0, index=scores.index)
        return (scores - min_score) / (max_score - min_score)

    def _content_scores(self, user_id: int, candidate_ids: list[int]) -> pd.Series:
        seen_movies = list(self.user_seen.get(user_id, set()))
        if not seen_movies:
            popularity = self.ratings.groupby("movieId")["rating"].mean()
            return popularity.reindex(candidate_ids).fillna(0.0)
        available_seen = [movie_id for movie_id in seen_movies if movie_id in self.content_similarity.index]
        if not available_seen:
            return pd.Series(0.0, index=candidate_ids)
        scores = self.content_similarity.loc[available_seen].mean(axis=0)
        return scores.reindex(candidate_ids).fillna(0.0)

    def recommend(self, user_id: int, top_n: int = 10, cold_user_threshold: int = 20) -> list[dict]:
        all_movie_ids = self.movies["movieId"].tolist()
        seen_movies = self.user_seen.get(user_id, set())
        candidate_ids = [movie_id for movie_id in all_movie_ids if movie_id not in seen_movies]
        if not candidate_ids:
            return []

        content_scores = self._normalize(self._content_scores(user_id, candidate_ids))

        if self.user_counts.get(user_id, 0) < cold_user_threshold:
            final_scores = content_scores
        else:
            cf_scores = self._normalize(collaborative_filtering.score_user_items(user_id, candidate_ids, self.model_dir, "svd"))
            neural_scores = self._normalize(neural_cf.score_user_items(user_id, candidate_ids, self.model_dir))
            if cf_scores.empty and neural_scores.empty:
                final_scores = content_scores
            else:
                final_scores = (
                    self.alpha * cf_scores.reindex(candidate_ids).fillna(0.0)
                    + self.beta * content_scores.reindex(candidate_ids).fillna(0.0)
                    + self.gamma * neural_scores.reindex(candidate_ids).fillna(0.0)
                )

        top_scores = final_scores.sort_values(ascending=False).head(top_n)
        results = self.movies[self.movies["movieId"].isin(top_scores.index)].copy()
        results["score"] = results["movieId"].map(top_scores.to_dict())
        return results.sort_values("score", ascending=False)[["movieId", "title", "score"]].to_dict("records")

    def save_config(self) -> Path:
        config_path = self.model_dir / "hybrid_config.json"
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump({"alpha": self.alpha, "beta": self.beta, "gamma": self.gamma}, file, indent=2)
        return config_path
