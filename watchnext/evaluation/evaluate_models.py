from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from watchnext.common import get_paths
from watchnext.data_loader import load_raw_data
from watchnext.evaluation.metrics import (
    coverage,
    mae,
    ndcg_at_k,
    novelty,
    precision_at_k,
    recall_at_k,
    rmse,
    temporal_train_test_split,
)
from watchnext.models.collaborative_filtering import score_user_items as cf_score_user_items
from watchnext.models.content_based import recommend_similar
from watchnext.models.hybrid_recommender import HybridRecommender


def evaluate_models(output_path: Path | None = None, k: int = 10) -> dict[str, dict[str, float]]:
    paths = get_paths()
    dataset = load_raw_data()
    ratings = dataset["ratings"]
    movies = dataset["movies"]
    train, test = temporal_train_test_split(ratings)
    test_users = test["userId"].drop_duplicates().tolist()[:100]
    popularity = train.groupby("movieId").size()
    hybrid = HybridRecommender(ratings_frame=train)
    catalog_size = movies["movieId"].nunique()

    rating_truth: list[float] = []
    rating_pred_cf: list[float] = []
    recommended_cf: list[list[int]] = []
    recommended_hybrid: list[list[int]] = []
    recommended_content: list[list[int]] = []
    precision_scores = {"content": [], "cf": [], "hybrid": []}
    recall_scores = {"content": [], "cf": [], "hybrid": []}
    ndcg_scores = {"content": [], "cf": [], "hybrid": []}

    for user_id in test_users:
        relevant_items = set(test.loc[(test["userId"] == user_id) & (test["rating"] >= 4.0), "movieId"].tolist())
        if not relevant_items:
            continue

        candidate_ids = list(movies["movieId"].tolist())
        cf_scores = cf_score_user_items(user_id, candidate_ids)
        cf_top = cf_scores.sort_values(ascending=False).head(k).index.tolist()
        hybrid_top = [row["movieId"] for row in hybrid.recommend(user_id, top_n=k)]

        seen_movie = train.loc[train["userId"] == user_id, "movieId"].iloc[0] if not train.loc[train["userId"] == user_id].empty else movies["movieId"].iloc[0]
        content_top = [row["movieId"] for row in recommend_similar(int(seen_movie), top_n=k)]

        recommended_cf.append(cf_top)
        recommended_hybrid.append(hybrid_top)
        recommended_content.append(content_top)

        for key, recs in {"content": content_top, "cf": cf_top, "hybrid": hybrid_top}.items():
            precision_scores[key].append(precision_at_k(relevant_items, recs, k))
            recall_scores[key].append(recall_at_k(relevant_items, recs, k))
            ndcg_scores[key].append(ndcg_at_k(relevant_items, recs, k))

        user_test_ratings = test.loc[test["userId"] == user_id, ["movieId", "rating"]]
        for _, row in user_test_ratings.iterrows():
            if row["movieId"] in cf_scores.index:
                rating_truth.append(float(row["rating"]))
                rating_pred_cf.append(float(cf_scores.loc[row["movieId"]]))

    results = {
        "content": {
            "precision_at_k": float(np.mean(precision_scores["content"])) if precision_scores["content"] else 0.0,
            "recall_at_k": float(np.mean(recall_scores["content"])) if recall_scores["content"] else 0.0,
            "ndcg_at_k": float(np.mean(ndcg_scores["content"])) if ndcg_scores["content"] else 0.0,
            "coverage": coverage(recommended_content, catalog_size),
            "novelty": novelty(recommended_content, popularity),
        },
        "cf": {
            "rmse": rmse(np.array(rating_truth), np.array(rating_pred_cf)) if rating_truth else 0.0,
            "mae": mae(np.array(rating_truth), np.array(rating_pred_cf)) if rating_truth else 0.0,
            "precision_at_k": float(np.mean(precision_scores["cf"])) if precision_scores["cf"] else 0.0,
            "recall_at_k": float(np.mean(recall_scores["cf"])) if recall_scores["cf"] else 0.0,
            "ndcg_at_k": float(np.mean(ndcg_scores["cf"])) if ndcg_scores["cf"] else 0.0,
            "coverage": coverage(recommended_cf, catalog_size),
            "novelty": novelty(recommended_cf, popularity),
        },
        "hybrid": {
            "precision_at_k": float(np.mean(precision_scores["hybrid"])) if precision_scores["hybrid"] else 0.0,
            "recall_at_k": float(np.mean(recall_scores["hybrid"])) if recall_scores["hybrid"] else 0.0,
            "ndcg_at_k": float(np.mean(ndcg_scores["hybrid"])) if ndcg_scores["hybrid"] else 0.0,
            "coverage": coverage(recommended_hybrid, catalog_size),
            "novelty": novelty(recommended_hybrid, popularity),
        },
    }

    target_path = output_path or (paths.reports / "evaluation_summary.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)
    return results


if __name__ == "__main__":
    print(json.dumps(evaluate_models(), indent=2))
