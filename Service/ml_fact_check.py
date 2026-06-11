"""Local ML model for fact-checking — fallback when the external API is unavailable.

The model is a CalibratedClassifierCV wrapping a LinearSVC, trained on
~206 Brazilian Portuguese political claims with TF-IDF word+char n-grams.
"""

import asyncio
import os
from typing import Any

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import FeatureUnion

_ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__))

_model: CalibratedClassifierCV | None = None
_vectorizer: FeatureUnion | None = None
_threshold: float | None = None
_classes: list[str] | None = None


def _load_artifacts() -> None:
    """Load model artifacts from disk on first use (lazy, cached)."""

    global _model, _vectorizer, _threshold, _classes

    if _model is not None:
        return

    _model = joblib.load(os.path.join(_ARTIFACTS_DIR, "modelo_factcheck.joblib"))
    _vectorizer = joblib.load(os.path.join(_ARTIFACTS_DIR, "vetorizador.joblib"))
    _threshold = joblib.load(os.path.join(_ARTIFACTS_DIR, "threshold.joblib"))
    _classes = joblib.load(os.path.join(_ARTIFACTS_DIR, "classes.joblib"))


async def predict(query: str) -> dict[str, Any]:
    """Run a blocking model prediction in a thread and return a result dict.

    The returned dict is shaped to match the upstream Claim schema as
    closely as possible, while clearly indicating the local source.
    """

    _load_artifacts()

    result = await asyncio.to_thread(_predict_sync, query)
    return result


def _predict_sync(query: str) -> dict[str, Any]:
    """Synchronous prediction — to be run via asyncio.to_thread."""

    idx_v = _classes.index("Verdadeiro")  # type: ignore[union-attr]
    x_vec = _vectorizer.transform([query])  # type: ignore[union-attr]
    prob = _model.predict_proba(x_vec)[0]  # type: ignore[union-attr]
    confidence_true = float(prob[idx_v])
    result_label = "Verdadeiro" if confidence_true >= _threshold else "Falso"  # type: ignore[operator]

    return {
        "claim": query,
        "resultado": result_label,
        "confianca_verdadeiro": round(confidence_true, 4),
        "confianca_falso": round(1.0 - confidence_true, 4),
        "threshold": float(_threshold),  # type: ignore[arg-type]
        "fonte": "modelo_local",
    }
