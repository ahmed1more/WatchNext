from __future__ import annotations

import math

import numpy as np
import pandas as pd


def temporal_train_test_split(ratings: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = ratings.sort_values("timestamp")
    cutoff = int(len(ordered) * (1 - test_fraction))
    train = ordered.iloc[:cutoff].copy()
    test = ordered.iloc[cutoff:].copy()
    return train, test


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def precision_at_k(relevant: set[int], recommended: list[int], k: int) -> float:
    top_k = recommended[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(top_k)


def recall_at_k(relevant: set[int], recommended: list[int], k: int) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for item in recommended[:k] if item in relevant)
    return hits / len(relevant)


def ndcg_at_k(relevant: set[int], recommended: list[int], k: int) -> float:
    def dcg(items: list[int]) -> float:
        score = 0.0
        for rank, item in enumerate(items[:k], start=1):
            if item in relevant:
                score += 1.0 / math.log2(rank + 1)
        return score

    ideal_length = min(len(relevant), k)
    if ideal_length == 0:
        return 0.0
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_length + 1))
    return dcg(recommended) / ideal


def coverage(recommended_lists: list[list[int]], catalog_size: int) -> float:
    recommended_items = {item for recs in recommended_lists for item in recs}
    if catalog_size == 0:
        return 0.0
    return len(recommended_items) / catalog_size


def novelty(recommended_lists: list[list[int]], popularity: pd.Series) -> float:
    scores: list[float] = []
    total_interactions = float(popularity.sum()) or 1.0
    for recs in recommended_lists:
        for item in recs:
            prob = float(popularity.get(item, 1.0)) / total_interactions
            scores.append(-math.log2(prob))
    return float(np.mean(scores)) if scores else 0.0
