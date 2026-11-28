import base64, hashlib, hmac, json, time
from dataclasses import replace
import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from app.integrations.hubspot import models, oauth, sync_service as svc, webhooks, mapper
from app.workers import sync_worker as worker
from app.api import hubspot_routes as routes

@pytest.fixture
def db(tmp_path,monkeypatch):
    engine=models.make_engine('sqlite:///'+str(tmp_path/'test.db'))
    models.Base.metadata.create_all(engine)
    session=sessionmaker(engine,expire_on_commit=False)
    config=replace(oauth.settings,allowed_portal='123',encryption_key=Fernet.generate_key().decode(),enabled=True,admin_key='x'*32,client_id='test',client_secret='secret',app_id='9',webhook_url='https://test.example/api/hubspot/webhooks')
    for module in (oauth,worker,routes):
        monkeypatch.setattr(module,'Session',session); monkeypatch.setattr(module,'settings',config)
    with session.begin() as s:
        s.add(models.Connection(portal_id='123',access_token=oauth.encrypt('access'),refresh_token=oauth.encrypt('refresh'),expires_at=time.time()+600))
    yield session
    engine.dispose()

class Fake:
    def __init__(self): self.remote={}; self.writes=0
    def validate_property(self,kind): pass
    def upsert(self,kind,local_id,properties):
        self.writes+=1; key=(kind,'99'); self.remote[key]={'id':'99','properties':{**properties,mapper.EXTERNAL_ID:local_id}}; return self.remote[key]
    def update(self,kind,remote_id,properties):
        self.writes+=1; self.remote[kind,remote_id]['properties'].update(properties); return self.remote[kind,remote_id]
    def get(self,kind,remote_id): return self.remote.get((kind,remote_id))

def test_signature():
    body=b'[]'; url='https://test.example/webhooks'; stamp='1000000'
    sig=base64.b64encode(hmac.new(b'secret',b'POST'+url.encode()+body+stamp.encode(),hashlib.sha256).digest()).decode()
    headers={'x-hubspot-signature-v3':sig,'x-hubspot-request-timestamp':stamp}
    assert webhooks.valid_signature('secret','POST',url,body,headers,now=1000)
    assert not webhooks.valid_signature('secret','POST',url,b'[1]',headers,now=1000)
    assert not webhooks.valid_signature('secret','POST',url,body,headers,now=1400)

def test_v1_signature():
    body=b'[]'; headers={'x-hubspot-signature-version':'v1','x-hubspot-signature':hashlib.sha256(b'secret'+body).hexdigest()}
    assert webhooks.valid_signature('secret','POST','url',body,headers,True)
    assert not webhooks.valid_signature('secret','POST','url',body,headers,False)

def test_state_one_time(db):
    from urllib.parse import urlparse,parse_qs
    state=parse_qs(urlparse(oauth.authorization_url()).query)['state'][0]
    assert oauth.consume_state(state)
    assert not oauth.consume_state(state)

def test_refresh_encrypted(db,monkeypatch):
    monkeypatch.setattr(oauth,'exchange',lambda **kwargs:{'access_token':'new','refresh_token':'rotated','expires_in':1800})
    assert oauth.access_token('123',force=True)=='new'
    with db() as s:
        row=s.get(models.Connection,'123'); assert row.access_token!='new'; assert oauth.decrypt(row.refresh_token)=='rotated'

def test_two_directions_no_loop(db):
    fake=Fake()
    with db.begin() as s: svc.queue_local_change(s,'123','contacts','lead-1',{'email':'example@example.com','firstname':'Before'})
    assert worker.process_one(lambda _:fake,False)
    assert worker.process_one(lambda _:fake,False) # read after write
    fake.remote['contacts','99']['properties']['firstname']='Remote'
    with db.begin() as s: svc.enqueue(s,'123','pull',{'kind':'contacts','remote_id':'99'})
    assert worker.process_one(lambda _:fake,False)
    assert not worker.process_one(lambda _:fake,False)
    with db() as s:
        row=s.get(models.Record,('123','contacts','lead-1')); assert row.properties['firstname']=='Remote'; assert row.pending=={}
    assert fake.writes==1
    with db.begin() as s: svc.queue_local_change(s,'123','contacts','lead-1',{'phone':'123'})
    assert worker.process_one(lambda _:fake,False)
    assert fake.remote['contacts','99']['properties']['phone']=='123'
    assert fake.writes==2

def test_pending_conflict(db):
    with db.begin() as s:
        row=svc.ingest(s,'123','contacts',{'id':'8','properties':{'firstname':'Old','phone':'1'}}); local=row.local_id
    with db.begin() as s: svc.queue_local_change(s,'123','contacts',local,{'firstname':'Local'})
    with db.begin() as s: svc.ingest(s,'123','contacts',{'id':'8','properties':{'firstname':'Remote','phone':'2'}})
    with db() as s:
        row=s.get(models.Record,('123','contacts',local)); assert row.properties=={'firstname':'Local','phone':'2'}

def test_duplicate_event_and_atomic_rollback(db):
    e={'portalId':123,'appId':9,'eventId':1,'subscriptionType':'contact.creation','objectId':99,'attemptNumber':0}
    key,p=webhooks.job_for_event(e); e['attemptNumber']=1; assert webhooks.job_for_event(e)[0]==key
    with db.begin() as s: svc.enqueue(s,'123','pull',p,key); svc.enqueue(s,'123','pull',p,key)
    with db() as s: assert len(s.scalars(select(models.Job)).all())==1
    with pytest.raises(RuntimeError):
        with db.begin() as s:
            svc.queue_local_change(s,'123','contacts','rollback',{'firstname':'Test'}); raise RuntimeError()
    with db() as s:
        assert s.get(models.Record,('123','contacts','rollback')) is None; assert len(s.scalars(select(models.Job)).all())==1

def test_retry(db):
    from app.integrations.hubspot.client import CRMError
    class Broken(Fake):
        def get(self,*args): raise CRMError(429,45)
    with db.begin() as s: jid=svc.enqueue(s,'123','pull',{'kind':'contacts','remote_id':'1'})
    assert worker.process_one(lambda _:Broken(),False)
    with db() as s:
        job=s.get(models.Job,jid); assert job.status=='pending'; assert job.attempts==1; assert job.available_at>time.time()+40

def test_archived(db):
    with db.begin() as s:
        row=svc.ingest(s,'123','deals',{'id':'7','properties':{'dealname':'Deal'}}); local=row.local_id
    with db.begin() as s: svc.pull(s,Fake(),'123','deals','7')
    with db() as s: assert s.get(models.Record,('123','deals',local)).archived

def test_api_auth_and_webhook(db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app=FastAPI(); app.include_router(routes.router); client=TestClient(app)
    assert client.get('/api/hubspot/status').status_code==401
    assert client.get('/api/hubspot/status',headers={'X-CRM-Admin-Key':'x'*32}).json()['connected']
    body=json.dumps([{'portalId':123,'appId':9,'eventId':123,'subscriptionType':'contact.creation','objectId':3}]).encode()
    assert client.post('/api/hubspot/webhooks',content=body).status_code==401
    headers={'X-HubSpot-Signature-Version':'v1','X-HubSpot-Signature':hashlib.sha256(b'secret'+body).hexdigest()}
    assert client.post('/api/hubspot/webhooks',content=body,headers=headers).status_code==202
    with db() as s: assert len(s.scalars(select(models.Job)).all())==1
