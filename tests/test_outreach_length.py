from types import SimpleNamespace
from app.schemas.outreach import OutreachCreate
from app.services import outreach_service as svc


def test_concise_tone_still_respects_long_length():
    lead = SimpleNamespace(company_name='Example Retail', contact_name='Alex Kim', industry='Retail')
    short = OutreachCreate(lead_id=1, tone='Concise', email_length='Short')
    long = OutreachCreate(lead_id=1, tone='Concise', email_length='Long')
    _, small = svc.local_draft(lead, short)
    _, large = svc.local_draft(lead, long)
    assert len(large.split()) > len(small.split()) * 2
    assert 'Example Retail' in large


def test_all_lengths_are_distinct_in_local_mode():
    lead = SimpleNamespace(company_name='Example Retail', contact_name='Alex Kim', industry='Retail')
    drafts = []
    for label in ['Short', 'Medium', 'Long']:
        req = OutreachCreate(lead_id=1, tone='Professional', email_length=label)
        drafts.append(svc.local_draft(lead, req)[1])
    counts = [len(body.split()) for body in drafts]
    assert counts[0] < counts[1] < counts[2]
