"""Train a REPRODUCIBLE DEMO model on explicitly SYNTHETIC examples."""
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from app.ml.preprocessing import FEATURES, CATEGORICAL, NUMERIC
from app.config import ROOT, get_settings


def train(csv_path=None, model_path=None, metrics_path=None):
    settings = get_settings()
    csv_path = Path(csv_path or ROOT / 'data' / 'sample_training_data.csv')
    model_path = Path(model_path or settings.model_path)
    metrics_path = Path(metrics_path or settings.metrics_path)
    frame = pd.read_csv(csv_path)
    needed = set(FEATURES + ['converted'])
    if not needed.issubset(frame.columns):
        raise ValueError(f'Training data missing: {sorted(needed - set(frame.columns))}')
    if len(frame) < 50 or frame['converted'].nunique() != 2:
        raise ValueError('Need at least 50 rows and both conversion classes')
    X, y = frame[FEATURES], frame['converted'].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.25, random_state=42, stratify=y)
    preprocess = ColumnTransformer([
        ('numeric', Pipeline([('imputer', SimpleImputer(strategy='median')), ('scale', StandardScaler())]), NUMERIC),
        ('category', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                               ('onehot', OneHotEncoder(handle_unknown='ignore'))]), CATEGORICAL),
    ])
    pipeline = Pipeline([('preprocess', preprocess), ('classifier', LogisticRegression(max_iter=1200, random_state=42))])
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]
    metrics = {
        'model_version': 'demo-logreg-v1', 'data_provenance': 'SYNTHETIC demonstration data, not real customer outcomes',
        'rows': int(len(frame)), 'train_rows': int(len(X_train)), 'test_rows': int(len(X_test)),
        'positive_rate_test': round(float(y_test.mean()), 4), 'random_seed': 42,
        'accuracy': round(float(accuracy_score(y_test, predictions)), 4),
        'precision': round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        'recall': round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        'f1': round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        'roc_auc': round(float(roc_auc_score(y_test, probabilities)), 4),
        'evaluated_at_utc': datetime.now(timezone.utc).isoformat(),
        'limitations': 'Synthetic classification evaluation, not proof of real-world prediction accuracy.'
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    return metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv')
    parser.add_argument('--model')
    parser.add_argument('--metrics')
    args = parser.parse_args()
    print(json.dumps(train(args.csv, args.model, args.metrics), indent=2))
