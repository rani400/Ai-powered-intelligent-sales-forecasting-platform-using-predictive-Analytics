"""Recreate the synthetic training CSV; NO real customer information is used."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def generate(rows=600, seed=42):
    rng = np.random.default_rng(seed)
    industries = ['Technology', 'Retail', 'Healthcare', 'Manufacturing', 'Finance', 'Education', 'Unknown']
    sizes = ['1-10', '11-50', '51-200', '201-500', '500+', 'Unknown']
    stages = ['New', 'Contacted', 'Qualified']
    items = []
    for _ in range(rows):
        industry = rng.choice(industries)
        size = rng.choice(sizes)
        stage = rng.choice(stages, p=[.48, .34, .18])
        eng = int(rng.integers(0, 101))
        email = int(rng.random() < .76)
        phone = int(rng.random() < .63)
        contact = int(rng.random() < .81)
        logit = (-2.8 + .027*eng + {'New': -.65, 'Contacted': .15, 'Qualified': 1.1}[stage]
                 + .30*email + .16*phone + .22*contact + (.20 if industry != 'Unknown' else -.25)
                 + (.20 if size not in ('Unknown', '1-10') else 0))
        probability = 1 / (1 + np.exp(-logit))
        label = int(rng.random() < probability)
        items.append([industry, size, stage, eng, email, phone, contact, label])
    frame = pd.DataFrame(items, columns=['industry', 'company_size', 'lead_status', 'engagement_score',
                                         'has_email', 'has_phone', 'has_contact', 'converted'])
    frame.to_csv(ROOT / 'sample_training_data.csv', index=False)
    return frame


if __name__ == '__main__':
    frame = generate()
    print(f'Generated {len(frame)} synthetic examples; positive fraction = {frame.converted.mean():.3f}')
