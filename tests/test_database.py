"""Database engineer regression checks for SQLite connection safety and integrity."""
from sqlalchemy import text
from app.database import make_engine
from app import models  # noqa: F401
from app.database import Base


def test_sqlite_foreign_keys_enabled(tmp_path):
    engine = make_engine(f'sqlite:///{tmp_path / "integrity.db"}')
    try:
        with engine.connect() as connection:
            assert connection.execute(text('PRAGMA foreign_keys')).scalar() == 1
    finally:
        engine.dispose()


def test_sqlite_waits_for_short_locks(tmp_path):
    engine = make_engine(f'sqlite:///{tmp_path / "contention.db"}')
    try:
        with engine.connect() as connection:
            assert connection.execute(text('PRAGMA busy_timeout')).scalar() == 5000
    finally:
        engine.dispose()


def test_model_registry_has_all_four_tables():
    assert {'leads', 'company_insights', 'lead_scores', 'outreach_campaigns'} <= set(Base.metadata.tables)
