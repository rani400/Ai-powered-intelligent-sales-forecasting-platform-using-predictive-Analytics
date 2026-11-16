"""Additional coverage for Module 5 audit logging; run in existing project pytest suite."""
from app.config import Settings, get_settings
from app.main import app


def test_dry_run_creates_audit_record(client, created):
    lead_id = created['lead_id']
    result = client.post(f'/api/crm/sync/hubspot/{lead_id}', json={'dry_run': True})
    assert result.status_code == 200
    app.dependency_overrides[get_settings] = lambda: Settings(crm_admin_key='local-admin-test')
    logs = client.get(f'/api/crm/logs/{lead_id}', headers={'X-CRM-Admin-Key': 'local-admin-test'})
    assert logs.status_code == 200
    assert logs.json()[0]['status'] == 'dry_run'
    assert logs.json()[0]['provider'] == 'hubspot'
    assert logs.json()[0]['remote_id'] is None


def test_audit_log_requires_admin_key(client, created):
    response = client.get(f"/api/crm/logs/{created['lead_id']}")
    assert response.status_code == 403
