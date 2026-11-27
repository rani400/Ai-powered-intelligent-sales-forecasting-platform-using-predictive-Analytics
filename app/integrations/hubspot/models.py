import time
from sqlalchemy import String, Text, Integer, Float, Boolean, JSON, UniqueConstraint, Index, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings

class Base(DeclarativeBase): pass

def now(): return time.time()

class Connection(Base):
    __tablename__='hubspot_connections'
    portal_id: Mapped[str]=mapped_column(String(40), primary_key=True)
    access_token: Mapped[str]=mapped_column(Text)
    refresh_token: Mapped[str]=mapped_column(Text)
    expires_at: Mapped[float]=mapped_column(Float)
    created_at: Mapped[float]=mapped_column(Float, default=now)
    updated_at: Mapped[float]=mapped_column(Float, default=now)
    last_poll: Mapped[float]=mapped_column(Float, default=0)

class OAuthState(Base):
    __tablename__='hubspot_oauth_states'
    digest: Mapped[str]=mapped_column(String(64), primary_key=True)
    expires_at: Mapped[float]=mapped_column(Float)

class Record(Base):
    __tablename__='hubspot_local_records'
    portal_id: Mapped[str]=mapped_column(String(40), primary_key=True)
    kind: Mapped[str]=mapped_column(String(20), primary_key=True)
    local_id: Mapped[str]=mapped_column(String(100), primary_key=True)
    properties: Mapped[dict]=mapped_column(JSON, default=dict)
    pending: Mapped[dict]=mapped_column(JSON, default=dict)
    archived: Mapped[bool]=mapped_column(Boolean, default=False)
    revision: Mapped[int]=mapped_column(Integer, default=0)
    updated_at: Mapped[float]=mapped_column(Float, default=now)

class ExternalMapping(Base):
    __tablename__='crm_external_mappings'
    __table_args__=(UniqueConstraint('provider','portal_id','kind','remote_id',name='uq_hs_remote_mapping'),)
    provider: Mapped[str]=mapped_column(String(20), primary_key=True, default='hubspot')
    portal_id: Mapped[str]=mapped_column(String(40), primary_key=True)
    kind: Mapped[str]=mapped_column(String(20), primary_key=True)
    local_id: Mapped[str]=mapped_column(String(100), primary_key=True)
    remote_id: Mapped[str]=mapped_column(String(100))
    last_synced_at: Mapped[float]=mapped_column(Float, default=now)

class Job(Base):
    __tablename__='hubspot_sync_jobs'
    __table_args__=(Index('ix_hs_jobs_ready','status','available_at'),)
    id: Mapped[str]=mapped_column(String(64), primary_key=True)
    portal_id: Mapped[str]=mapped_column(String(40))
    action: Mapped[str]=mapped_column(String(20))
    payload: Mapped[dict]=mapped_column(JSON)
    status: Mapped[str]=mapped_column(String(20), default='pending')
    attempts: Mapped[int]=mapped_column(Integer, default=0)
    available_at: Mapped[float]=mapped_column(Float, default=now)
    error: Mapped[str]=mapped_column(String(200), default='')
    created_at: Mapped[float]=mapped_column(Float, default=now)

def make_engine(url):
    engine=create_engine(url, pool_pre_ping=True, connect_args={'timeout':30} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def setup(dbapi, _):
            dbapi.isolation_level=None
            dbapi.execute('PRAGMA journal_mode=WAL')
            dbapi.execute('PRAGMA busy_timeout=30000')
        @event.listens_for(engine,'begin')
        def explicit_begin(conn): conn.exec_driver_sql('BEGIN')
    return engine

engine=make_engine(settings.database_url)
Session=sessionmaker(engine, expire_on_commit=False)
def init_db(): Base.metadata.create_all(engine)
