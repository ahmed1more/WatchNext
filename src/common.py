from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "ml-latest-small"
PLOTS_DIR = DATA_DIR / "plots"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT_DIR / "models"
SAVED_MODELS_DIR = MODELS_DIR / "saved"
REPORTS_DIR = ROOT_DIR / "reports"


@dataclass(frozen=True)
class PipelinePaths:
    raw_data: Path = RAW_DATA_DIR
    plots: Path = PLOTS_DIR
    processed: Path = PROCESSED_DIR
    models: Path = MODELS_DIR
    saved_models: Path = SAVED_MODELS_DIR
    reports: Path = REPORTS_DIR

    def ensure(self) -> "PipelinePaths":
        for directory in (
            self.plots,
            self.processed,
            self.models,
            self.saved_models,
            self.reports,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self


def get_paths() -> PipelinePaths:
    return PipelinePaths().ensure()

if __name__ == "__main__":
    print(ROOT_DIR)