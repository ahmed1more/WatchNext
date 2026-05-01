from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF as SklearnNMF
from sklearn.decomposition import TruncatedSVD

if int(np.__version__.split(".")[0]) >= 2:
    Dataset = NMF = Reader = SVD = GridSearchCV = None
    SURPRISE_AVAILABLE = False
else:
    try:
        from surprise import Dataset, NMF, Reader, SVD
        from surprise.model_selection import GridSearchCV
        SURPRISE_AVAILABLE = True
    except Exception:  # pragma: no cover - environment dependent fallback
        Dataset = NMF = Reader = SVD = GridSearchCV = None
        SURPRISE_AVAILABLE = False

if not SURPRISE_AVAILABLE:
    Dataset = NMF = Reader = SVD = GridSearchCV = None

from src.common import get_paths
from src.data_loader import load_raw_data


def _build_trainset() -> tuple[pd.DataFrame, object]:
    ratings = load_raw_data()["ratings"]
    if not SURPRISE_AVAILABLE:
        raise RuntimeError("surprise backend is unavailable")
    reader = Reader(rating_scale=(float(ratings["rating"].min()), float(ratings["rating"].max())))
    surprise_data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)
    return ratings, surprise_data.build_full_trainset()


def train_collaborative_models(output_dir: Path | None = None, tune: bool = False) -> dict[str, Path]:
    paths = get_paths()
    target_dir = output_dir or paths.saved_models
    target_dir.mkdir(parents=True, exist_ok=True)

    ratings = load_raw_data()["ratings"]
    metadata = {
        "user_ids": sorted(ratings["userId"].unique().tolist()),
        "movie_ids": sorted(ratings["movieId"].unique().tolist()),
    }

    if SURPRISE_AVAILABLE:
        _, trainset = _build_trainset()
        svd_params = {"n_factors": 50, "n_epochs": 20, "reg_all": 0.02, "random_state": 42}
        nmf_params = {"n_factors": 30, "n_epochs": 40, "random_state": 42}

        if tune:
            reader = Reader(rating_scale=(float(ratings["rating"].min()), float(ratings["rating"].max())))
            data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)
            search = GridSearchCV(
                SVD,
                {"n_factors": [20, 50], "n_epochs": [10, 20], "reg_all": [0.02, 0.05]},
                measures=["rmse"],
                cv=3,
                joblib_verbose=0,
            )
            search.fit(data)
            svd_params.update(search.best_params["rmse"])

        svd_model = SVD(**svd_params)
        nmf_model = NMF(**nmf_params)
        svd_model.fit(trainset)
        nmf_model.fit(trainset)
        metadata.update({"backend": "surprise", "svd_params": svd_params, "nmf_params": nmf_params})
    else:
        matrix = ratings.pivot_table(index="userId", columns="movieId", values="rating").fillna(0.0)
        svd_model = TruncatedSVD(n_components=min(50, max(2, min(matrix.shape) - 1)), random_state=42)
        svd_latent = svd_model.fit_transform(matrix)
        svd_reconstruction = pd.DataFrame(
            svd_model.inverse_transform(svd_latent),
            index=matrix.index,
            columns=matrix.columns,
        )

        nmf_model = SklearnNMF(n_components=min(30, max(2, min(matrix.shape) - 1)), init="nndsvda", random_state=42, max_iter=300)
        nmf_latent = nmf_model.fit_transform(np.maximum(matrix, 0))
        nmf_reconstruction = pd.DataFrame(
            nmf_latent @ nmf_model.components_,
            index=matrix.index,
            columns=matrix.columns,
        )
        svd_model = {"type": "reconstruction", "scores": svd_reconstruction}
        nmf_model = {"type": "reconstruction", "scores": nmf_reconstruction}
        metadata.update({"backend": "sklearn-fallback"})

    svd_path = target_dir / "cf_svd.pkl"
    nmf_path = target_dir / "cf_nmf.pkl"
    metadata_path = target_dir / "cf_metadata.json"

    with open(svd_path, "wb") as file:
        pickle.dump(svd_model, file)
    with open(nmf_path, "wb") as file:
        pickle.dump(nmf_model, file)
    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    return {"svd": svd_path, "nmf": nmf_path, "metadata": metadata_path}


def score_user_items(user_id: int, movie_ids: list[int], model_dir: Path | None = None, algorithm: str = "svd") -> pd.Series:
    paths = get_paths()
    source_dir = model_dir or paths.saved_models
    model_path = source_dir / ("cf_svd.pkl" if algorithm == "svd" else "cf_nmf.pkl")
    with open(model_path, "rb") as file:
        model = pickle.load(file)
    if isinstance(model, dict) and model.get("type") == "reconstruction":
        scores = model["scores"]
        if user_id not in scores.index:
            return pd.Series(dtype=float)
        return scores.loc[user_id].reindex(movie_ids).dropna()
    return pd.Series({movie_id: model.predict(user_id, movie_id).est for movie_id in movie_ids})
