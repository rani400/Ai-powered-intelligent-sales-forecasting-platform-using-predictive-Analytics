import httpx
from urllib.parse import quote
from .oauth import access_token
from .mapper import FIELDS, EXTERNAL_ID


class CRMError(Exception):
    def __init__(self, status, retry_after=0):
        self.status = status
        self.retry_after = retry_after
        super().__init__(f'HubSpot HTTP {status}')


class HubSpotClient:

    def __init__(self, portal):
        self.portal = portal

    def request(self, method, path, **kwargs):
        for retry in (False, True):
            token = access_token(self.portal, force=retry)

            with httpx.Client(
                base_url='https://api.hubapi.com',
                timeout=20
            ) as http:
                response = http.request(
                    method,
                    path,
                    headers={
                        'Authorization': 'Bearer ' + token
                    },
                    **kwargs
                )

            if response.status_code == 401 and not retry:
                continue

            if not response.is_success or response.status_code == 207:

                # Diagnostic information without exposing tokens
                try:
                    details = response.json()

                    print("HubSpot endpoint:", method, path, flush=True)
                    print("HubSpot status:", response.status_code, flush=True)
                    print("HubSpot category:", details.get("category"), flush=True)
                    print("Detailed error:", details.get("message"), flush=True)
                    for error in details.get("errors", []):
                        print("Error context:", error.get("context"), flush=True)
                        print("Error message:", error.get("message"), flush=True)
                    print("Validation codes:", [
                        e.get("code")
                        for e in details.get("errors", [])
                        if isinstance(e, dict)
                    ], flush=True)

                    print(
                        "Correlation ID:",
                        details.get("correlationId"),
                        flush=True
                    )

                except (ValueError, AttributeError, TypeError):
                    pass

                try:
                    delay = float(
                        response.headers.get('Retry-After', '0')
                    )
                except ValueError:
                    delay = 0

                raise CRMError(response.status_code, delay)

            return response.json() if response.content else {}

    def path(self, kind):
        return '/crm/v3/objects/' + kind

    def get(self, kind, remote_id):
        try:
            return self.request(
                'GET',
                self.path(kind) + '/' + quote(str(remote_id), safe=''),
                params={
                    'properties': ','.join(
                        (*FIELDS[kind], EXTERNAL_ID)
                    )
                }
            )

        except CRMError as e:
            if e.status == 404:
                return None
            raise

    def page(self, kind, after=None):
        params = {
            'limit': 100,
            'properties': ','.join(
                (*FIELDS[kind], EXTERNAL_ID)
            )
        }

        if after is not None:
            params['after'] = after

        return self.request(
            'GET',
            self.path(kind),
            params=params
        )

    def update(self, kind, remote_id, properties):
        return self.request(
            'PATCH',
            self.path(kind) + '/' + quote(str(remote_id), safe=''),
            json={'properties': properties}
        )

    def upsert(self, kind, local_id, properties):
        data = self.request(
            'POST',
            self.path(kind) + '/batch/upsert',
            json={
                'inputs': [
                    {
                        'id': local_id,
                        'idProperty': EXTERNAL_ID,
                        'properties': {
                            **properties,
                            EXTERNAL_ID: local_id
                        }
                    }
                ]
            }
        )

        results = data.get('results', [])

        if (
            data.get('errors')
            or len(results) != 1
            or not results[0].get('id')
            or data.get('status') not in (None, 'COMPLETE')
        ):
            raise RuntimeError(
                'HubSpot did not confirm upsert'
            )

        return results[0]

    def validate_property(self, kind):
        prop = self.request(
            'GET',
            f'/crm/v3/properties/{kind}/{EXTERNAL_ID}'
        )

        if (
            not prop.get('hasUniqueValue')
            or prop.get('type') != 'string'
        ):
            raise RuntimeError(
                'External ID property must be unique text'
            )