"""Validate Gemini integration without sending requests or exposing real keys."""
import json
from types import SimpleNamespace
from app.services import outreach_service as svc
from app.schemas.outreach import OutreachCreate


def test_gemini_openai_compatible_json_request(monkeypatch):
    settings = SimpleNamespace(llm_provider='gemini', llm_api_key='test-only-key',
        llm_model='gemini-3.8-flash',
        llm_api_url='https://generativelanguage.googleapis.com/v1beta/openai/chat/completions')
    monkeypatch.setattr(svc, 'get_settings', lambda: settings)
    seen = {}
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'subject': 'Meeting about Acme',
                            'body': (
                                'Hello Morgan, could we schedule a '
                                'conversation to discuss your goals '
                                'and how we might collaborate? '
                                'Best regards.'
                           )
                        })
                    }
                }]
            }
    class FakeClient:
        def __init__(self, timeout):
            seen['timeout'] = timeout
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, json, headers):
            seen.update({'url': url, 'json': json, 'headers': headers})
            return FakeResponse()
    monkeypatch.setattr(svc.httpx, 'Client', FakeClient)
    lead = SimpleNamespace(company_name='Acme', contact_name='Morgan', industry='Retail',
        company_size='1-10', lead_status='New', notes='Interested in improving workflows')
    req = OutreachCreate(lead_id=7, tone='Professional', email_length='Long',
        communication_goal='Meeting request')
    result = svc.llm_draft(lead, req, None)
    assert result[0] == 'Meeting about Acme'
    assert seen['url'] == settings.llm_api_url
    assert seen['headers']['Authorization'] == 'Bearer test-only-key'
    assert seen['json']['model'] == 'gemini-3.8-flash'
    assert '220 to 300 words' in seen['json']['messages'][1]['content']


def test_no_api_key_skips_remote_request(monkeypatch):
    settings = SimpleNamespace(llm_provider='gemini', llm_api_key='',
        llm_model='gemini-3.8-flash', llm_api_url='https://example.test/')
    monkeypatch.setattr(svc, 'get_settings', lambda: settings)
    assert svc.llm_draft(None, None, None) is None
