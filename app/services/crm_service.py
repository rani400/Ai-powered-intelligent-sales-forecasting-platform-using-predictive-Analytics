"""CRM mapping, safe preview and opt-in live HTTP integrations."""
import re
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException
from app.schemas.crm import CRMProvider, CRMPreview, CRMMappingInfo, CRMFieldMapping

_SF_FIELDS = {'company_name': 'Company', 'contact_name': 'FirstName / LastName',
              'email': 'Email', 'phone': 'Phone', 'industry': 'Industry'}
_HS_FIELDS = {'company_name': 'company', 'contact_name': 'firstname / lastname',
              'email': 'email', 'phone': 'phone'}
_NOT_SYNCED = ['lead_status', 'engagement_score', 'notes', 'source', 'is_active', 'company_size']


def get_mapping(provider: CRMProvider) -> CRMMappingInfo:
    target = 'Lead' if provider == CRMProvider.salesforce else 'Contact'
    mapping = _SF_FIELDS if provider == CRMProvider.salesforce else _HS_FIELDS
    return CRMMappingInfo(provider=provider, target_object=target,
                          fields=[CRMFieldMapping(source=a, destination=b) for a, b in mapping.items()],
                          not_synced=_NOT_SYNCED)


def _person_parts(name: str | None):
    parts = (name or '').strip().split()
    if not parts:
        return '', ''
    return (' '.join(parts[:-1]), parts[-1]) if len(parts) > 1 else ('', parts[0])


def build_preview(provider: CRMProvider, lead) -> CRMPreview:
    first, last = _person_parts(lead.contact_name)
    if provider == CRMProvider.salesforce:
        if not last:
            raise HTTPException(422, 'Salesforce requires a contact name')
        payload = {'Company': lead.company_name, 'FirstName': first, 'LastName': last}
        if lead.email:
            payload['Email'] = lead.email
        if lead.phone:
            payload['Phone'] = lead.phone
        if lead.industry:
            payload['Industry'] = lead.industry
        return CRMPreview(provider=provider, lead_id=lead.lead_id, target_object='Lead',
                          operation='create', payload=payload)
    if not lead.email:
        raise HTTPException(422, 'HubSpot requires an email for upsert')
    payload = {'email': lead.email, 'company': lead.company_name}
    if first:
        payload['firstname'] = first
    if last:
        payload['lastname'] = last
    if lead.phone:
        payload['phone'] = lead.phone
    return CRMPreview(provider=provider, lead_id=lead.lead_id, target_object='Contact',
                      operation='upsert_by_email', payload=payload)


def _salesforce_base_url(host: str) -> str:
    # Reject arbitrary hosts, ports, paths, credentials, HTTP and lookalike domains.
    if not isinstance(host, str) or not re.fullmatch(
        r'https://[a-zA-Z0-9-]+\.my\.salesforce\.com', host):
        raise HTTPException(503, 'Salesforce instance URL is not configured safely')
    return host


def _post_json(url: str, token: str, body: dict):
    try:
        with httpx.Client(timeout=12.0, follow_redirects=False, trust_env=False) as client:
            response = client.post(url, headers={'Authorization': f'Bearer {token}',
                  'Content-Type': 'application/json'}, json=body)
        try:
            data = response.json()
        except ValueError:
            data = {}
        return response.status_code, data
    except httpx.RequestError as exc:
        # Never return upstream URL/headers/tokens in an API exception.
        raise HTTPException(502, 'CRM provider request failed') from None


def live_sync(preview: CRMPreview, settings) -> str:
    if preview.provider == CRMProvider.salesforce:
        base = _salesforce_base_url(settings.salesforce_instance_url)
        if not settings.salesforce_access_token:
            raise HTTPException(503, 'Salesforce access token is not configured')
        url = base + '/services/data/v60.0/sobjects/Lead/'
        status, data = _post_json(url, settings.salesforce_access_token, preview.payload)
        if status != 201 or not isinstance(data, dict) or not data.get('success') or not data.get('id'):
            raise HTTPException(502, 'Salesforce did not confirm the record write')
        return str(data['id'])
    if not settings.hubspot_access_token:
        raise HTTPException(503, 'HubSpot access token is not configured')
    url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert'
    data_in = {'inputs': [{'idProperty': 'email', 'id': preview.payload['email'],
                           'properties': preview.payload}]}
    status, data = _post_json(url, settings.hubspot_access_token, data_in)
    if status not in (200, 201) or not isinstance(data, dict) or not data.get('results'):
        raise HTTPException(502, 'HubSpot did not confirm the record write')
    remote_id = data['results'][0].get('id')
    if not remote_id:
        raise HTTPException(502, 'HubSpot did not return a contact identifier')
    return str(remote_id)
