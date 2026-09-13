import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import joblib
from typing import Any, Dict, List

# Base directory: project root (contains backend and Exasol_MEVShield-main)
BASE_DIR = Path(__file__).parent.parent
MODEL_PATH = BASE_DIR / "Exasol_MEVShield-main" / "models" / "champion_mev_model.joblib"

# Global variables to hold the loaded components
_model: Any = None
_model_name: str = ""
_optimal_threshold: float = 0.0
_feature_names: List[str] = []
_metrics: Dict[str, Any] = {}

def _load_model() -> None:
    """Load the XGBoost model artifact from disk."""
    global _model, _model_name, _optimal_threshold, _feature_names, _metrics
    try:
        artifact = joblib.load(MODEL_PATH)
        _model = artifact.get("model")
        _model_name = artifact.get("model_name", "")
        _optimal_threshold = float(artifact.get("optimal_threshold", 0.0))
        _feature_names = list(artifact.get("feature_names", []))
        _metrics = artifact.get("metrics", {})
    except Exception as e:
        # In a real app, you might want to log this or raise a more specific error
        raise RuntimeError(f"Failed to load model from {MODEL_PATH}: {e}")

# Load the model at module import time
_load_model()

def get_model() -> Any:
    """Return the loaded XGBoost model."""
    return _model

def get_model_name() -> str:
    """Return the model name."""
    return _model_name

def get_optimal_threshold() -> float:
    """Return the optimal threshold for classification."""
    return _optimal_threshold

def get_feature_names() -> List[str]:
    """Return the list of feature names expected by the model."""
    return _feature_names

def get_metrics() -> Dict[str, Any]:
    """Return the metrics dictionary from the artifact."""
    return _metrics

def predict_proba(features: List[float]) -> float:
    """
    Return the probability of the positive class (MEV) for the given feature vector.
    Assumes features are in the same order as `feature_names`.
    """
    if _model is None:
        raise RuntimeError("Model not loaded")
    # Ensure features is a 2D array for sklearn/XGBoost predict_proba
    prob = _model.predict_proba([features])[0][1]  # probability of class 1
    return float(prob)