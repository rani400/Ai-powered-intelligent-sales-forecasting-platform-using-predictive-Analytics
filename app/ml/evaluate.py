"""Read actual held-out metrics from a completed training run."""
import json
from pathlib import Path
from app.config import get_settings


def model_status():
    config = get_settings()
    mp, jp = Path(config.model_path), Path(config.metrics_path)
    if mp.is_file() and jp.is_file():
        try:
            metrics = json.loads(jp.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            metrics = None
        if metrics:
            return {'available': True, 'mode': 'demo_ml', 'model_version': metrics['model_version'],
                    'metrics': metrics, 'notice': 'Metrics reflect synthetic demo data only; real-world accuracy is unknown.'}
    return {'available': False, 'mode': 'heuristic_not_ml', 'model_version': 'heuristic-v1',
            'metrics': None, 'notice': 'No trained model found. Estimates use a transparent heuristic, not machine learning.'}
