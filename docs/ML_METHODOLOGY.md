# Predictive conversion demonstration · methodology and real evaluation

## Scope and scientific caution

This milestone demonstrates **classification of lead conversion probability**, not forecasting future revenue or daily/weekly sales totals. The model is *educational*. All 600 rows and their binary `converted` labels were generated through a reproducible simulation. No real customer data, ground-truth external outcomes, independent population or calibrated business cost estimates are available. Therefore held-out results describe only the supplied synthetic distribution. The specified project ambition of 85%+ accuracy is **not achieved** and must **not** be claimed.

The overall Module 4 output contains **three distinct quantities**:
1. A **0–100 lead priority score** from authored rules (`app/services/scoring_service.py`), **not ML**.
2. An estimated probability from a **trained logistic regression**, labeled `demo_ml`; without the artifact, mode is `heuristic_not_ml`.
3. A suggested action from an **explainable conditional policy** (`app/services/recommendation_service.py`), **not ML**.

A lead already marked `Converted` returns 1.0 with mode `observed_converted` to indicate **existing known status, not a future prediction**.

## Pipeline

**Data collection (synthetic):** `data/generate_demo_data.py` uses NumPy `default_rng(seed=42)` to generate 600 demonstration rows. The simulated target is drawn probabilistically from a latent function of engagement, stage, contact availability, industry and company size plus Bernoulli randomness. The labels are not simply copied from an input feature. `data/sample_training_data.csv` is the output.

**Features:**

| Feature | Role / meaning |
|---|---|
| `industry` | categorical, including `Unknown` |
| `company_size` | categorical size band, including `Unknown` |
| `lead_status` | categorical stage among `New`, `Contacted`, `Qualified` in training; `Converted` is an observed state excluded from training |
| `engagement_score` | numerical 0–100 from supplied data |
| `has_email` | binary contact flag |
| `has_phone` | binary contact flag |
| `has_contact` | binary named-contact flag |

**Preprocessing:** train-time `ColumnTransformer` applies numerical median imputation and scaling; categorical most-frequent imputation and one-hot encoding with unknown handling. All steps live inside a fitted sklearn `Pipeline`, eliminating separately fit test-time feature transformations.

**Split:** deterministic `train_test_split(test_size=0.25, random_state=42, stratify=y)` → 450 training and 150 independent test rows. **Model:** `LogisticRegression(max_iter=1200, random_state=42)`; simplest technically reasonable baseline. No hyperparameter test-set tuning is performed.

**Prediction:** inference constructs a one-row DataFrame using the exact feature contract (`app/ml/preprocessing.py`), loads a **trusted local** joblib pipeline and returns `predict_proba[:, 1]`, rounded to four decimals. Never load arbitrary user-uploaded artifacts. Missing artifact uses a rule-of-thumb estimate labeled as **non-ML**, not a calibrated real conversion probability.

## Held-out evaluation (actually computed on 2026-10-28 UTC)

| Metric | Calculated value |
|---|---:|
| Training observations | 450 |
| Held-out observations | 150 |
| Positive label share in held-out set | 34.00% |
| Accuracy | **64.67%** |
| Precision | **47.22%** |
| Recall | **33.33%** |
| F1 | **39.08%** |
| ROC-AUC | **0.6813** |
| Random seed | 42 |
| Model version | `demo-logreg-v1` |

Values from `artifacts/model_metrics.json`, computed by real scikit-learn calls—not invented or manually adjusted. Any retraining may update metrics and should update this table if different data is used.

**Interpretation:** the classifier distinguishes some patterns better than random on this synthetic dataset but performs far below the target 85% accuracy. A majority-class baseline could score ~66% accuracy in this dataset, so accuracy alone is misleading; both ranking quality and minority-class recall need improvement. No production-level accuracy is demonstrated. A business-ready model requires real labeled outcomes, disjoint temporal splits, leakage audits, probability calibration (e.g., calibration curve / Brier score), subgroup monitoring, robustness and drift testing.

## Priority formula (not ML)

```text
0–100 priority =
  industry provided:          10
  company size provided:       10
  contact name and email:      20 (10 each)
  engagement score:           25 × engagement/100
  lead lifecycle stage:       20 (New 2, Contacted 10, Qualified 17, Converted 20)
  reachable email or phone:    10
  saved intelligence exists:    5
```

Bands: `Low` below 40; `Medium` 40–59.99; `High` 60–79.99; `Critical` 80+. These weights are design choices for explainability, **not learned coefficients or empirical proof of correlation**. Industry is only a completeness proxy, not verified product-market fit.

Module 2 qualification uses its **own** documented 100-point rubric: industry 15, named contact 10, email 20, phone 10, company size 10, engagement 20, lifecycle stage 15. Qualification bands: `Very Low` (0–19.99), `Low` (20–39.99), `Medium` (40–59.99), `High` (60–79.99), `Very High` (80–100).

## Reproduction on Windows

```bat
python -m data.generate_demo_data
python -m app.ml.train
python -m pytest -q
```

To train from another **appropriately collected and consented** dataset using the same feature names, run `python -m app.ml.train --csv path\to\training.csv`. Do not present a demonstration synthetic model as validated for real customer deployment. Model status is accessible at `GET /api/scoring/model/status` and shown on the Lead Scoring page.
