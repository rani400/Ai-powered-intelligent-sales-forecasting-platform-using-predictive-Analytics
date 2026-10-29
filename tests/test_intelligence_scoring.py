import json
import subprocess
import sys
import os
import pytest
from sqlalchemy import text
from app.database import make_engine
from app.services.intelligence_service import qualification
from app.services.recommendation_service import recommend


def test_analyze(client, created):
    r = client.post(f"/api/intelligence/{created['lead_id']}/analyze")
    assert r.status_code == 201, r.text
    j = r.json()
    assert j['qualification_band']
    assert 'No external company research' in j['company_summary']
    assert 'Rule-based' in j['methodology']


def test_intelligence_saved(client, created):
    client.post(f"/api/intelligence/{created['lead_id']}/analyze")
    assert client.get(f"/api/intelligence/{created['lead_id']}").status_code == 200


def test_intelligence_gaps(client):
    row = client.post('/api/leads', json={'company_name': 'No Contact LLC'}).json()
    result = client.post(f"/api/intelligence/{row['lead_id']}/analyze").json()
    assert 'Email not recorded' in result['information_gaps']
    assert 'Industry not recorded' in result['information_gaps']
    assert result['qualification_score'] < 20


def test_score(client, created):
    r = client.post(f"/api/scoring/{created['lead_id']}/score")
    assert r.status_code == 201, r.text
    body = r.json()
    assert 0 <= body['score'] <= 100
    assert 0 <= body['conversion_probability'] <= 1
    assert sum(f['points'] for f in body['factors']) == pytest.approx(body['score'])
    assert body['recommended_action']


def test_scoring_saved(client, created):
    client.post(f"/api/scoring/{created['lead_id']}/score")
    assert client.get(f"/api/scoring/{created['lead_id']}").status_code == 200


def test_missing_scoring_and_intelligence(client, created):
    assert client.get(f"/api/scoring/{created['lead_id']}").status_code == 404
    assert client.get(f"/api/intelligence/{created['lead_id']}").status_code == 404


def test_intelligence_bonus(client, created):
    before = client.post(f"/api/scoring/{created['lead_id']}/score").json()['score']
    client.post(f"/api/intelligence/{created['lead_id']}/analyze")
    after = client.post(f"/api/scoring/{created['lead_id']}/score").json()['score']
    assert after - before == 5


def test_model_status(client):
    r = client.get('/api/scoring/model/status')
    assert r.status_code == 200
    assert r.json()['mode'] in ('demo_ml', 'heuristic_not_ml')


def test_prediction_varies(client):
    a = client.post('/api/leads', json={'company_name': 'Alpha', 'engagement_score': 5}).json()
    b = client.post('/api/leads', json={'company_name': 'Beta', 'engagement_score': 95,
                                       'lead_status': 'Qualified', 'email': 'beta@example.org'}).json()
    low = client.post(f"/api/scoring/{a['lead_id']}/score").json()['conversion_probability']
    high = client.post(f"/api/scoring/{b['lead_id']}/score").json()['conversion_probability']
    assert low < high


def test_recommend_no_channel(client):
    row = client.post('/api/leads', json={'company_name': 'No Reach'}).json()
    result = client.post(f"/api/scoring/{row['lead_id']}/score").json()
    assert result['recommended_action'] == 'Request missing contact details'


def test_recommend_contacted(client):
    row = client.post('/api/leads', json={'company_name': 'Contacted', 'email': 'a@example.org',
                                         'lead_status': 'Contacted'}).json()
    result = client.post(f"/api/scoring/{row['lead_id']}/score").json()
    assert result['suggested_outreach_goal'] == 'Follow-up'


def test_cascade_foreign_keys(client, created):
    lead_id = created['lead_id']
    client.post(f'/api/intelligence/{lead_id}/analyze')
    client.post(f'/api/scoring/{lead_id}/score')
    client.post('/api/outreach/generate', json={'lead_id': lead_id})
    assert client.delete(f'/api/leads/{lead_id}').status_code == 204
    assert client.get(f'/api/leads/{lead_id}').status_code == 404
    # Using a known clean test fixture, all FK-owned resources must be deleted.
    from app.main import app
    from app.database import get_db
    from sqlalchemy import select, func
    from app.models import CompanyInsight, LeadScore, OutreachCampaign
    db = next(app.dependency_overrides[get_db]())
    try:
        for table in (CompanyInsight, LeadScore, OutreachCampaign):
            assert db.scalar(select(func.count()).select_from(table)) == 0
    finally:
        db.close()


def test_api_contract_openapi(client):
    schema = client.get('/openapi.json').json()
    paths = schema['paths']
    for path in ['/api/leads', '/api/leads/import', '/api/leads/{lead_id}',
                 '/api/intelligence/{lead_id}/analyze', '/api/outreach/generate',
                 '/api/scoring/{lead_id}/score', '/api/scoring/model/status']:
        assert path in paths
    assert client.get('/docs').status_code == 200


def test_migrations(tmp_path):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    target = tmp_path / 'migrated.db'
    env = dict(os.environ, DATABASE_URL=f'sqlite:///{target}')
    run = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=root, env=env,
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr
    engine = make_engine(f'sqlite:///{target}')
    with engine.connect() as conn:
        version = conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        assert version == '0001'
    engine.dispose()


def test_real_training_metrics_from_synthetic_csv(tmp_path):
    from pathlib import Path
    from app.ml.train import train
    path = Path(__file__).resolve().parents[1] / 'data' / 'sample_training_data.csv'
    metrics = train(csv_path=path, model_path=tmp_path / 'model.joblib', metrics_path=tmp_path / 'metrics.json')
    assert metrics['train_rows'] == 450 and metrics['test_rows'] == 150
    assert all(0 <= metrics[key] <= 1 for key in ('accuracy', 'precision', 'recall', 'f1', 'roc_auc'))
    assert (tmp_path / 'model.joblib').is_file()
    assert (tmp_path / 'metrics.json').is_file()

def test_converted_status_not_predicted(client):
    row = client.post('/api/leads', json={'company_name': 'Already Converted', 'lead_status': 'Converted'}).json()
    result = client.post(f"/api/scoring/{row['lead_id']}/score").json()
    assert result['prediction_mode'] == 'observed_converted'
    assert result['conversion_probability'] == 1.0
