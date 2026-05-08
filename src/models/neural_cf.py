from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from src.common import get_paths
from src.data_loader import load_raw_data


class InteractionDataset(Dataset):
    def __init__(self, frame: pd.DataFrame):
        self.users = torch.tensor(frame["user_idx"].to_numpy(), dtype=torch.long)
        self.items = torch.tensor(frame["movie_idx"].to_numpy(), dtype=torch.long)
        self.labels = torch.tensor(frame["label"].to_numpy(), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.users[idx], self.items[idx], self.labels[idx]


class NeuralCF(nn.Module):
    def __init__(self, num_users: int, num_items: int, embedding_dim: int = 32):
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, user_idx: torch.Tensor, item_idx: torch.Tensor) -> torch.Tensor:
        user_vec = self.user_embedding(user_idx)
        item_vec = self.item_embedding(item_idx)
        return self.mlp(user_vec * item_vec).squeeze(-1)


@dataclass
class NeuralArtifacts:
    model_path: Path
    metadata_path: Path


def _prepare_training_frame(ratings: pd.DataFrame, negative_ratio: int = 2) -> tuple[pd.DataFrame, dict[int, int], dict[int, int]]:
    user_ids = sorted(ratings["userId"].unique())
    movie_ids = sorted(ratings["movieId"].unique())
    user_map = {user_id: idx for idx, user_id in enumerate(user_ids)}
    movie_map = {movie_id: idx for idx, movie_id in enumerate(movie_ids)}

    positives = ratings[["userId", "movieId"]].drop_duplicates().copy()
    positives["label"] = 1.0
    positives["user_idx"] = positives["userId"].map(user_map)
    positives["movie_idx"] = positives["movieId"].map(movie_map)

    observed = set(zip(positives["userId"], positives["movieId"]))
    rng = np.random.default_rng(42)
    negatives: list[tuple[int, int, float, int, int]] = []
    all_movies = np.array(movie_ids)

    for user_id in user_ids:
        user_seen = ratings.loc[ratings["userId"] == user_id, "movieId"].unique()
        candidates = np.setdiff1d(all_movies, user_seen)
        if len(candidates) == 0:
            continue
        sample_size = min(len(candidates), max(1, len(user_seen) * negative_ratio))
        for movie_id in rng.choice(candidates, size=sample_size, replace=False):
            if (user_id, int(movie_id)) not in observed:
                negatives.append((user_id, int(movie_id), 0.0, user_map[user_id], movie_map[int(movie_id)]))

    negatives_df = pd.DataFrame(negatives, columns=["userId", "movieId", "label", "user_idx", "movie_idx"])
    train_frame = pd.concat([positives, negatives_df], ignore_index=True)
    return train_frame.sample(frac=1.0, random_state=42).reset_index(drop=True), user_map, movie_map


def train_neural_cf(output_dir: Path | None = None, epochs: int = 3, batch_size: int = 1024) -> NeuralArtifacts:
    paths = get_paths()
    target_dir = output_dir or paths.saved_models
    target_dir.mkdir(parents=True, exist_ok=True)

    ratings = load_raw_data()["ratings"]
    train_frame, user_map, movie_map = _prepare_training_frame(ratings)
    dataset = InteractionDataset(train_frame)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = NeuralCF(num_users=len(user_map), num_items=len(movie_map)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCEWithLogitsLoss()

    model.train()
    for _ in range(epochs):
        progress = tqdm(loader, desc="NeuralCF", leave=False)
        for user_idx, item_idx, labels in progress:
            user_idx = user_idx.to(device)
            item_idx = item_idx.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(user_idx, item_idx)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            progress.set_postfix(loss=f"{loss.item():.4f}")

    model_path = target_dir / "neural_cf.pt"
    metadata_path = target_dir / "neural_cf_meta.pkl"
    torch.save(model.state_dict(), model_path)
    with open(metadata_path, "wb") as file:
        pickle.dump({"user_map": user_map, "movie_map": movie_map}, file)
    return NeuralArtifacts(model_path=model_path, metadata_path=metadata_path)


def score_user_items(user_id: int, movie_ids: list[int], model_dir: Path | None = None) -> pd.Series:
    paths = get_paths()
    source_dir = model_dir or paths.saved_models
    try:
        with open(source_dir / "neural_cf_meta.pkl", "rb") as file:
            metadata = pickle.load(file)
    except Exception:
        return pd.Series(dtype=float)
    user_map = metadata["user_map"]
    movie_map = metadata["movie_map"]
    if user_id not in user_map:
        return pd.Series(dtype=float)

    valid_movie_ids = [movie_id for movie_id in movie_ids if movie_id in movie_map]
    if not valid_movie_ids:
        return pd.Series(dtype=float)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = NeuralCF(num_users=len(user_map), num_items=len(movie_map)).to(device)
    try:
        model.load_state_dict(torch.load(source_dir / "neural_cf.pt", map_location=device))
    except Exception:
        return pd.Series(dtype=float)
    model.eval()

    with torch.no_grad():
        user_tensor = torch.tensor([user_map[user_id]] * len(valid_movie_ids), dtype=torch.long, device=device)
        movie_tensor = torch.tensor([movie_map[movie_id] for movie_id in valid_movie_ids], dtype=torch.long, device=device)
        scores = torch.sigmoid(model(user_tensor, movie_tensor)).cpu().numpy()
    return pd.Series(scores, index=valid_movie_ids)
