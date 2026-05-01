from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from watchnext.common import DATA_DIR, RAW_DATA_DIR


def _ensure_data_exists(target_dir: Path) -> None:
    """Download and unzip the MovieLens dataset if it doesn't exist."""
    if (target_dir / "movies.csv").exists():
        return

    print(f"Data not found at {target_dir}. Downloading MovieLens Small dataset...")
    url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        # The zip contains a directory 'ml-latest-small/'
        # We want to extract its contents to our RAW_DATA_DIR
        zip_ref.extractall(DATA_DIR)
    
    print("Download and extraction complete.")


def load_raw_data(csv_path: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the MovieLens small dataset tables."""
    base_path = csv_path or RAW_DATA_DIR
    if csv_path is None:
        _ensure_data_exists(base_path)
        
    return {
        "movies": pd.read_csv(base_path / "movies.csv"),
        "ratings": pd.read_csv(base_path / "ratings.csv"),
        "links": pd.read_csv(base_path / "links.csv"),
        "tags": pd.read_csv(base_path / "tags.csv"),
    }


def load_data(csv_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backward-compatible loader returning movies and ratings only."""
    dataset = load_raw_data(csv_path)
    return dataset["movies"], dataset["ratings"]


if __name__ == "__main__":
    dataset = load_raw_data()
    for name, frame in dataset.items():
        print(f"{name}: {frame.shape}")
