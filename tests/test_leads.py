import pytest


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['active_modules'] == 4


def test_create(client, sample):
    r = client.post('/api/leads', json=sample)
    assert r.status_code == 201
    assert r.json()['company_name'] == 'Sample Tech'
    assert r.json()['created_at']


def test_get(client, created):
    r = client.get(f"/api/leads/{created['lead_id']}")
    assert r.status_code == 200
    assert r.json()['email'] == 'sam@example.org'


def test_update(client, created):
    r = client.patch(f"/api/leads/{created['lead_id']}", json={'lead_status': 'Qualified', 'engagement_score': 89})
    assert r.status_code == 200
    assert r.json()['lead_status'] == 'Qualified'
    assert r.json()['engagement_score'] == 89


def test_delete(client, created):
    assert client.delete(f"/api/leads/{created['lead_id']}").status_code == 204
    assert client.get(f"/api/leads/{created['lead_id']}").status_code == 404


def test_missing_lead(client):
    assert client.get('/api/leads/99999').status_code == 404
    assert client.patch('/api/leads/99999', json={'lead_status': 'New'}).status_code == 404


def test_search(client, created):
    assert client.get('/api/leads', params={'search': 'SAMPLE'}).json()['total'] == 1
    assert client.get('/api/leads', params={'search': 'nonexistent'}).json()['total'] == 0


def test_filters(client, created):
    assert client.get('/api/leads', params={'lead_status': 'New'}).json()['total'] == 1
    assert client.get('/api/leads', params={'lead_status': 'Qualified'}).json()['total'] == 0
    assert client.get('/api/leads', params={'industry': 'technology'}).json()['total'] == 1


def test_pagination(client, sample):
    for n in range(3):
        data = dict(sample, email=f'person{n}@example.org', contact_name=f'Person {n}')
        assert client.post('/api/leads', json=data).status_code == 201
    r = client.get('/api/leads', params={'page': 2, 'page_size': 2})
    assert r.status_code == 200
    assert r.json()['total'] == 3
    assert len(r.json()['items']) == 1


@pytest.mark.parametrize('field,value', [
    ('company_name', '   '), ('lead_status', 'Won'), ('engagement_score', 101),
    ('engagement_score', -1), ('email', 'this-is-not-email')])
def test_invalid_create(client, sample, field, value):
    r = client.post('/api/leads', json={**sample, field: value})
    assert r.status_code == 422


def test_duplicate_email(client, created, sample):
    r = client.post('/api/leads', json={**sample, 'company_name': 'New Company', 'contact_name': 'Another Person'})
    assert r.status_code == 409


def test_duplicate_company_contact(client, created, sample):
    r = client.post('/api/leads', json={**sample, 'email': 'other@example.org'})
    assert r.status_code == 409


def test_duplicate_update(client, created, sample):
    second = client.post('/api/leads', json={**sample, 'company_name': 'Other', 'contact_name': 'Zoe', 'email': 'zoe@example.org'}).json()
    r = client.patch(f"/api/leads/{second['lead_id']}", json={'email': created['email']})
    assert r.status_code == 409


def test_required_update_null(client, created):
    assert client.patch(f"/api/leads/{created['lead_id']}", json={'company_name': None}).status_code == 422


def test_not_nullable_email(client, sample):
    sample.pop('email')
    assert client.post('/api/leads', json=sample).status_code == 201


def test_no_extraneous_fields(client, created):
    assert client.patch(f"/api/leads/{created['lead_id']}", json={'unexpected': 'x'}).status_code == 422
