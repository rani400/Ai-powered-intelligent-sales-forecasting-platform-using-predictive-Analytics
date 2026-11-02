"""Run with the TEAM repo's existing tests/conftest.py client + created fixtures."""
import httpx
import pytest
from fastapi import HTTPException

from app.config import Settings, get_settings
from app.main import app
from app.services import crm_service


def _live_settings(**kwargs):
    defaults = dict(crm_live_sync_enabled=True, crm_admin_key='testing-admin-secret',
                    hubspot_access_token='test-hubspot-token',
                    salesforce_access_token='test-salesforce-token',
                    salesforce_instance_url='https://example.my.salesforce.com')
    defaults.update(kwargs)
    return Settings(**defaults)


def test_salesforce_mapping(client):
    response = client.get('/api/crm/mappings/salesforce')
    assert response.status_code == 200
    body = response.json()
    assert body['target_object'] == 'Lead'
    assert any(row['destination'] == 'Company' for row in body['fields'])
    assert 'lead_status' in body['not_synced']


def test_hubspot_mapping(client):
    body = client.get('/api/crm/mappings/hubspot').json()
    assert body['target_object'] == 'Contact'
    assert any(row['destination'] == 'email' for row in body['fields'])


def test_unknown_provider(client):
    assert client.get('/api/crm/mappings/unknown').status_code == 422


def test_salesforce_preview_uses_existing_lead(client, created):
    response = client.get(f"/api/crm/preview/salesforce/{created['lead_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body['payload']['Company'] == created['company_name']
    assert body['payload']['FirstName'] == 'Sam'
    assert body['payload']['LastName'] == 'Test'
    assert body['payload']['Email'] == created['email']
    assert body['operation'] == 'create'


def test_hubspot_preview(client, created):
    response = client.get(f"/api/crm/preview/hubspot/{created['lead_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body['payload']['company'] == created['company_name']
    assert body['payload']['firstname'] == 'Sam'
    assert body['payload']['lastname'] == 'Test'
    assert body['payload']['email'] == created['email']
    assert body['operation'] == 'upsert_by_email'


def test_missing_lead(client):
    assert client.get('/api/crm/preview/hubspot/99999').status_code == 404


def test_salesforce_requires_contact_name(client, sample):
    data = {**sample, 'contact_name': None, 'email': 'no-name@example.org'}
    lead = client.post('/api/leads', json=data).json()
    response = client.get(f"/api/crm/preview/salesforce/{lead['lead_id']}")
    assert response.status_code == 422


def test_hubspot_requires_email(client, sample):
    data = {**sample, 'email': None}
    lead = client.post('/api/leads', json=data).json()
    response = client.get(f"/api/crm/preview/hubspot/{lead['lead_id']}")
    assert response.status_code == 422


def test_dry_run_no_network(client, created, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Dry-run attempted a network call!')
    monkeypatch.setattr(crm_service, '_post_json', forbidden)
    response = client.post(f"/api/crm/sync/hubspot/{created['lead_id']}",
                           json={'dry_run': True})
    assert response.status_code == 200
    assert response.json()['status'] == 'dry_run'
    assert response.json()['preview']['payload']['email'] == created['email']


def test_live_requires_confirmation(client, created):
    response = client.post(f"/api/crm/sync/salesforce/{created['lead_id']}",
                           json={'dry_run': False, 'confirm_live': False})
    assert response.status_code == 400


def test_live_off_by_default(client, created):
    response = client.post(f"/api/crm/sync/salesforce/{created['lead_id']}",
                           json={'dry_run': False, 'confirm_live': True})
    assert response.status_code == 503


def test_live_rejects_missing_admin_key(client, created):
    app.dependency_overrides[get_settings] = lambda: _live_settings()
    response = client.post(f"/api/crm/sync/hubspot/{created['lead_id']}",
                           json={'dry_run': False, 'confirm_live': True})
    assert response.status_code == 403


def test_live_hubspot_upsert_success_mocked(client, created, monkeypatch):
    app.dependency_overrides[get_settings] = lambda: _live_settings()
    captured = {}

    def fake_post(url, token, body):
        captured.update(url=url, token=token, body=body)
        return 200, {'status': 'COMPLETE', 'results': [{'id': 'hubspot-42'}]}

    monkeypatch.setattr(crm_service, '_post_json', fake_post)
    response = client.post(f"/api/crm/sync/hubspot/{created['lead_id']}",
                           headers={'X-CRM-Admin-Key': 'testing-admin-secret'},
                           json={'dry_run': False, 'confirm_live': True})
    assert response.status_code == 200, response.text
    assert response.json()['remote_id'] == 'hubspot-42'
    assert captured['body']['inputs'][0]['idProperty'] == 'email'
    assert captured['body']['inputs'][0]['id'] == created['email']
    assert captured['url'].startswith('https://api.hubapi.com/')


def test_live_salesforce_create_success_mocked(client, created, monkeypatch):
    app.dependency_overrides[get_settings] = lambda: _live_settings()
    captured = {}

    def fake_post(url, token, body):
        captured.update(url=url, body=body)
        return 201, {'id': '00QfakeID', 'success': True, 'errors': []}

    monkeypatch.setattr(crm_service, '_post_json', fake_post)
    response = client.post(f"/api/crm/sync/salesforce/{created['lead_id']}",
                           headers={'X-CRM-Admin-Key': 'testing-admin-secret'},
                           json={'dry_run': False, 'confirm_live': True})
    assert response.status_code == 200, response.text
    assert response.json()['remote_id'] == '00QfakeID'
    assert captured['url'].endswith('/services/data/v60.0/sobjects/Lead/')
    assert captured['body']['LastName'] == 'Test'


def test_provider_failure_returns_sanitized_error(client, created, monkeypatch):
    app.dependency_overrides[get_settings] = lambda: _live_settings()
    monkeypatch.setattr(crm_service, '_post_json', lambda *args: (401, {'error': 'sensitive upstream details'}))
    response = client.post(f"/api/crm/sync/hubspot/{created['lead_id']}",
                           headers={'X-CRM-Admin-Key': 'testing-admin-secret'},
                           json={'dry_run': False, 'confirm_live': True})
    assert response.status_code == 502
    assert 'sensitive upstream details' not in response.text


@pytest.mark.parametrize('host', [
    'https://evil.example.com', 'http://example.my.salesforce.com',
    'https://example.my.salesforce.com.evil.example.com',
    'https://example.my.salesforce.com/extra',
])
def test_salesforce_rejects_untrusted_instance(host):
    with pytest.raises(HTTPException) as exc:
        crm_service._salesforce_base_url(host)
    assert exc.value.status_code == 503


def test_http_transport_uses_bearer_without_real_network(monkeypatch):
    client_constructor = httpx.Client
    observed = {}

    def handler(request):
        observed['url'] = str(request.url)
        observed['authorization'] = request.headers['authorization']
        return httpx.Response(201, json={'id': 'fake', 'success': True})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(crm_service.httpx, 'Client',
                        lambda **kwargs: client_constructor(transport=transport, **kwargs))
    status, result = crm_service._post_json('https://example.my.salesforce.com/test',
                                           'fake-token', {'Company': 'Demo'})
    assert status == 201 and result['id'] == 'fake'
    assert observed['authorization'] == 'Bearer fake-token'
