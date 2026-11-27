import os
from dataclasses import dataclass
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()
SCOPES = tuple(f'crm.objects.{kind}.{mode}' for kind in ('contacts','companies','deals') for mode in ('read','write'))

def flag(name, default='false'):
    return os.getenv(name, default).lower() in ('1','true','yes')

@dataclass(frozen=True)
class Settings:
    enabled: bool
    admin_key: str
    client_id: str
    client_secret: str
    redirect_uri: str
    webhook_url: str
    app_id: str
    allowed_portal: str
    encryption_key: str
    database_url: str
    poll_seconds: int
    allow_v1: bool

    @classmethod
    def load(cls):
        url = os.getenv('HUBSPOT_DATABASE_URL') or os.getenv('DATABASE_URL') or 'sqlite:///./hubspot_sync.db'
        if url.startswith('postgres://'): url = url.replace('postgres://','postgresql+psycopg://',1)
        if url.startswith('postgresql://'): url = url.replace('postgresql://','postgresql+psycopg://',1)
        return cls(flag('CRM_LIVE_SYNC_ENABLED'), os.getenv('CRM_ADMIN_KEY',''), os.getenv('HUBSPOT_CLIENT_ID',''), os.getenv('HUBSPOT_CLIENT_SECRET',''), os.getenv('HUBSPOT_REDIRECT_URI','http://localhost:8000/api/hubspot/oauth/callback'), os.getenv('HUBSPOT_WEBHOOK_URL',''), os.getenv('HUBSPOT_APP_ID',''), os.getenv('HUBSPOT_ALLOWED_PORTAL_ID',''), os.getenv('HUBSPOT_ENCRYPTION_KEY') or os.getenv('ENCRYPTION_KEY',''), url, max(60,int(os.getenv('HUBSPOT_POLL_SECONDS','300'))), flag('HUBSPOT_ALLOW_V1_WEBHOOKS','true'))

    def validate(self):
        if not self.enabled: raise ValueError('CRM live sync is disabled')
        if len(self.admin_key)<24 or self.admin_key.startswith('replace-'): raise ValueError('Set a strong CRM_ADMIN_KEY')
        if not all((self.client_id,self.client_secret,self.app_id,self.allowed_portal)): raise ValueError('Set HubSpot client credentials, app ID and allowed portal ID')
        if not self.webhook_url.startswith('https://'): raise ValueError('Set the public HTTPS webhook URL')
        Fernet(self.encryption_key.encode())

settings = Settings.load()
