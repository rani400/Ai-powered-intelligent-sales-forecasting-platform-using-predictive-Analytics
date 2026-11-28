import logging, time
import httpx
from sqlalchemy import select, text, func
from app.integrations.hubspot.config import settings
from app.integrations.hubspot.models import Session, engine, init_db, Job, Connection
from app.integrations.hubspot.client import HubSpotClient, CRMError
from app.integrations.hubspot.oauth import access_token
from app.integrations.hubspot.sync_service import pull, push, scan, schedule_scan

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('hubspot.worker')
ACTIONS={'pull':pull,'push':push,'scan':scan}

def periodic():
    with Session.begin() as db:
        conn=db.get(Connection,settings.allowed_portal)
        if conn and time.time()-conn.last_poll>=settings.poll_seconds:
            active=db.scalar(select(func.count()).select_from(Job).where(Job.portal_id==conn.portal_id,Job.action=='scan',Job.status=='pending'))
            if not active: schedule_scan(db,conn.portal_id)
            conn.last_poll=time.time()

def process_one(client_factory=HubSpotClient, preflight=True):
    # One worker per SQLite DB. PostgreSQL advisory lock held for worker lifetime.
    with Session() as db:
        job_id=db.scalar(select(Job.id).where(Job.portal_id==settings.allowed_portal,Job.status=='pending',Job.available_at<=time.time()).order_by(Job.created_at,Job.id).limit(1))
    if not job_id: return False
    try:
        if preflight: access_token(settings.allowed_portal)
        with Session.begin() as db:
            job=db.get(Job,job_id,with_for_update=True)
            if not job or job.status!='pending': return True
            ACTIONS[job.action](db,client_factory(job.portal_id),job.portal_id,**job.payload)
            job.status='done'; job.error=''
    except Exception as exc:
        log.warning("Database error code: %s", getattr(getattr(exc, "orig", exc), "sqlite_errorname", "Unavailable"))
        with Session.begin() as db:
            job=db.get(Job,job_id,with_for_update=True)
            if not job: return True
            job.attempts+=1
            permanent=isinstance(exc,ValueError) or (isinstance(exc,CRMError) and 400<=exc.status<500 and exc.status not in (401,408,409,429))
            job.status='failed' if permanent or job.attempts>=8 else 'pending'
            job.available_at=time.time()+max(min(3600,2**job.attempts*5),getattr(exc,'retry_after',0))
            # Avoid logging CRM payloads, token strings or response bodies.
            job.error=f'HubSpot HTTP {exc.status}' if isinstance(exc,CRMError) else type(exc).__name__
            log.warning('Job %s: %s (%s)',job.id,job.error,job.status)
    return True

def main():
    settings.validate(); init_db()
    with engine.connect() as lock:
        if engine.dialect.name=='postgresql':
            if not lock.execute(text('SELECT pg_try_advisory_lock(80321457)')).scalar(): raise RuntimeError('Another HubSpot worker is active')
            lock.commit()
        log.info('HubSpot sync worker started')
        while True:
            try:
                periodic()
                if not process_one(): time.sleep(2)
            except Exception as exc:
                log.warning('Worker loop: %s',type(exc).__name__); time.sleep(5)

if __name__=='__main__': main()
