import hashlib, secrets, time
from urllib.parse import urlencode
import httpx
from cryptography.fernet import Fernet
from sqlalchemy import delete
from .config import settings, SCOPES
from .models import OAuthState, Connection, Session

TOKEN_URL='https://api.hubapi.com/oauth/2026-03/token'

def cipher(): return Fernet(settings.encryption_key.encode())
def encrypt(value): return cipher().encrypt(value.encode()).decode()
def decrypt(value): return cipher().decrypt(value.encode()).decode()
def digest(value): return hashlib.sha256(value.encode()).hexdigest()

def authorization_url():
    state=secrets.token_urlsafe(32)
    with Session.begin() as db:
        db.execute(delete(OAuthState).where(OAuthState.expires_at<time.time()))
        db.add(OAuthState(digest=digest(state),expires_at=time.time()+600))
    return 'https://app.hubspot.com/oauth/authorize?'+urlencode({'client_id':settings.client_id,'redirect_uri':settings.redirect_uri,'scope':' '.join(('oauth',)+SCOPES),'state':state})

def consume_state(state):
    with Session.begin() as db:
        result=db.execute(delete(OAuthState).where(OAuthState.digest==digest(state),OAuthState.expires_at>=time.time()))
        return result.rowcount==1

def exchange(**fields):
    with httpx.Client(timeout=15) as client:
        response=client.post(TOKEN_URL,data={'client_id':settings.client_id,'client_secret':settings.client_secret,**fields})
        if not response.is_success: raise RuntimeError(f'OAuth token request failed HTTP {response.status_code}')
        return response.json()

def install(code):
    data=exchange(grant_type='authorization_code',code=code,redirect_uri=settings.redirect_uri)
    portal=str(data.get('hub_id',''))
    if not portal:
        # Fail closed rather than linking an unverifiable account.
        raise RuntimeError('Token response omitted hub_id; verify OAuth endpoint/account')
    if portal!=settings.allowed_portal: raise ValueError('HubSpot account is not allowed')
    if not set(SCOPES).issubset(set(data.get('scopes',[]))): raise ValueError('Missing required CRM scopes')
    with Session.begin() as db:
        row=db.get(Connection,portal,with_for_update=True)
        if row is None:
            row=Connection(portal_id=portal); db.add(row)
        row.access_token=encrypt(data['access_token']); row.refresh_token=encrypt(data['refresh_token'])
        row.expires_at=time.time()+int(data['expires_in']); row.updated_at=time.time(); row.last_poll=0
    return portal

def access_token(portal, force=False):
    # Commit refresh separately before CRM operations: rotating tokens must survive job rollback.
    with Session.begin() as db:
        row=db.get(Connection,portal,with_for_update=True)
        if row is None: raise RuntimeError('HubSpot is not connected')
        if not force and row.expires_at>time.time()+90: return decrypt(row.access_token)
        data=exchange(grant_type='refresh_token',refresh_token=decrypt(row.refresh_token))
        if data.get('hub_id') is not None and str(data['hub_id'])!=portal: raise RuntimeError('OAuth portal mismatch')
        row.access_token=encrypt(data['access_token'])
        if data.get('refresh_token'): row.refresh_token=encrypt(data['refresh_token'])
        row.expires_at=time.time()+int(data['expires_in']); row.updated_at=time.time()
        return data['access_token']
