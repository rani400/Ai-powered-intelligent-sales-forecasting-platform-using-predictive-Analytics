from app.services.outreach_service import local_draft
from app.schemas.outreach import OutreachCreate


def test_outreach_generates_draft(client, created):
    r = client.post('/api/outreach/generate', json={'lead_id': created['lead_id'], 'tone': 'Professional',
                                                   'communication_goal': 'Introduction', 'email_length': 'Medium'})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body['campaign_status'] == 'DRAFT'
    assert body['email_subject']
    assert created['company_name'] in body['email_content']


def test_outreach_fallback_is_explicit(client, created, monkeypatch):
    monkeypatch.setattr('app.services.outreach_service.llm_draft', lambda *a, **k: None)
    r = client.post('/api/outreach/generate', json={'lead_id': created['lead_id']})
    assert r.status_code == 201
    assert r.json()['is_mock'] is True
    assert r.json()['provider'] == 'local-template'


def test_outreach_history(client, created):
    id_ = created['lead_id']
    client.post('/api/outreach/generate', json={'lead_id': id_})
    client.post('/api/outreach/generate', json={'lead_id': id_, 'tone': 'Friendly'})
    r = client.get(f'/api/outreach/leads/{id_}/drafts')
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert all(x['campaign_status'] == 'DRAFT' for x in r.json())


def test_outreach_tones_and_goals(client, created):
    for tone, goal in [('Friendly', 'Meeting request'), ('Concise', 'Discovery call'),
                       ('Persuasive', 'Follow-up'), ('Professional', 'Re-engagement')]:
        r = client.post('/api/outreach/generate', json={'lead_id': created['lead_id'],
                     'tone': tone, 'communication_goal': goal, 'email_length': 'Short'})
        assert r.status_code == 201
        assert len(r.json()['email_content']) > 50


def test_invalid_outreach_goal(client, created):
    assert client.post('/api/outreach/generate', json={'lead_id': created['lead_id'],
                                                        'communication_goal': 'Unsolicited SMS'}).status_code == 422


def test_missing_outreach_lead(client):
    assert client.post('/api/outreach/generate', json={'lead_id': 12345}).status_code == 404


def test_email_no_unverified_claims(client, created):
    r = client.post('/api/outreach/generate', json={'lead_id': created['lead_id']})
    content = r.json()['email_content'].lower()
    assert 'guaranteed' not in content
    assert 'million in revenue' not in content
    assert 'partnership' not in content
