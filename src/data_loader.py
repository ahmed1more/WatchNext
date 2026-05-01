from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common import RAW_DATA_DIR


def load_raw_data(csv_path: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the MovieLens small dataset tables."""
    base_path = csv_path or RAW_DATA_DIR
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
