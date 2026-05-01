from watchnext.models.collaborative_filtering import train_collaborative_models
from watchnext.models.content_based import train_content_model
from watchnext.models.hybrid_recommender import HybridRecommender
from watchnext.models.neural_cf import train_neural_cf


def train_all_models() -> None:
    train_collaborative_models()
    train_content_model()
    train_neural_cf()
    HybridRecommender().save_config()


if __name__ == "__main__":
    train_all_models()
