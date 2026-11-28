import time, uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .models import Record, ExternalMapping, Job, Connection
from .mapper import normalize, FIELDS, EXTERNAL_ID


def enqueue(db,portal,action,payload,job_id=None):
    job=Job(id=job_id or uuid.uuid4().hex,portal_id=portal,action=action,payload=payload)
    try:
        with db.begin_nested():
            db.add(job); db.flush()
    except IntegrityError:
        if job_id is None or db.get(Job,job_id) is None: raise
    return job.id


def mapping(db,portal,kind,local_id):
    return db.get(ExternalMapping,('hubspot',portal,kind,local_id))


def queue_local_change(db,portal,kind,local_id,properties):
    """Call in the same DB transaction as a local write if using this store.
    Existing project models need a custom bridge; local_id must be stable per object.
    """
    props=normalize(kind,properties,strict=True)
    if not props: raise ValueError('No supported properties supplied')
    if not local_id or len(local_id)>100: raise ValueError('Invalid local ID')
    if db.get(Connection,portal) is None: raise ValueError('HubSpot is not connected')
    row=db.get(Record,(portal,kind,local_id),with_for_update=True)
    if row is None:
        row=Record(portal_id=portal,kind=kind,local_id=local_id,properties={},pending={},archived=False,revision=0); db.add(row)
    if row.archived: raise ValueError('Archived remote record; resolve manually before editing')
    delta={k:v for k,v in props.items() if row.properties.get(k)!=v}
    if not delta: return None
    row.properties={**row.properties,**delta}; row.pending={**row.pending,**delta}
    row.revision+=1; row.updated_at=time.time()
    return enqueue(db,portal,'push',{'kind':kind,'local_id':local_id})


def ingest(db,portal,kind,remote):
    remote_id=str(remote['id']); props=remote.get('properties',{})
    link=db.scalar(select(ExternalMapping).where(ExternalMapping.provider=='hubspot',ExternalMapping.portal_id==portal,ExternalMapping.kind==kind,ExternalMapping.remote_id==remote_id))
    if link is None:
        claimed=props.get(EXTERNAL_ID)
        candidate=db.get(Record,(portal,kind,str(claimed)),with_for_update=True) if claimed else None
        # Recover an upsert if the remote write succeeded but local commit failed.
        if candidate is not None:
            if mapping(db,portal,kind,candidate.local_id): raise RuntimeError('Remote identity collision; resolve manually')
            local_id=candidate.local_id
        else:
            local_id='hs-'+uuid.uuid4().hex
        link=ExternalMapping(provider='hubspot',portal_id=portal,kind=kind,local_id=local_id,remote_id=remote_id); db.add(link)
    row=db.get(Record,(portal,kind,link.local_id),with_for_update=True)
    if row is None:
        row=Record(portal_id=portal,kind=kind,local_id=link.local_id,properties={},pending={},archived=False,revision=0); db.add(row)
    incoming=normalize(kind,props)
    # Pending local field edits win; other fields accept the latest remote snapshot.
    merged={**row.properties,**incoming,**row.pending}
    if row.properties!=merged or row.archived:
        row.properties=merged; row.archived=False; row.updated_at=time.time(); row.revision+=1
    link.last_synced_at=time.time()
    # Crucially: inbound updates NEVER enqueue outbound jobs.
    return row


def pull(db,client,portal,kind,remote_id):
    data=client.get(kind,remote_id)
    if data is not None and not data.get('archived'):
        ingest(db,portal,kind,data); return
    link=db.scalar(select(ExternalMapping).where(ExternalMapping.provider=='hubspot',ExternalMapping.portal_id==portal,ExternalMapping.kind==kind,ExternalMapping.remote_id==remote_id))
    if link:
        row=db.get(Record,(portal,kind,link.local_id),with_for_update=True)
        if row: row.archived=True; row.updated_at=time.time()


def push(db,client,portal,kind,local_id):
    row=db.get(Record,(portal,kind,local_id),with_for_update=True)
    if not row or not row.pending: return
    if row.archived: raise ValueError('Remote record archived; outbound edit blocked')
    link=mapping(db,portal,kind,local_id)
    if link is None:
        client.validate_property(kind)
        result=client.upsert(kind,local_id,row.properties)
        link=ExternalMapping(provider='hubspot',portal_id=portal,kind=kind,local_id=local_id,remote_id=str(result['id'])); db.add(link)
    else:
        result=client.update(kind,link.remote_id,row.pending)
        if str(result.get('id',''))!=link.remote_id: raise RuntimeError('HubSpot did not confirm update')
    row.pending={}; link.last_synced_at=time.time(); row.updated_at=time.time()
    # Pull after successful write to capture HubSpot normalization without echoing it.
    enqueue(db,portal,'pull',{'kind':kind,'remote_id':link.remote_id})


def scan(db,client,portal,kind,after=None):
    page=client.page(kind,after)
    for remote in page.get('results',[]): ingest(db,portal,kind,remote)
    cursor=page.get('paging',{}).get('next',{}).get('after')
    if cursor is not None and str(cursor)!=str(after):
        enqueue(db,portal,'scan',{'kind':kind,'after':str(cursor)})


def schedule_scan(db,portal):
    for kind in FIELDS: enqueue(db,portal,'scan',{'kind':kind})
