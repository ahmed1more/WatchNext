# WatchNext ML Pipeline Implementation Plan

This document outlines the step-by-step implementation of the end-to-end Machine Learning pipeline for the WatchNext recommendation system, exactly as specified in the provided requirements.

## User Review Required

> [!IMPORTANT]
> The Neural Collaborative Filtering (Neural CF) model requires **PyTorch**. Currently, `torch` is not listed in your `pyproject.toml`. I will need to add it as a dependency. I also recommend adding `seaborn` for the EDA phase (genre co-occurrence heatmaps, etc.) and `tqdm` for tracking model training progress.

## Open Questions

> [!WARNING]
> 1. **Dependencies:** Are you okay with me adding `torch`, `seaborn`, and `tqdm` to `pyproject.toml`?
> 2. **Environment:** Once added, do you want me to install these new dependencies into your current environment, or will you handle it?
> 3. **Output Artifacts:** Where should the processed data (e.g., feature matrices, data splits) and trained models be saved? Should I create `data/processed/` and `models/saved/` directories for this purpose?
> 4. **Format for Phase 1 (EDA):** Do you prefer the EDA plots to be output as saved image files (e.g., `data/plots/`), or structured entirely within a Jupyter Notebook (e.g., `notebooks/01_eda.ipynb`) for interactive viewing?

## Proposed Changes

### Configuration & Dependencies
#### [MODIFY] `pyproject.toml`
- Add `torch`, `seaborn`, `tqdm`, and `scipy` (if not implicitly included) to the project dependencies.

### Phase 1 — EDA (Exploratory Data Analysis)
#### [NEW] `notebooks/01_EDA.ipynb` (or corresponding Python script based on your preference)
- **Data Loading:** Load `movies.csv`, `ratings.csv`, `links.csv`, and `tags.csv`. Merge `links.csv` to map TMDB IDs.
- **Integrity Checks:** Check for nulls, duplicate `(userId, movieId)` pairs, and dangling movie IDs in ratings.
- **Visualizations:**
  - Rating distribution histogram (overall and per-genre).
  - Rating count per user and per movie (log-log scale).
  - User-item interaction matrix density plot (1000x1000 sample).
  - Genre co-occurrence heatmap.
  - Temporal drift plots (average rating by year of rating and release year).
  - Tag frequency chart.
- **Cold-Start Identification:** Calculate sparsity and flag users/items below the threshold (e.g., users <20 ratings, movies <10 ratings).

### Phase 2 — Feature Engineering
#### [NEW] `src/features/build_features.py` (or similar location)
- **User Features:** Mean rating, std dev, rating counts, active years, and temporal recency weights.
- **Item Features:** Genre multi-hot encoding, Tag TF-IDF vectors, release decade, average rating, rating count, rating std dev.
- **Interaction Matrix:** Build the sparse `scipy.sparse.csr_matrix` for implicit feedback interactions.

### Phase 3 — Models
#### [NEW] `src/models/collaborative_filtering.py`
- Setup data loaders for the `surprise` library.
- Train SVD and NMF models.
- Implement hyperparameter tuning (GridSearchCV) for `n_factors`, `n_epochs`, and regularizations.

#### [NEW] `src/models/content_based.py`
- Vectorize tags using `TfidfVectorizer`.
- Combine tag TF-IDF and genre multi-hot vectors.
- Compute the movie-movie cosine similarity matrix.

#### [NEW] `src/models/neural_cf.py`
- Define the two-tower embedding model in PyTorch.
- User embedding + Movie embedding -> element-wise product -> MLP -> scalar score.
- Implement training loop with `BCEWithLogitsLoss` and negative sampling.

#### [NEW] `src/models/hybrid_recommender.py`
- Implement the serving-time ensemble.
- Blending logic: `final_score = α*CF + β*Content + γ*NeuralCF`.
- Implement threshold-based routing (e.g., if cold-start user, route entirely through Content-Based).
- Logic to tune $\alpha, \beta, \gamma$ using a validation set to maximize NDCG@10.

### Phase 4 — Evaluation
#### [NEW] `src/evaluation/metrics.py`
- Implement temporal train/test splitting logic.
- Implement metric functions:
  - Rating prediction: RMSE, MAE.
  - Top-N Ranking: Precision@K, Recall@K, NDCG@K.
  - Catalog Metrics: Coverage, Novelty.

#### [NEW] `src/evaluation/evaluate_models.py`
- Offline ablation runs to compare Content-based only vs. CF only vs. Hybrid.
- Generate a summary report of performance.

## Verification Plan

### Automated Tests / Scripts
- **Data Integrity:** Run the EDA/Feature Engineering pipeline to ensure matrices are populated correctly and cold-start entities are properly flagged.
- **Model Training:** Ensure the PyTorch model loss decreases over epochs and SVD `fit()` executes without errors.
- **Evaluation Pipeline:** Ensure the temporal split generates disjoint sets based on timestamps, and that NDCG and Precision/Recall calculations match expected logic.

### Manual Verification
- Review the generated EDA plots to confirm MovieLens distributions (e.g., power laws, 3.5-4.0 rating skew).
- Examine the evaluation output to verify that the Hybrid model outperforms the standalone CF and Content-Based models on NDCG@10.
