from __future__ import annotations

import argparse
import json

def main() -> None:
    parser = argparse.ArgumentParser(description="WatchNext ML pipeline runner")
    parser.add_argument(
        "phase",
        choices=["eda", "features", "models", "evaluate", "all"],
        nargs="?",
        default="all",
    )
    args = parser.parse_args()

    if args.phase in {"eda", "all"}:
        from src.eda import run_eda

        print(json.dumps(run_eda(), indent=2))
    if args.phase in {"features", "all"}:
        from src.features.build_features import build_features

        print(build_features())
    if args.phase in {"models", "all"}:
        from src.models.collaborative_filtering import train_collaborative_models
        from src.models.content_based import train_content_model
        from src.models.hybrid_recommender import HybridRecommender
        from src.models.neural_cf import train_neural_cf

        print(train_collaborative_models())
        print(train_content_model())
        print(train_neural_cf())
        print(HybridRecommender().save_config())
    if args.phase in {"evaluate", "all"}:
        from src.evaluation.evaluate_models import evaluate_models

        print(json.dumps(evaluate_models(), indent=2))


if __name__ == "__main__":
    main()
