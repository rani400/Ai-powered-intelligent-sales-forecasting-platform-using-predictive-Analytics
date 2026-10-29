"""Demo ML prediction with explicitly labeled heuristic fallback."""
from functools import lru_cache
from pathlib import Path
import joblib
from app.config import get_settings
from app.ml.preprocessing import lead_features


@lru_cache(maxsize=4)
def load_model(path: str):
    if not Path(path).is_file():
        return None
    return joblib.load(path)  # only load trusted local artifacts produced by our train.py


def predict(lead):
    if lead.lead_status == 'Converted':
        # This is observed status, NOT a forecast.
        return 1.0, 'observed_converted', 'observed-status-v1'
    settings = get_settings()
    model = load_model(settings.model_path)
    if model is not None:
        prob = float(model.predict_proba(lead_features(lead))[:, 1][0])
        return round(max(0.0, min(prob, 1.0)), 4), 'demo_ml', 'demo-logreg-v1'
    # Non-ML fallback explicitly identified; range is a coarse heuristic, not a calibrated probability.
    stage = {'New': 0.05, 'Contacted': 0.13, 'Qualified': 0.28, 'Converted': 0.5}.get(lead.lead_status, 0.05)
    estimate = min(.95, max(.05, .10 + .003 * lead.engagement_score + stage + (.05 if lead.email else 0)))
    return round(estimate, 4), 'heuristic_not_ml', 'heuristic-v1'
