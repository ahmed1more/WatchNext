from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer

from watchnext.common import get_paths
from watchnext.data_loader import load_raw_data


def train_content_model(output_dir: Path | None = None) -> dict[str, Path]:
    paths = get_paths()
    target_dir = output_dir or paths.saved_models
    target_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_raw_data()
    movies = dataset["movies"].copy()
    tags = dataset["tags"].copy()

    movies["genres_list"] = movies["genres"].fillna("(no genres listed)").str.split("|")
    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform(movies["genres_list"])

    tag_text = (
        tags.assign(tag=tags["tag"].fillna("").str.lower())
        .groupby("movieId")["tag"]
        .apply(lambda values: " ".join(values))
    )
    movies["tag_text"] = movies["movieId"].map(tag_text).fillna("")

    tfidf = TfidfVectorizer(max_features=500, stop_words="english")
    tag_matrix = tfidf.fit_transform(movies["tag_text"])

    # Optimization: Use float32 and concatenate numpy arrays directly to save memory
    feature_matrix = np.hstack([
        genre_matrix.astype(np.float32),
        tag_matrix.toarray().astype(np.float32)
    ])
    
    similarity = cosine_similarity(feature_matrix).astype(np.float32)
    similarity_df = pd.DataFrame(similarity, index=movies["movieId"], columns=movies["movieId"])

    similarity_path = target_dir / "content_similarity.pkl"
    metadata_path = target_dir / "content_movies.pkl"
    vectorizer_path = target_dir / "content_vectorizer.pkl"

    similarity_df.to_pickle(similarity_path)
    movies.to_pickle(metadata_path)
    with open(vectorizer_path, "wb") as file:
        pickle.dump({"tfidf": tfidf, "genres": mlb.classes_.tolist()}, file)

    return {
        "similarity": similarity_path,
        "movies": metadata_path,
        "vectorizer": vectorizer_path,
    }


def recommend_similar(movie_id: int, top_n: int = 10, model_dir: Path | None = None) -> list[dict]:
    paths = get_paths()
    source_dir = model_dir or paths.saved_models
    similarity_df = pd.read_pickle(source_dir / "content_similarity.pkl")
    movies = pd.read_pickle(source_dir / "content_movies.pkl")

    if movie_id not in similarity_df.index:
        return []

    ranked = similarity_df.loc[movie_id].sort_values(ascending=False).iloc[1 : top_n + 1]
    matched = movies[movies["movieId"].isin(ranked.index)].copy()
    matched["score"] = matched["movieId"].map(ranked.to_dict())
    return matched.sort_values("score", ascending=False)[["movieId", "title", "score"]].to_dict("records")
